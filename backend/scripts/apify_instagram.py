"""
Instagram reel scraper using Apify
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
OUTPUT_DIR = Path("data/raw/instagram")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scrape_instagram_reels(username: str, limit: int = 10):
    """Scrape Instagram reels using Apify"""
    print(f"\n🔍 Scraping @{username} reels...")
    
    client = ApifyClient(APIFY_TOKEN)
    
    # Run Instagram Reel Scraper actor
    run_input = {
        "username": [username],
        "resultsLimit": limit,
    }
    
    print("🚀 Starting Apify actor...")
    run = client.actor("apify/instagram-reel-scraper").call(run_input=run_input)
    
    print("📥 Fetching results...")
    items = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        items.append(item)
    
    # Save results
    user_dir = OUTPUT_DIR / username
    user_dir.mkdir(exist_ok=True)
    
    output_file = user_dir / "reels.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    
    print(f"\n✅ Scraped {len(items)} reels")
    print(f"💾 Saved to: {output_file}")
    
    # Print sample
    if items:
        print("\n📊 Sample reel:")
        sample = items[0]
        print(f"  Caption: {sample.get('caption', 'N/A')[:100]}...")
        print(f"  Video URL: {sample.get('videoUrl', 'N/A')}")
        print(f"  Likes: {sample.get('likesCount', 0):,}")
    
    return items

if __name__ == "__main__":
    print("=" * 60)
    print("Instagram Reel Scraper (Apify)")
    print("=" * 60)
    
    scrape_instagram_reels("hudabeauty", limit=10)
    
    print("\n✅ Done!")