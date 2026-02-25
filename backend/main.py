"""
FastAPI backend for the Influencer Product Search Platform.
"""

import json
import os
import re
import subprocess
import sys
import threading
import uuid
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from groq import Groq
from pydantic import BaseModel

load_dotenv()

# ── Supabase client ────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables must be set.")

from supabase import create_client, Client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Groq AI client ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable must be set.")

groq_client = Groq(api_key=GROQ_API_KEY)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Influencer Product Search API",
    description="Search for products used by Egyptian/MENA influencers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Image proxy ────────────────────────────────────────────────────────────────

@app.get("/api/proxy-image")
async def proxy_image(url: str):
    """
    Proxy external images to bypass CORS restrictions.
    Used primarily for Instagram profile pictures.
    """
    try:
        if not url.startswith("https://scontent") and not url.startswith("https://instagram"):
            return Response(status_code=400, content="Invalid image URL")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
                timeout=10.0,
                follow_redirects=True
            )

            if response.status_code != 200:
                return Response(status_code=404, content="Image not found")

            return Response(
                content=response.content,
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    except Exception as e:
        print(f"Image proxy error: {e}")
        return Response(status_code=500, content="Failed to load image")


# ── Request models ─────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    influencer_name: Optional[str] = None

class InfluencerSearchRequest(BaseModel):
    handle: str
    platform: str = "instagram"

class AddInfluencerRequest(BaseModel):
    handle: str
    platform: str
    limit: int = 20

class ParseInfluencerRequest(BaseModel):
    handle: str
    platform: str = "instagram"
    limit: int = 10

class SaveProductsRequest(BaseModel):
    influencer_name: str
    profile_pic: str = ""
    platform: str = "instagram"
    products: list[dict]


# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch_buy_links(product_ids: list[str]) -> dict[str, list[dict]]:
    """Return a mapping of product_id → list of buy links."""
    if not product_ids:
        return {}

    resp = (
        supabase.table("buy_links")
        .select("*")
        .in_("product_id", product_ids)
        .execute()
    )
    links: dict[str, list[dict]] = {}
    for row in resp.data:
        pid = row["product_id"]
        links.setdefault(pid, []).append(row)
    return links


def enrich_products(products: list[dict]) -> list[dict]:
    """Enrich products with buy links."""
    from urllib.parse import quote_plus
    
    enriched = []
    for product in products:
        # Fetch buy links for this product
        resp = supabase.table("buy_links").select("*").eq("product_id", product["id"]).execute()
        
        buy_links = [
            {
                "id": link.get("id"),
                "store_name": link.get("store_name"),  # database column is "store_name"
                "price": link.get("price"),
                "currency": link.get("currency"),
                "url": link.get("url"),
                "in_stock": link.get("in_stock"),
            }
            for link in (resp.data or [])
        ]
        
        # ✅ AUTO-GENERATE FALLBACK LINKS IF NONE EXIST
        if not buy_links:
            search_query = f"{product.get('brand', '')} {product.get('product_name', '')}".strip()
            encoded = quote_plus(search_query)
            
            buy_links = [
                {
                    "id": "",
                    "store_name": "Amazon Egypt",
                    "url": f"https://www.amazon.eg/s?k={encoded}",
                    "price": None,
                    "currency": "EGP"
                },
                {
                    "id": "",
                    "store_name": "Noon Egypt",
                    "url": f"https://www.noon.com/egypt-en/search?q={encoded}",
                    "price": None,
                    "currency": "EGP"
                },
                {
                    "id": "",
                    "store_name": "Jumia Egypt",
                    "url": f"https://www.jumia.com.eg/catalog/?q={encoded}",
                    "price": None,
                    "currency": "EGP"
                },
                {
                    "id": "",
                    "store_name": "Google Shopping",
                    "url": f"https://www.google.com/search?tbm=shop&q={encoded}",
                    "price": None,
                    "currency": None
                }
            ]
        
        enriched.append({
            "id": product.get("id"),
            "influencer_name": product.get("influencer_name"),
            "influencer_profile_pic": product.get("influencer_profile_pic"),
            "product_name": product.get("product_name"),
            "brand": product.get("brand"),
            "category": product.get("category"),
            "quote": product.get("quote"),
            "video_url": product.get("video_url"),
            "platform": product.get("platform"),
            "buy_links": buy_links
        })
    return enriched
KNOWN_CATEGORIES = [
    "skincare", "makeup", "haircare", "fragrance", "fashion",
    "food", "tech", "lifestyle", "beauty", "other",
]


def detect_category(query: str) -> Optional[str]:
    """Return category if query contains a known category keyword."""
    query_lower = query.lower()
    for cat in KNOWN_CATEGORIES:
        if cat in query_lower:
            return cat
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Influencer Product Search API"}


@app.get("/search")
def search(q: str = Query(..., min_length=1, description="Search query")):
    """Smart search endpoint with STRICT influencer filtering."""
    try:
        query_lower = q.lower()
        
        # DETECT SPECIFIC INFLUENCER
        target_influencer = None
        if any(word in query_lower for word in ['sarah', 'sarah hany', 'sarahhany']):
            target_influencer = 'sarah'
        elif any(word in query_lower for word in ['huda', 'huda beauty', 'hudabeauty']):
            target_influencer = 'huda'
        
        category = detect_category(q)
        
        query_builder = supabase.table("products").select("*")
        
        if target_influencer:
            query_builder = query_builder.ilike("influencer_name", f"%{target_influencer}%")
        
        if category:
            query_builder = query_builder.ilike("category", f"%{category}%")
        
        if not target_influencer and not category:
            query_builder = query_builder.or_(
                f"product_name.ilike.%{q}%,brand.ilike.%{q}%,quote.ilike.%{q}%"
            )
        
        resp = query_builder.limit(50).execute()
        products = resp.data or []
        products = enrich_products(products)
        
        return {
            "query": q,
            "detected_influencer": target_influencer,
            "detected_category": category,
            "count": len(products),
            "results": products,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/products")
def list_products(
    limit: int = Query(50, ge=1, le=1000),  # ✅ Max 1000
    offset: int = Query(0, ge=0),
):
    """List all products with buy links."""
    try:
        resp = (
            supabase.table("products")
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )
        products = enrich_products(resp.data or [])
        return {"count": len(products), "results": products}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/influencers")
def list_influencers():
    """List all influencers."""
    try:
        resp = supabase.table("influencers").select("*").execute()
        return {"count": len(resp.data), "results": resp.data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/categories")
def list_categories():
    """List all distinct product categories."""
    try:
        resp = supabase.table("products").select("category").execute()
        categories = sorted(
            {row["category"] for row in (resp.data or []) if row.get("category")}
        )
        return {"count": len(categories), "results": categories}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask")
def ask_ai(req: QuestionRequest):
    """AI-powered Q&A endpoint with STRICT influencer filtering"""
    raw = ""
    try:
        print(f"\n🔍 Question: {req.question}")
        
        resp = supabase.table("products").select("*").execute()
        products = resp.data or []
        print(f"✅ Found {len(products)} products")
        
        if not products:
            return {
                "question": req.question,
                "answer": "No products in the database yet! Add some influencers first.",
                "products": [],
                "total_products": 0
            }
        
        products = enrich_products(products)

        question_lower = req.question.lower()
        target_influencer = None
        
        if any(word in question_lower for word in ['sarah', 'sarah hany', 'sarahhany']):
            target_influencer = 'sarah'
        elif any(word in question_lower for word in ['huda', 'huda beauty', 'hudabeauty']):
            target_influencer = 'huda'
        
        filtered_products = products
        if req.influencer_name:
            filtered_products = [
                p for p in products
                if req.influencer_name.lower() in p['influencer_name'].lower()
            ]
        elif target_influencer:
            filtered_products = [
                p for p in products 
                if target_influencer in p['influencer_name'].lower()
            ]
        
        if not filtered_products:
            return {
                "question": req.question,
                "answer": f"I couldn't find any products from that influencer yet.",
                "products": [],
                "total_products": 0
            }

        context = f"Products from {filtered_products[0]['influencer_name']}:\n\n" if target_influencer else "Products:\n\n"
        
        for p in filtered_products[:30]:
            context += f"• {p['product_name']}"
            if p.get('brand'):
                context += f" by {p['brand']}"
            context += f" ({p.get('category', 'other')})\n"
            context += f"  By: {p['influencer_name']}\n"
            if p.get('quote'):
                context += f"  \"{p['quote'][:150]}\"\n"
            context += "\n"

        system_prompt = """You are a friendly Egyptian shopping assistant for beauty and lifestyle products.

CRITICAL LANGUAGE RULES:
- Answer in BOTH English AND Egyptian Arabic (العامية المصرية)
- Egyptian Arabic MUST be conversational dialect, NOT formal Arabic (فصحى)
- Use Egyptian slang and expressions like:
  - "يا عم" / "يا جميل" (hey buddy)
  - "دي" / "ده" instead of "هذه" / "هذا"
  - "ممكن" instead of "يمكن"
  - "بتاع" instead of "الخاص ب"
  - "حاجة" instead of "شيء"
  - "عايز" / "عايزة" instead of "يريد"
  - "احنا" instead of "نحن"
  - "انت" / "انتي" instead of "أنت" / "أنتِ"

Return ONLY valid JSON:
{
  "answer": "Friendly answer in BOTH English and Egyptian Arabic mentioning influencer and products",
  "recommended_products": ["Product 1", "Product 2"]
}

No markdown, no extra text. Just JSON starting with { and ending with }."""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly Egyptian shopping assistant. Always respond in conversational Egyptian Arabic (عامية مصرية), NOT formal Arabic. Use Egyptian slang, expressions, and speak like a Cairo local. Be helpful and friendly!"
                },
                {"role": "user", "content": f"{context}\n\nQuestion: {req.question}"}
            ],
            temperature=0.5,
            max_tokens=800,
        )
        
        raw = completion.choices[0].message.content.strip()

        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
            if raw.startswith("json"):
                raw = raw[4:].strip()

        json_start = raw.find('{')
        json_end = raw.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:  # ✅ ADD 8 SPACES HERE!
            if '"answer":' in raw and '"recommended_products":' in raw:
                answer_start = raw.find('"answer":')
                products_end = raw.rfind(']')
                if answer_start != -1 and products_end != -1:
                    json_str = '{' + raw[answer_start:products_end+1] + '}'
                else:
                    return {
                        "question": req.question,
                        "answer": "Here are some products! 💄",
                        "products": filtered_products,
                        "total_products": len(filtered_products)
                    }
            else:
                return {
                    "question": req.question,
                    "answer": "Here are some products! 💄",
                    "products": filtered_products,
                    "total_products": len(filtered_products)
                }
        else:
            json_str = raw[json_start:json_end]
        
        try:
            ai_response = json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "question": req.question,
                "answer": "I found some products for you! 💄",
                "products": filtered_products,
                "total_products": len(filtered_products)
            }

        recommended_names = ai_response.get("recommended_products", [])
        recommended = []
        
        for name in recommended_names:
            name_lower = name.lower()
            for p in filtered_products:
                if name_lower in p['product_name'].lower() or p['product_name'].lower() in name_lower:
                    if p not in recommended:
                        recommended.append(p)
                    break

        if not recommended:
            recommended = filtered_products

        return {
            "question": req.question,
            "answer": ai_response.get("answer", "Here are some products!"),
            "products": recommended,
            "total_products": len(recommended)
        }

    except Exception as exc:
        print(f"❌ ERROR: {exc}")
        return {
            "question": req.question,
            "answer": "I found some products for you! 💄",
            "products": filtered_products if 'filtered_products' in locals() else products,
            "total_products": len(filtered_products) if 'filtered_products' in locals() else len(products)
        }

# ── Admin Endpoints ────────────────────────────────────────────────────────────

scrape_tasks = {}

@app.post("/admin/preview-influencer")
def preview_influencer(req: InfluencerSearchRequest):
    """Preview influencer before scraping"""
    try:
        from apify_client import ApifyClient
        client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
        
        if req.platform == "instagram":
            run = client.actor("apify/instagram-reel-scraper").call(
                run_input={"username": [req.handle], "resultsLimit": 1}
            )
            
            dataset_id = run["defaultDatasetId"]
            items = list(client.dataset(dataset_id).iterate_items())
            
            if not items:
                raise HTTPException(status_code=404, detail="Influencer not found")
            
            first_reel = items[0]
            
            return {
                "found": True,
                "platform": "instagram",
                "username": first_reel.get("ownerUsername", req.handle),
                "full_name": first_reel.get("ownerFullName") or req.handle,
                "profile_pic": first_reel.get("ownerProfilePicUrl") or "",
                "followers": 0,
                "bio": f"Instagram creator @{req.handle}",
                "is_verified": first_reel.get("isVerified", False),
                "posts_count": 0
            }
        else:
            run = client.actor("clockworks/free-tiktok-scraper").call(
                run_input={"profiles": [f"@{req.handle}"], "resultsPerPage": 1}
            )
            
            dataset_id = run["defaultDatasetId"]
            items = list(client.dataset(dataset_id).iterate_items())
            
            if not items:
                raise HTTPException(status_code=404, detail="Influencer not found")
            
            video = items[0]
            author = video.get("authorMeta", {})
            
            return {
                "found": True,
                "platform": "tiktok",
                "username": author.get("name"),
                "full_name": author.get("nickName"),
                "profile_pic": author.get("avatar"),
                "followers": author.get("fans", 0),
                "bio": author.get("signature"),
                "is_verified": author.get("verified"),
                "posts_count": author.get("video", 0)
            }
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/admin/parse-influencer")
def parse_influencer_products(req: ParseInfluencerRequest):
    """Parse influencer and extract products WITHOUT saving."""
    try:
        from apify_client import ApifyClient
        
        print(f"\n{'='*60}")
        print(f"🔍 Parsing: {req.handle} ({req.platform})")
        print(f"{'='*60}\n")
        
        client = ApifyClient(os.getenv("APIFY_API_TOKEN"))
        
        print("📥 Scraping videos...")
        if req.platform == "instagram":
            run = client.actor("apify/instagram-reel-scraper").call(
                run_input={"username": [req.handle], "resultsLimit": req.limit}
            )
        else:
            run = client.actor("clockworks/free-tiktok-scraper").call(
                run_input={"profiles": [f"@{req.handle}"], "resultsPerPage": req.limit}
            )
        
        dataset_id = run["defaultDatasetId"]
        items = list(client.dataset(dataset_id).iterate_items())
        
        print(f"✅ Found {len(items)} videos\n")
        
        if not items:
            raise HTTPException(status_code=404, detail="No videos found")
        
        first_video = items[0]
        
        if req.platform == "instagram":
            influencer_name = first_video.get("ownerFullName") or first_video.get("ownerUsername") or req.handle
            profile_pic = first_video.get("ownerProfilePicUrl") or ""
            
            # If profile pic not in video data, use dedicated profile scraper
            if not profile_pic:
                try:
                    print("📸 Fetching profile pic via profile scraper...")
                    profile_run = client.actor("apify/instagram-profile-scraper").call(
                        run_input={"usernames": [req.handle]}
                    )
                    profile_items = list(client.dataset(profile_run["defaultDatasetId"]).iterate_items())
                    if profile_items:
                        profile_pic = profile_items[0].get("profilePicUrl") or profile_items[0].get("profilePicUrlHD") or ""
                except Exception as e:
                    print(f"⚠️ Profile scraper failed: {e}")
        else:
            author = first_video.get("authorMeta", {})
            influencer_name = author.get("nickName") or author.get("name") or req.handle
            profile_pic = author.get("avatar") or ""
        
        print(f"👤 Influencer: {influencer_name}")
        print(f"📸 Profile: {profile_pic[:60] if profile_pic else 'None'}...\n")
        
        print("🤖 Extracting products...\n")
        
        all_products = []
        
        for i, video in enumerate(items):
            caption = video.get("caption") or video.get("text", "")
            
            if not caption.strip():
                continue
            
            print(f"  [{i+1}/{len(items)}] Processing...")
            
            # ====================================================================
            # 🔥 EXTRACT CDN VIDEO URL (DIRECT .MP4 LINK)
            # ====================================================================
            cdn_video_url = (
                video.get("videoUrl") or          # Instagram CDN
                video.get("video_url") or
                video.get("downloadAddr") or      # TikTok download address
                video.get("playAddr") or          # TikTok play address
                video.get("url") or
                ""
            )
            
            # Fallback for TikTok: check videoMeta
            if not cdn_video_url and req.platform == "tiktok":
                video_meta = video.get("videoMeta", {})
                play_addr = video_meta.get("playAddr") or video_meta.get("downloadAddr")
                if play_addr:
                    cdn_video_url = play_addr
            
            print(f"    🔗 CDN URL: {cdn_video_url[:80] if cdn_video_url else 'NONE'}...")
            
            if not cdn_video_url:
                print(f"    ⚠️ No CDN URL found, skipping...")
                continue
            
            # AI Extraction with CDN URL embedded
            prompt = f"""Extract beauty/lifestyle products from: "{caption}"

Return JSON:
[
  {{
    "product_name": "Product name",
    "brand": "Brand",
    "category": "makeup/skincare/haircare/fragrance/other",
    "quote": "Quote from caption",
    "video_url": "{cdn_video_url}"
  }}
]

If none: []"""
            
            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1024
                )
                
                raw = response.choices[0].message.content.strip()
                
                if raw.startswith("```"):
                    lines = raw.split("\n")
                    raw = "\n".join(lines[1:-1])
                    if raw.startswith("json"):
                        raw = raw[4:].strip()
                
                products = json.loads(raw)
                
                for product in products:
                    # Explicitly set video_url from CDN URL (don't rely on AI)
                    product["video_url"] = cdn_video_url
                    # Add empty buy links for frontend
                    product["buy_links"] = [
                        {"store_name": "Jumia Egypt", "url": "", "currency": "EGP"},
                        {"store_name": "Noon Egypt", "url": "", "currency": "EGP"},
                        {"store_name": "Amazon Egypt", "url": "", "currency": "EGP"},
                        {"store_name": "Google Shopping", "url": "", "currency": None},
                    ]
                    all_products.append(product)
                
                print(f"      ✅ Found {len(products)} products")
                
            except Exception as e:
                print(f"      ⚠️ Failed: {e}")
                continue
        
        print(f"\n✅ Extracted {len(all_products)} total products\n")
        
        return {
            "success": True,
            "influencer_name": influencer_name,
            "profile_pic": profile_pic,
            "total_products": len(all_products),
            "products": all_products
        }
        
    except Exception as exc:
        print(f"❌ ERROR: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/admin/save-products")
def save_verified_products(req: SaveProductsRequest):
    """Save manually verified products to database."""
    try:
        print(f"\n💾 Saving {len(req.products)} verified products...\n")
        
        saved_count = 0
        
        for product in req.products:
            try:
                existing = supabase.table("products").select("id").eq(
                    "product_name", product["product_name"]
                ).eq(
                    "influencer_name", req.influencer_name
                ).execute()
                
                if existing.data:
                    print(f"  ⏭️  Skipping: {product['product_name']}")
                    continue
                
                product_data = {
                    "product_name": product["product_name"],
                    "brand": product.get("brand", ""),
                    "category": product.get("category", "other"),
                    "quote": product.get("quote", ""),
                    "influencer_name": req.influencer_name,
                    "influencer_profile_pic": req.profile_pic,
                    "platform": req.platform,
                    "video_url": product.get("video_url", "")
                }
                
                result = supabase.table("products").insert(product_data).execute()
                product_id = result.data[0]["id"]

                links_added = 0

                # Parse @mentions from caption and create Instagram links FIRST
                caption = product.get("quote", "")
                mentions = re.findall(r'@([a-zA-Z0-9._]+)', caption)
                for mention in mentions:
                    try:
                        supabase.table("buy_links").insert({
                            "product_id": product_id,
                            "store_name": f"@{mention}",
                            "url": f"https://instagram.com/{mention}",
                            "price": None,
                            "currency": None
                        }).execute()
                        links_added += 1
                    except Exception as e:
                        print(f"      ⚠️ Mention link failed: {e}")

                buy_links = product.get("buy_links", [])

                # Auto-generate if empty
                if not buy_links or all(not link.get("url", "").strip() for link in buy_links):
                    from urllib.parse import quote_plus
                    search_query = f"{product.get('brand', '')} {product['product_name']}".strip()
                    
                    buy_links = [
                        {
                            "store_name": "Jumia Egypt",
                            "url": f"https://www.jumia.com.eg/catalog/?q={quote_plus(search_query)}",
                            "currency": "EGP"
                        },
                        {
                            "store_name": "Noon Egypt",
                            "url": f"https://www.noon.com/egypt-en/search?q={quote_plus(search_query)}",
                            "currency": "EGP"
                        },
                        {
                            "store_name": "Amazon Egypt",
                            "url": f"https://www.amazon.eg/s?k={quote_plus(search_query)}",
                            "currency": "EGP"
                        },
                        {
                            "store_name": "Google Shopping",
                            "url": f"https://www.google.com/search?tbm=shop&q={quote_plus(search_query)}",
                            "currency": None
                        }
                    ]
                    print(f"      🔗 Auto-generated search links")
                
                for link in buy_links:
                    url = link.get("url", "").strip()
                    if url:
                        try:
                            supabase.table("buy_links").insert({
                                "product_id": product_id,
                                "store_name": link["store_name"],
                                "url": url,
                                "price": link.get("price"),
                                "currency": link.get("currency")
                            }).execute()
                            links_added += 1
                        except Exception as e:
                            print(f"      ⚠️ Link failed: {e}")
                
                saved_count += 1
                print(f"  ✅ {product['product_name']} ({links_added} links)")
                
            except Exception as e:
                print(f"  ❌ Failed: {product.get('product_name')}: {e}")
                continue
        
        print(f"\n✅ Saved {saved_count}/{len(req.products)} products!\n")
        
        return {
            "success": True,
            "saved_count": saved_count,
            "total_count": len(req.products)
        }
        
    except Exception as exc:
        print(f"❌ ERROR: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

@app.delete("/admin/delete-product/{product_id}")
def delete_product(product_id: str):
    """Delete a product and its buy links"""
    try:
        print(f"\n🗑️ Deleting product {product_id}...")

        # Step 1: Check if product exists
        print("  🔍 Checking if product exists...")
        product_check = supabase.table("products").select("id").eq("id", product_id).execute()

        if not product_check.data or len(product_check.data) == 0:
            print(f"  ❌ Product {product_id} not found")
            raise HTTPException(status_code=404, detail="Product not found")

        print("  ✅ Product exists")

        # Step 2: Delete buy_links first (even though CASCADE should handle it)
        print("  ⏳ Deleting buy links...")
        buy_links_result = supabase.table("buy_links").delete().eq("product_id", product_id).execute()
        deleted_links = len(buy_links_result.data) if buy_links_result.data else 0
        print(f"  ✅ Deleted {deleted_links} buy links")

        # Step 3: Delete the product (don't check result since Supabase doesn't return deleted rows)
        print("  ⏳ Deleting product...")
        supabase.table("products").delete().eq("id", product_id).execute()

        print(f"  ✅ Product deleted successfully\n")

        return {
            "success": True,
            "message": "Product deleted",
            "deleted_links": deleted_links
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"  ❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/admin/update-product/{product_id}")
def update_product(product_id: str, req: dict):
    """Update product details and buy links"""
    try:
        print(f"\n🔧 Updating product {product_id}")
        print(f"📦 Received data: {req}")  # ✅ DEBUG LOG
        
        # Update product
        product_data = {
            "product_name": req.get("product_name"),
            "brand": req.get("brand", ""),
            "category": req.get("category", "other"),
            "quote": req.get("quote", ""),
        }
        
        print(f"✏️  Updating product: {product_data}")
        supabase.table("products").update(product_data).eq("id", product_id).execute()
        
        # Delete old buy links
        print(f"🗑️  Deleting old buy links...")
        supabase.table("buy_links").delete().eq("product_id", product_id).execute()
        
        # Add new buy links
        buy_links = req.get("buy_links", [])
        print(f"🔗 Adding {len(buy_links)} buy links...")
        
        for i, link in enumerate(buy_links):
            url = link.get("url", "").strip()
            store_name = link.get("store_name", "").strip()
            
            print(f"  [{i+1}] Store: '{store_name}', URL: '{url[:50] if url else 'EMPTY'}'...")
            
            if url and store_name:  # ✅ Require BOTH store name and URL
                try:
                    supabase.table("buy_links").insert({
                        "product_id": product_id,
                        "store_name": store_name,
                        "url": url,
                        "price": link.get("price"),
                        "currency": link.get("currency")
                    }).execute()
                    print(f"      ✅ Added")
                except Exception as link_error:
                    print(f"      ❌ Failed to add link: {link_error}")
            else:
                print(f"      ⏭️  Skipped (missing store or url)")
        
        print(f"✅ Product updated successfully!\n")
        return {"success": True, "message": "Product updated"}
        
    except Exception as e:
        print(f"❌ ERROR updating product: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/add-influencer")
async def add_influencer(req: AddInfluencerRequest):
    """Start scraping influencer in background"""
    task_id = str(uuid.uuid4())
    
    scrape_tasks[task_id] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing...",
        "handle": req.handle,
        "platform": req.platform
    }
    
    def run_scraper():
        try:
            result = subprocess.run([
                sys.executable,
                "scripts/add_influencer.py",
                req.handle,
                req.platform,
                str(req.limit)
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                scrape_tasks[task_id]["status"] = "complete"
                scrape_tasks[task_id]["progress"] = 100
                scrape_tasks[task_id]["message"] = "✅ Complete!"
            else:
                scrape_tasks[task_id]["status"] = "failed"
                scrape_tasks[task_id]["message"] = f"❌ Error: {result.stderr}"
        
        except Exception as e:
            scrape_tasks[task_id]["status"] = "failed"
            scrape_tasks[task_id]["message"] = f"❌ Error: {str(e)}"
    
    thread = threading.Thread(target=run_scraper)
    thread.start()
    
    return {"task_id": task_id, "status": "started"}


@app.get("/admin/task/{task_id}")
async def get_task_status(task_id: str):
    """Check progress of scraping task"""
    if task_id not in scrape_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return scrape_tasks[task_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)