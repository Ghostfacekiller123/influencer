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
Usage: python add_influencer.py "sarahhanyofficial" instagram 20
"""

import json
import time
import re  # ✅ NEW - For extracting mentions
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

# ✅ NEW FUNCTION - Extract @mentions
def extract_mentions(caption: str):
    """Extract @mentions from caption"""
    mentions = re.findall(r'@([a-zA-Z0-9._]+)', caption)
    return list(set(mentions))  # Remove duplicates

def scrape_real_buy_links(product_name: str, brand: str):
    """
    Simple search URLs - no scraping, no affiliate needed
    """
    from urllib.parse import quote_plus
    
    query = f"{brand} {product_name}".strip() if brand else product_name
    encoded = quote_plus(query)
    
    return [
        {
            "store_name": "Amazon Egypt",
            "url": f"https://www.amazon.eg/s?k={encoded}",
            "price": None,
            "currency": "EGP"
        },
        {
            "store_name": "Noon Egypt",
            "url": f"https://www.noon.com/egypt-en/search?q={encoded}",
            "price": None,
            "currency": "EGP"
        },
        {
            "store_name": "Jumia Egypt",
            "url": f"https://www.jumia.com.eg/catalog/?q={encoded}",
            "price": None,
            "currency": "EGP"
        },
        {
            "store_name": "Google Shopping",
            "url": f"https://www.google.com/search?tbm=shop&q={encoded}",
            "price": None,
            "currency": None
        }
    ]


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
        
        # If profile pic not in video data, use dedicated profile scraper
        if not profile_pic:
            try:
                print("📸 Fetching profile pic via profile scraper...")
                profile_run = apify.actor("apify/instagram-profile-scraper").call(
                    run_input={"usernames": [username]}
                )
                profile_items = list(apify.dataset(profile_run["defaultDatasetId"]).iterate_items())
                if profile_items:
                    profile_pic = profile_items[0].get("profilePicUrl") or profile_items[0].get("profilePicUrlHD") or ""
                    print(f"📸 Profile pic from scraper: {profile_pic[:60] if profile_pic else 'None'}...")
            except Exception as e:
                print(f"⚠️  Profile scraper failed: {e}")
    else:
        author = first_video.get("authorMeta", {})
        influencer_name = author.get("nickName") or author.get("name") or username
        influencer_id = author.get("id")
        profile_pic = author.get("avatar") or ""
    
    print(f"👤 Influencer: {influencer_name}")
    print(f"🆔 ID: {influencer_id}")
    print(f"📸 Profile pic: {profile_pic[:60] if profile_pic else 'None'}...\n")
    
    # STEP 3: EXTRACT TRANSCRIPTS + CDN VIDEO URLS
    print("📝 Step 2: Extracting captions + CDN video URLs...\n")
    
    transcriptions = []
    
    for i, video in enumerate(items, 1):
        caption = video.get("caption") or video.get("text", "")
        
        if not caption or not caption.strip():
            print(f"  [{i}/{len(items)}] ⏭️  No caption, skipping...")
            continue
        
        try:
            transcript = caption.strip()
            
            print(f"  [{i}/{len(items)}] ✅ Caption: {transcript[:60]}...")
            
            # ====================================================================
            # 🔥 EXTRACT CDN VIDEO URL (DIRECT .MP4 LINK)
            # ====================================================================
            
            # Try multiple possible CDN URL fields
            cdn_video_url = (
                video.get("videoUrl") or          # Instagram CDN
                video.get("video_url") or
                video.get("downloadAddr") or      # TikTok download address
                video.get("playAddr") or          # TikTok play address
                video.get("url") or
                ""
            )
            
            print(f"    🔗 CDN URL: {cdn_video_url[:80] if cdn_video_url else 'NONE'}...")
            
            # Fallback: if no CDN URL, try to extract from videoMeta
            if not cdn_video_url and platform == "tiktok":
                video_meta = video.get("videoMeta", {})
                play_addr = video_meta.get("playAddr") or video_meta.get("downloadAddr")
                if play_addr:
                    cdn_video_url = play_addr
                    print(f"    🔗 Extracted from videoMeta: {cdn_video_url[:80]}...")
            
            # DEBUG: Print all available keys if no URL found
            if not cdn_video_url:
                print(f"    ⚠️  No video URL found!")
                print(f"    🔍 Available fields: {list(video.keys())[:15]}...")
            
            # Use the CDN URL directly
            full_video_url = cdn_video_url
            
            # ✅ NEW - Extract @mentions from caption
            mentions = extract_mentions(transcript)
            if mentions:
                print(f"    📍 Found mentions: {', '.join(['@' + m for m in mentions])}")
            
            transcriptions.append({
                "video_url": full_video_url,
                "transcript": transcript,
                "mentions": mentions,  # ✅ NEW
                "platform": platform,
                "influencer_name": influencer_name
            })
            
        except Exception as e:
            print(f"    ⚠️ Failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"✅ Processed {len(transcriptions)} videos with CDN URLs\n")
    
    # STEP 4: EXTRACT PRODUCTS WITH AI
    print("🤖 Step 3: Extracting products with AI...\n")
    
    all_products = []
    
    for i, trans in enumerate(transcriptions, 1):
        if not trans["transcript"].strip():
            continue
        
        print(f"  [{i}/{len(transcriptions)}] Analyzing...")
        
        # ✅ UPDATED PROMPT - Extract EVERYTHING!
        prompt = f"""Extract ALL products, items, brands, or recommendations mentioned in this social media caption.

This includes:
- Beauty products (makeup, skincare, haircare, fragrance)
- Fashion items (clothes, dresses, tops, pants, shoes, bags, accessories, jewelry)
- Lifestyle products (home decor, tech, gadgets, food, drinks, supplements)
- Services (salons, restaurants, apps, websites, stores)

Caption: "{trans['transcript']}"

Return ONLY valid JSON array:
[
  {{
    "product_name": "Exact product/item name",
    "brand": "Brand name or @mention if it's a local brand/page",
    "category": "makeup/skincare/haircare/fragrance/fashion/shoes/bags/jewelry/accessories/tech/food/lifestyle/home/other",
    "quote": "Exact quote from caption about this product"
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
            
            # Clean up markdown code blocks
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1])
                if raw.startswith("json"):
                    raw = raw[4:].strip()
            
            products = json.loads(raw)
            
            for product in products:
                product["influencer_name"] = influencer_name
                product["video_url"] = trans["video_url"]  # ✅ CDN URL
                product["platform"] = platform
                product["mentions"] = trans["mentions"]  # ✅ NEW - Store mentions
                all_products.append(product)
            
            print(f"      ✅ Found {len(products)} products")
            
        except Exception as e:
            print(f"      ⚠️ AI extraction failed: {e}")
            continue
    
    print(f"✅ Extracted {len(all_products)} total products\n")
    
    # STEP 5: UPLOAD + SCRAPE REAL BUY LINKS
    print("💾 Step 4: Uploading + scraping buy links...\n")
    
    uploaded = 0
    for product in all_products:
        try:
            # Skip products without a valid video URL
            if not product.get("video_url"):
                print(f"  ⚠️  Skipping: {product['product_name']} - no video URL")
                continue
            
            # Check if product already exists
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
                "video_url": product.get("video_url", "")  # ✅ CDN URL saved here
            }
            
            product_result = supabase.table("products").insert(product_data).execute()
            product_id = product_result.data[0]["id"]
            
            print(f"  📦 {product['product_name']}")
            print(f"      📹 CDN Video: {product.get('video_url', 'NO URL')[:60]}...")
            
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
            
            # Add @mentions as buy links
            mentions = product.get("mentions", [])
            for mention in mentions:
                try:
                    instagram_url = f"https://www.instagram.com/{mention}/"
                    supabase.table("buy_links").insert({
                        "product_id": product_id,
                        "store_name": f"@{mention}",
                        "url": instagram_url,
                        "price": None,
                        "currency": None
                    }).execute()
                    print(f"      📍 Added mention: @{mention}")
                except Exception as e:
                    print(f"      ❌ @{mention}: {e}")
            
            uploaded += 1
            print(f"      ✅ Added {len(real_links) + len(mentions)} buy links\n")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ❌ Failed: {product.get('product_name')}: {e}")
    
    print(f"\n✅ Uploaded {uploaded} new products!")
    
    # SUMMARY
    print(f"\n{'='*60}")
    print(f"✅ COMPLETE - {influencer_name}")
    print(f"{'='*60}")
    print(f"  Videos scraped: {len(items)}")
    print(f"  Processed: {len(transcriptions)}")
    print(f"  Products extracted: {len(all_products)}")
    print(f"  New products added: {uploaded}")
    print(f"{'='*60}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python add_influencer.py <username> [platform] [limit]")
        print('Example: python add_influencer.py "sarahhanyofficial" instagram 20')
        sys.exit(1)
    
    username = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else "instagram"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    scrape_and_process(username, platform, limit)


if __name__ == "__main__":
    main()