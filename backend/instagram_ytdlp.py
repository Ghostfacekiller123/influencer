"""
Instagram scraper using yt-dlp (more reliable than instaloader)
"""
import os
import json
from pathlib import Path
import subprocess

# Instagram usernames to scrape
INFLUENCERS = ["hudabeauty"]
VIDEO_LIMIT = 10
OUTPUT_DIR = Path("data/raw/instagram")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scrape_influencer(username: str):
    print(f"\n🔍 Scraping @{username}...")
    
    user_dir = OUTPUT_DIR / username
    user_dir.mkdir(exist_ok=True)
    
    # yt-dlp command to download Instagram reels
    cmd = [
        "yt-dlp",
        f"https://www.instagram.com/{username}/reels/",
        "--max-downloads", str(VIDEO_LIMIT),
        "--output", str(user_dir / "%(id)s.%(ext)s"),
        "--write-info-json",
        "--no-playlist",
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Downloaded videos for @{username}")
        else:
            print(f"❌ Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Instagram Scraper (yt-dlp)")
    print("=" * 60)
    
    for influencer in INFLUENCERS:
        scrape_influencer(influencer)
    
    print("\n✅ Done!")