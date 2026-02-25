"""
Check which influencer this ID belongs to
"""
import os
import json
from pathlib import Path

# Check raw scraped data
data_dir = Path("../data/raw")

# Check Instagram
ig_dir = data_dir / "instagram"
if ig_dir.exists():
    for user_dir in ig_dir.iterdir():
        if user_dir.is_dir():
            print(f"Instagram user: {user_dir.name}")
            
            # Check metadata
            metadata = user_dir / "reels.json"
            if metadata.exists():
                with open(metadata) as f:
                    data = json.load(f)
                    if data:
                        first = data[0]
                        print(f"  ID: {first.get('ownerUserId', 'N/A')}")
                        print(f"  Username: {first.get('ownerUsername', 'N/A')}")
                        print(f"  Full Name: {first.get('ownerFullName', 'N/A')}")
                        print()

# Check TikTok
tt_dir = data_dir / "tiktok"
if tt_dir.exists():
    for user_dir in tt_dir.iterdir():
        if user_dir.is_dir():
            print(f"TikTok user: {user_dir.name}")
            
            metadata = user_dir / "videos.json"
            if metadata.exists():
                with open(metadata) as f:
                    data = json.load(f)
                    if data:
                        first = data[0]
                        author = first.get('authorMeta', {})
                        print(f"  ID: {author.get('id', 'N/A')}")
                        print(f"  Username: {author.get('name', 'N/A')}")
                        print(f"  Full Name: {author.get('nickName', 'N/A')}")
                        print()