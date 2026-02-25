import json
from pathlib import Path

file = Path("data/raw/tiktok/hudabeauty/videos.json")
with open(file) as f:
    data = json.load(f)

if data:
    video = data[0]
    
    print("webVideoUrl:")
    print(f"  {video.get('webVideoUrl', 'N/A')}")
    
    print("\nvideoMeta.subtitleLinks:")
    subtitle_links = video.get('videoMeta', {}).get('subtitleLinks', [])
    if subtitle_links:
        print(json.dumps(subtitle_links[:2], indent=2))  # First 2
    else:
        print("  N/A")
    
    print("\n" + "="*60)
    print("CHECKING IF APIFY REMOVED VIDEO URLS...")
    print("="*60)
    print("\nThis might be a limitation of the FREE tier.")
    print("Let's check the Apify actor docs or use a different actor.")