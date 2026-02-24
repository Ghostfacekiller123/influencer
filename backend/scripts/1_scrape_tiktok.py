"""
Script 1: Scrape TikTok videos from influencers listed in influencers.json.

Usage:
    python 1_scrape_tiktok.py

Requires:
    TIKTOK_SESSION_ID  (optional, improves reliability)
    VIDEO_LIMIT_PER_INFLUENCER  (default: 10)
"""

import json
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

INFLUENCERS_FILE = ROOT_DIR / "influencers.json"
OUTPUT_FILE = DATA_DIR / "tiktok_videos.json"

VIDEO_LIMIT = int(os.getenv("VIDEO_LIMIT_PER_INFLUENCER", 10))
SESSION_ID = os.getenv("TIKTOK_SESSION_ID", "")


async def scrape_influencer(api, influencer: dict) -> list[dict]:
    """Fetch up to VIDEO_LIMIT videos for one influencer."""
    handle = influencer.get("tiktok", "")
    if not handle:
        print(f"  [SKIP] {influencer['name']} — no TikTok handle")
        return []

    videos = []
    try:
        user = api.user(username=handle)
        async for video in user.videos(count=VIDEO_LIMIT):
            video_data = video.as_dict
            caption = ""

            # Prefer auto-generated captions when available
            if video_data.get("textExtra"):
                caption = " ".join(
                    t.get("hashtagName", "") or t.get("userUniqueId", "")
                    for t in video_data["textExtra"]
                    if t.get("hashtagName") or t.get("userUniqueId")
                )
            if not caption:
                caption = video_data.get("desc", "")

            videos.append(
                {
                    "id": video_data.get("id"),
                    "influencer": influencer["name"],
                    "platform": "tiktok",
                    "url": f"https://www.tiktok.com/@{handle}/video/{video_data.get('id')}",
                    "caption": caption,
                    "has_caption": bool(caption),
                }
            )
        print(f"  [OK]   {influencer['name']} — {len(videos)} videos")
    except Exception as exc:
        print(f"  [ERR]  {influencer['name']} — {exc}")

    return videos


async def main():
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        print("[ERROR] TikTokApi not installed. Run: pip install TikTokApi")
        return

    print("=" * 60)
    print("Step 1: Scraping TikTok videos")
    print("=" * 60)

    with open(INFLUENCERS_FILE) as f:
        influencers = json.load(f)

    print(f"Loaded {len(influencers)} influencers\n")

    all_videos: list[dict] = []

    ms_token = os.getenv("MS_TOKEN", "")  # optional browser cookie
    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token] if ms_token else None,
            num_sessions=1,
            sleep_after=3,
        )
        for influencer in influencers:
            print(f"→ {influencer['name']} (@{influencer.get('tiktok', 'N/A')})")
            videos = await scrape_influencer(api, influencer)
            all_videos.extend(videos)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(all_videos)} videos to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
