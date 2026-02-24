"""
Transcribe videos from Apify scraped data using Groq Whisper
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# Paths
INSTAGRAM_VIDEOS = Path("data/raw/instagram/hudabeauty/videos")
TIKTOK_VIDEOS = Path("data/raw/tiktok/hudabeauty/videos")
OUTPUT_FILE = Path("data/processed/transcriptions.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def transcribe_video(video_path: Path):
    """Transcribe a single video file"""
    print(f"  🎤 Transcribing {video_path.name}...")
    
    try:
        with open(video_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(video_path.name, f.read()),
                model="whisper-large-v3",
                language="en",
                response_format="verbose_json",
            )
        
        return {
            "video_id": video_path.stem,
            "filename": video_path.name,
            "platform": "instagram" if "instagram" in str(video_path) else "tiktok",
            "text": transcription.text,
        }
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Transcribing Videos (Apify Data)")
    print("=" * 60)
    
    # Collect all video files
    video_files = []
    
    if INSTAGRAM_VIDEOS.exists():
        video_files.extend(list(INSTAGRAM_VIDEOS.glob("*.mp4")))
    
    if TIKTOK_VIDEOS.exists():
        video_files.extend(list(TIKTOK_VIDEOS.glob("*.mp4")))
    
    # Filter out 0-byte files
    video_files = [v for v in video_files if v.stat().st_size > 0]
    
    print(f"\n📹 Found {len(video_files)} videos\n")
    
    transcriptions = []
    
    for i, video_path in enumerate(video_files, 1):
        print(f"{i}/{len(video_files)}:")
        result = transcribe_video(video_path)
        if result:
            transcriptions.append(result)
            print(f"     ✅ {len(result['text'])} chars")
    
    # Save transcriptions
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(transcriptions, f, indent=2)
    
    print(f"\n💾 Saved {len(transcriptions)} transcriptions to: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()