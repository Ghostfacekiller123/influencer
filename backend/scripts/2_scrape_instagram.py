"""
Script 2: Scrape Instagram reels from influencers listed in influencers.json.

Usage:
    python 2_scrape_instagram.py

Requires:
    INSTA_USERNAME
    INSTA_PASSWORD
    VIDEO_LIMIT_PER_INFLUENCER  (default: 10)

Note: Create a throwaway Instagram account. Do NOT use your personal account.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "instagram"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INFLUENCERS_FILE = ROOT_DIR / "influencers.json"
OUTPUT_FILE = ROOT_DIR / "data" / "instagram_videos.json"

VIDEO_LIMIT = int(os.getenv("VIDEO_LIMIT_PER_INFLUENCER", 10))
INSTA_USERNAME = os.getenv("INSTA_USERNAME", "")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD", "")


def scrape_influencer(loader, influencer: dict) -> list[dict]:
    """Download reels and return metadata list for one influencer."""
    import instaloader

    handle = influencer.get("instagram", "")
    if not handle:
        print(f"  [SKIP] {influencer['name']} — no Instagram handle")
        return []

    videos = []
    try:
        profile = instaloader.Profile.from_username(loader.context, handle)
        count = 0
        for post in profile.get_posts():
            if count >= VIDEO_LIMIT:
                break
            if not post.is_video:
                continue

            # Download video file
            try:
                loader.download_post(post, target=str(DATA_DIR / handle))
            except Exception as dl_err:
                print(f"    [WARN] Could not download video: {dl_err}")

            videos.append(
                {
                    "shortcode": post.shortcode,
                    "influencer": sarahhany["name"],
                    "platform": "instagram",
                    "url": f"https://www.instagram.com/p/{post.shortcode}/",
                    "caption": post.caption or "",
                    "has_caption": bool(post.caption),
                    "local_path": str(DATA_DIR / handle / f"{post.date_utc:%Y-%m-%d_%H-%M-%S}_UTC.mp4"),
                }
            )
            count += 1

        print(f"  [OK]   {influencer['name']} — {len(videos)} reels")
    except Exception as exc:
        print(f"  [ERR]  {influencer['name']} — {exc}")

    return videos


def main():
    try:
        import instaloader
    except ImportError:
        print("[ERROR] instaloader not installed. Run: pip install instaloader")
        return

    if not INSTA_USERNAME or not INSTA_PASSWORD:
        print("[ERROR] Set INSTA_USERNAME and INSTA_PASSWORD in your .env file")
        return

    print("=" * 60)
    print("Step 2: Scraping Instagram reels")
    print("=" * 60)

    loader = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    print(f"Logging in as @{INSTA_USERNAME} …")
    try:
        loader.login(INSTA_USERNAME, INSTA_PASSWORD)
        print("Login successful\n")
    except Exception as exc:
        print(f"[ERROR] Login failed: {exc}")
        return

    with open(INFLUENCERS_FILE) as f:
        influencers = json.load(f)

    print(f"Loaded {len(influencers)} influencers\n")

    all_videos: list[dict] = []
    for influencer in influencers:
        print(f"→ {influencer['name']} (@{influencer.get('instagram', 'N/A')})")
        videos = scrape_influencer(loader, influencer)
        all_videos.extend(videos)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(all_videos)} reels to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
