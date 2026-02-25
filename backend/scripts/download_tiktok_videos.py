"""
Download TikTok video files from scraped data
"""
import json
import requests
from pathlib import Path
from tqdm import tqdm

INPUT_FILE = Path("data/raw/tiktok/hudabeauty/videos.json")
OUTPUT_DIR = Path("data/raw/tiktok/hudabeauty/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_video(url: str, output_path: Path):
    """Download video from URL"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=output_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

def get_video_url(video):
    """Extract video URL from subtitle links (prioritize English)"""
    subtitle_links = video.get('videoMeta', {}).get('subtitleLinks', [])
    
    if not subtitle_links:
        return None
    
    # Try to find English version first
    for link in subtitle_links:
        if link.get('language', '').startswith('eng'):
            return link.get('downloadLink')
    
    # Fallback to first available
    return subtitle_links[0].get('downloadLink')

def main():
    print("=" * 60)
    print("Downloading TikTok Videos")
    print("=" * 60)
    
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        videos = json.load(f)
    
    print(f"\n📦 Found {len(videos)} videos to download\n")
    
    for i, video in enumerate(videos, 1):
        video_id = video.get("id", f"video_{i}")
        video_url = get_video_url(video)
        
        if not video_url:
            print(f"❌ {i}. No video URL for {video_id}")
            continue
        
        output_path = OUTPUT_DIR / f"{video_id}.mp4"
        
        if output_path.exists():
            print(f"⏭️  {i}. Already downloaded: {video_id}")
            continue
        
        print(f"⬇️  {i}/{len(videos)}. Downloading {video_id}...")
        try:
            download_video(video_url, output_path)
            print(f"   ✅ Saved to: {output_path}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Download complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()