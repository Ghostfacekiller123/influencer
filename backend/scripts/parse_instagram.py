"""
Parse Instagram HTML and extract posts/reels
"""
import json
import re
from pathlib import Path

def extract_instagram_data(html_file: Path):
    """Extract embedded JSON data from Instagram HTML"""
    print(f"\n📝 Parsing {html_file}...")
    
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Instagram embeds data in <script> tags
    # Look for window._sharedData or similar patterns
    patterns = [
        r'window\._sharedData\s*=\s*({.+?});',
        r'window\.__additionalDataLoaded\([^,]+,\s*({.+?})\);',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            try:
                data = json.loads(matches[0])
                return data
            except:
                continue
    
    # Alternative: look for <script type="application/ld+json">
    ld_json = re.findall(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL)
    if ld_json:
        try:
            data = json.loads(ld_json[0])
            return data
        except:
            pass
    
    return None

if __name__ == "__main__":
    html_file = Path("data/raw/instagram/hudabeauty/profile.html")
    
    data = extract_instagram_data(html_file)
    
    if data:
        print("✅ Extracted data!")
        print(json.dumps(data, indent=2)[:1000])  # Print first 1000 chars
        
        # Save to JSON
        output = html_file.parent / "data.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved to: {output}")
    else:
        print("❌ No data found in HTML")
        print("Let's check what we have...")
        print(f"HTML size: {html_file.stat().st_size} bytes")