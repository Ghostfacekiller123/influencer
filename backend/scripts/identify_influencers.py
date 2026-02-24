"""
Check what products each ID has to identify them
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Get all influencer IDs
response = supabase.table("products").select("influencer_name, product_name, brand, platform, video_url").execute()
products = response.data

# Group by ID
influencers = {}
for p in products:
    id = p["influencer_name"]
    if id not in influencers:
        influencers[id] = []
    influencers[id].append(p)

# Show what each ID has
for id, prods in influencers.items():
    print(f"\n{'='*60}")
    print(f"ID: {id}")
    print(f"Total products: {len(prods)}")
    print(f"{'='*60}")
    
    for p in prods[:5]:  # Show first 5
        print(f"  • {p['product_name']}")
        if p.get('brand'):
            print(f"    Brand: {p['brand']}")
        if p.get('video_url'):
            print(f"    Video: {p['video_url'][:60]}...")
    
    if len(prods) > 5:
        print(f"  ... and {len(prods) - 5} more")
    
    print()

print("\n" + "="*60)
print("Based on products/brands, who do you think each ID is?")
print("="*60)