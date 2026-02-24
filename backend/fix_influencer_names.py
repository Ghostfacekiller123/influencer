"""
Fix influencer_name column - replace IDs with actual names
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Mapping of IDs to actual names
INFLUENCER_MAP = {
    "3839726240806747388": "Huda Kattan",
    "3837473612853163853": "Sarah Hany",
    # Add more as needed
}

def fix_names():
    # Get all products
    response = supabase.table("products").select("*").execute()
    products = response.data
    
    fixed = 0
    for product in products:
        old_name = product["influencer_name"]
        
        # Check if it's an ID (all digits)
        if old_name.isdigit() and old_name in INFLUENCER_MAP:
            new_name = INFLUENCER_MAP[old_name]
            
            supabase.table("products").update({
                "influencer_name": new_name
            }).eq("id", product["id"]).execute()
            
            print(f"✅ Fixed: {old_name} → {new_name}")
            fixed += 1
    
    print(f"\n✅ Fixed {fixed} products")

if __name__ == "__main__":
    fix_names()