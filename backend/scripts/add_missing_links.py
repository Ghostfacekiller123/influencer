"""
Add buy links to existing products that don't have them
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def add_links_to_existing_products():
    # Get all products
    products = supabase.table("products").select("*").execute().data
    
    print(f"Found {len(products)} products\n")
    
    for product in products:
        product_id = product["id"]
        
        # Check if product already has links
        existing_links = supabase.table("buy_links").select("*").eq("product_id", product_id).execute().data
        
        if existing_links:
            print(f"⏭️  {product['product_name']} - already has {len(existing_links)} links")
            continue
        
        # Generate search query
        product_name = product["product_name"]
        brand = product.get("brand", "")
        search_query = f"{brand} {product_name}".strip()
        
        print(f"➕ {product_name}")
        
        # Add Amazon link
        amazon_search = f"https://www.amazon.com/s?k={search_query.replace(' ', '+')}"
        supabase.table("buy_links").insert({
            "product_id": product_id,
            "store_name": "Amazon",
            "url": amazon_search,
            "price": None,
            "currency": "USD"
        }).execute()
        
        # Add Google Shopping link
        google_shopping = f"https://www.google.com/search?tbm=shop&q={search_query.replace(' ', '+')}"
        supabase.table("buy_links").insert({
            "product_id": product_id,
            "store_name": "Google Shopping",
            "url": google_shopping,
            "price": None,
            "currency": None
        }).execute()
        
        # Add Jumia Egypt link
        jumia_search = f"https://www.jumia.com.eg/catalog/?q={search_query.replace(' ', '+')}"
        supabase.table("buy_links").insert({
            "product_id": product_id,
            "store_name": "Jumia Egypt",
            "url": jumia_search,
            "price": None,
            "currency": "EGP"
        }).execute()
        
        print(f"   ✅ Added 3 buy links\n")
    
    print("🎉 DONE!")

if __name__ == "__main__":
    add_links_to_existing_products()