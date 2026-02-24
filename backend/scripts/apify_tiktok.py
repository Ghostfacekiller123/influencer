"""
TikTok video scraper using Apify
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
OUTPUT_DIR = Path("data/raw/tiktok")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scrape_tiktok_videos(username: str, limit: int = 10):
    """Scrape TikTok videos using Apify"""
    print(f"\n🔍 Scraping @{username} videos...")
    
    client = ApifyClient(APIFY_TOKEN)
    
    # Run TikTok Scraper actor
    run_input = {
        "profiles": [username],
        "resultsPerPage": limit,
    }
    
    print("🚀 Starting Apify actor...")
    run = client.actor("clockworks/free-tiktok-scraper").call(run_input=run_input)
    
    print("📥 Fetching results...")
    items = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
    
    # Save results
    user_dir = OUTPUT_DIR / username
    user_dir.mkdir(exist_ok=True)
    
    output_file = user_dir / "videos.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    
    print(f"\n✅ Scraped {len(items)} videos")
    print(f"💾 Saved to: {output_file}")
    
    # Print sample
    if items:
        print("\n📊 Sample video:")
        sample = items[0]
        print(f"  Text: {sample.get('text', 'N/A')[:100]}...")
        print(f"  Video URL: {sample.get('videoUrl', 'N/A')}")
        print(f"  Likes: {sample.get('diggCount', 0):,}")
    
    return items

if __name__ == "__main__":
    print("=" * 60)
    print("TikTok Video Scraper (Apify)")
    print("=" * 60)
    
    # Test with a beauty influencer
    scrape_tiktok_videos("hudabeauty", limit=10)
    
    print("\n✅ Done!")