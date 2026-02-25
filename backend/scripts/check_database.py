from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

response = supabase.table("products").select("influencer_name, product_name, category").execute()

# Group by influencer
influencers = {}
for p in response.data:
    name = p["influencer_name"]
    if name not in influencers:
        influencers[name] = []
    influencers[name].append(p)

print("\n" + "="*60)
print("DATABASE SUMMARY")
print("="*60)

for influencer, products in influencers.items():
    print(f"\n👤 {influencer} ({len(products)} products)")
    
    categories = {}
    for p in products:
        cat = p.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p["product_name"])
    
    for cat, prods in categories.items():
        print(f"   {cat}: {len(prods)} items")
        for prod in prods[:3]:
            print(f"     • {prod}")
        if len(prods) > 3:
            print(f"     ... and {len(prods) - 3} more")

print("\n" + "="*60)
print(f"TOTAL: {len(response.data)} products")
print("="*60 + "\n")