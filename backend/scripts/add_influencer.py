# -*- coding: utf-8 -*-
import sys
import os

# Fix Windows encoding for emojis
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

"""
ONE-COMMAND INFLUENCER SCRAPER
Usage: python add_influencer.py "sarahhanyofficial"
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient
from supabase import create_client
from groq import Groq

load_dotenv()

# Clients
apify = ApifyClient(os.getenv("APIFY_API_TOKEN"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

def scrape_real_buy_links(product_name: str, brand: str):
    """
    Simple search URLs - no scraping, no affiliate needed
    """
    from urllib.parse import quote_plus
    
    search_query = f"{brand} {product_name}".strip()
    
    print(f"    🔍 Creating links for: {search_query}")
    
    links = []
    
    # Jumia Egypt
    jumia_url = f"https://www.jumia.com.eg/catalog/?q={quote_plus(search_query)}"
    links.append({
        "store_name": "Jumia Egypt",
        "url": jumia_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Jumia Egypt")
    
    # Noon Egypt
    noon_url = f"https://www.noon.com/egypt-en/search?q={quote_plus(search_query)}"
    links.append({
        "store_name": "Noon Egypt",
        "url": noon_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Noon Egypt")
    
    # Amazon Egypt
    amazon_url = f"https://www.amazon.eg/s?k={quote_plus(search_query)}"
    links.append({
        "store_name": "Amazon Egypt",
        "url": amazon_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Amazon Egypt")
    
    # Google Shopping
    google_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(search_query)}"
    links.append({
        "store_name": "Google Shopping",
        "url": google_url,
        "price": None,
        "currency": None
    })
    print(f"      ✅ Google Shopping")
    
    return links


def scrape_and_process(username: str, platform: str = "instagram", limit: int = 20):
    """
    Full pipeline for one influencer
    """
    
    print(f"\n{'='*60}")
    print(f"🚀 Processing: {username} ({platform})")
    print(f"{'='*60}\n")
    
    # STEP 1: SCRAPE WITH APIFY
    print("📥 Step 1: Scraping videos on Apify cloud...")
    
    if platform == "instagram":
        run = apify.actor("apify/instagram-reel-scraper").call(
            run_input={
                "username": [username],
                "resultsLimit": limit
            }
        )
    else:
        run = apify.actor("clockworks/free-tiktok-scraper").call(
            run_input={
                "profiles": [f"@{username}"],
                "resultsPerPage": limit
            }
        )
    
    dataset_id = run["defaultDatasetId"]
    items = list(apify.dataset(dataset_id).iterate_items())
    
    print(f"✅ Scraped {len(items)} videos\n")
    
    if not items:
        print("❌ No videos found!")
        return
    
    # STEP 2: GET INFLUENCER INFO + PROFILE PIC
    first_video = items[0]
    
    if platform == "instagram":
        influencer_name = first_video.get("ownerFullName") or first_video.get("ownerUsername") or username
        influencer_id = first_video.get("ownerUserId")
        profile_pic = first_video.get("ownerProfilePicUrl") or ""
    else:
        author = first_video.get("authorMeta", {})
        influencer_name = author.get("nickName") or author.get("name") or username
        influencer_id = author.get("id")
        profile_pic = author.get("avatar") or ""
    
    print(f"👤 Influencer: {influencer_name} (ID: {influencer_id})")
    print(f"📸 Profile Pic: {profile_pic[:60] if profile_pic else 'None'}...\n")
    
    # STEP 3: TRANSCRIBE VIDEOS WITH DEBUG
    print("🎤 Step 2: Transcribing videos...")
    
    transcriptions = []
    for i, video in enumerate(items[:limit]):
        video_url = video.get("videoUrl") or video.get("video", {}).get("downloadAddr")
        caption = video.get("caption") or video.get("title", "")
        
        if not video_url:
            continue
        
        print(f"  [{i+1}/{len(items)}] Processing...")
        
        try:
            transcript = caption
            
            # 🔍 DEBUG: Print ALL available fields
            print(f"    🔍 Available fields: {list(video.keys())}")
            
            # Try multiple possible ID fields
            video_id = (
                video.get("id") or 
                video.get("videoId") or 
                video.get("shortCode") or
                video.get("code") or
                video.get("pk") or
                ""
            )
            
            print(f"    🆔 Extracted ID: '{video_id}'")
            print(f"    🔗 Raw videoUrl: {video_url[:100] if video_url else 'None'}...")
            
            # Build proper video URL
            if platform == "instagram":
                if video_id:
                    full_video_url = f"https://www.instagram.com/reel/{video_id}/"
                    print(f"    ✅ Built URL from ID: {full_video_url}")
                elif video_url and "instagram.com" in str(video_url):
                    full_video_url = video_url
                    print(f"    ✅ Using raw URL: {full_video_url[:80]}...")
                else:
                    full_video_url = ""
                    print(f"    ❌ NO VIDEO URL FOUND!")
            else:  # tiktok
                full_video_url = video_url
            
            transcriptions.append({
                "video_url": full_video_url,
                "transcript": transcript,
                "platform": platform,
                "influencer_name": influencer_name
            })
            
        except Exception as e:
            print(f"    ⚠️ Failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"✅ Transcribed {len(transcriptions)} videos\n")
    
    # STEP 4: EXTRACT PRODUCTS WITH AI
    print("🤖 Step 3: Extracting products with AI...")
    
    all_products = []
    
    for trans in transcriptions:
        if not trans["transcript"].strip():
            continue
        
        prompt = f"""
Extract ALL beauty/lifestyle products mentioned in this video caption/transcript.

Transcript: "{trans['transcript']}"

Return ONLY valid JSON array:
[
  {{
    "product_name": "Exact product name",
    "brand": "Brand name",
    "category": "makeup/skincare/haircare/fragrance/other",
    "quote": "Exact quote about the product from transcript"
  }}
]

If no products found, return: []
"""
        
        try:
            response = groq.chat.completions.create(
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
                product["influencer_name"] = influencer_name
                product["video_url"] = trans["video_url"]
                product["platform"] = platform
                all_products.append(product)
            
            print(f"  ✅ Found {len(products)} products")
            
        except Exception as e:
            print(f"  ⚠️ AI extraction failed: {e}")
            continue
    
    print(f"✅ Extracted {len(all_products)} total products\n")
    
    # STEP 5: UPLOAD + SCRAPE REAL BUY LINKS
    print("💾 Step 4: Uploading + scraping buy links...\n")
    
    uploaded = 0
    for product in all_products:
        try:
            existing = supabase.table("products").select("id").eq(
                "product_name", product["product_name"]
            ).eq(
                "influencer_name", influencer_name
            ).execute()
            
            if existing.data:
                print(f"  ⏭️  Skipping: {product['product_name']}")
                continue
            
            # Insert product WITH ALL FIELDS INCLUDING PROFILE PIC
            product_data = {
                "product_name": product["product_name"],
                "brand": product.get("brand", ""),
                "category": product.get("category", "other"),
                "quote": product.get("quote", ""),
                "influencer_name": influencer_name,
                "influencer_profile_pic": profile_pic,
                "platform": platform,
                "video_url": product.get("video_url", "")
            }
            
            product_result = supabase.table("products").insert(product_data).execute()
            product_id = product_result.data[0]["id"]
            
            print(f"  📦 {product['product_name']}")
            print(f"      📹 Video: {product.get('video_url', 'NO URL')[:60]}...")
            
            # SCRAPE REAL LINKS
            real_links = scrape_real_buy_links(
                product["product_name"],
                product.get("brand", "")
            )
            
            # Insert buy links
            for link in real_links:
                try:
                    supabase.table("buy_links").insert({
                        "product_id": product_id,
                        "store_name": link["store_name"],
                        "url": link["url"],
                        "price": link.get("price"),
                        "currency": link.get("currency")
                    }).execute()
                except Exception as e:
                    print(f"      ❌ {link['store_name']}: {e}")
            
            uploaded += 1
            print(f"      ✅ Added {len(real_links)} links\n")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Failed: {product.get('product_name')}: {e}")
    
    print(f"\n✅ Uploaded {uploaded} new products!")
    
    # SUMMARY
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE - {influencer_name}")
    print(f"{'='*60}")
    print(f"  Videos scraped: {len(items)}")
    print(f"  Transcriptions: {len(transcriptions)}")
    print(f"  Products extracted: {len(all_products)}")
    print(f"  New products added: {uploaded}")
    print(f"  Profile pic: {'✅' if profile_pic else '❌'}")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_influencer.py <username> [platform] [limit]")
        print("\nExamples:")
        print("  python add_influencer.py sarahhanyofficial")
        print("  python add_influencer.py sarahhany tiktok 30")
        print("  python add_influencer.py hudabeauty instagram 50")
        sys.exit(1)
    
    username = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else "instagram"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    scrape_and_process(username, platform, limit)


if __name__ == "__main__":
    main()