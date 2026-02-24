"""
Download video files from scraped Instagram reels
"""
import json
import requests
from pathlib import Path
from tqdm import tqdm

INPUT_FILE = Path("data/raw/instagram/hudabeauty/reels.json")
OUTPUT_DIR = Path("data/raw/instagram/hudabeauty/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_video(url: str, output_path: Path):
    """Download video from URL"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

def main():
    print("=" * 60)
    print("Downloading Instagram Reel Videos")
    print("=" * 60)
    
    # Load scraped data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reels = json.load(f)
    
    print(f"\n📦 Found {len(reels)} reels to download\n")
    
    for i, reel in enumerate(reels, 1):
        video_url = reel.get("videoUrl")
        reel_id = reel.get("id", f"reel_{i}")
        
        if not video_url:
            print(f"❌ {i}. No video URL for {reel_id}")
            continue
        
        output_path = OUTPUT_DIR / f"{reel_id}.mp4"
        
        if output_path.exists():
            print(f"⏭️  {i}. Already downloaded: {reel_id}")
            continue
        
        print(f"⬇️  {i}. Downloading {reel_id}...")
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