"""
Fix influencer_name - replace IDs with actual names
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Based on the products we saw earlier
INFLUENCER_MAP = {
    "3839726240806747388": "Huda Kattan",
    "3837473612853163853": "Sarah Hany",
    "3836834772354552655": "Huda Beauty",  # This one had all Huda products
}

def fix_all_names():
    print("🔧 Fixing influencer names...\n")
    
    # Get all products
    response = supabase.table("products").select("*").execute()
    products = response.data
    
    print(f"Found {len(products)} products\n")
    
    fixed = 0
    for product in products:
        old_id = product["influencer_name"]
        
        if old_id in INFLUENCER_MAP:
            new_name = INFLUENCER_MAP[old_id]
            
            # Update in Supabase
            supabase.table("products").update({
                "influencer_name": new_name
            }).eq("id", product["id"]).execute()
            
            print(f"✅ {product['product_name'][:40]}")
            print(f"   {old_id} → {new_name}\n")
            fixed += 1
    
    print(f"\n✅ Fixed {fixed}/{len(products)} products!")
    
    # Show new distinct names
    response = supabase.table("products").select("influencer_name").execute()
    unique_names = set(p["influencer_name"] for p in response.data)
    print(f"\n📊 Unique influencer names now:")
    for name in sorted(unique_names):
        print(f"  • {name}")

if __name__ == "__main__":
    fix_all_names()