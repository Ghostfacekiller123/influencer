# -*- coding: utf-8 -*-
"""
Update existing products with real buy links using SerpAPI
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client
from serpapi import GoogleSearch

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def scrape_real_buy_links(product_name: str, brand: str):
    """
    Simple search URLs - no scraping, no affiliate needed
    """
    from urllib.parse import quote_plus
    
    search_query = f"{brand} {product_name}".strip()
    
    print(f"    🔍 Creating links for: {search_query}")
    
    links = []
    
    # Jumia Egypt
    jumia_url = f"https://www.jumia.com.eg/catalog/?q={quote_plus(search_query)}"
    links.append({
        "store_name": "Jumia Egypt",
        "url": jumia_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Jumia Egypt")
    
    # Noon Egypt
    noon_url = f"https://www.noon.com/egypt-en/search?q={quote_plus(search_query)}"
    links.append({
        "store_name": "Noon Egypt",
        "url": noon_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Noon Egypt")
    
    # Amazon Egypt
    amazon_url = f"https://www.amazon.eg/s?k={quote_plus(search_query)}"
    links.append({
        "store_name": "Amazon Egypt",
        "url": amazon_url,
        "price": None,
        "currency": "EGP"
    })
    print(f"      ✅ Amazon Egypt")
    
    # Google Shopping
    google_url = f"https://www.google.com/search?tbm=shop&q={quote_plus(search_query)}"
    links.append({
        "store_name": "Google Shopping",
        "url": google_url,
        "price": None,
        "currency": None
    })
    print(f"      ✅ Google Shopping")
    
    return links
def update_all_products():
    """
    Update all products with real buy links
    """
    print("��� Fetching all products...\n")
    products = supabase.table("products").select("*").execute().data
    
    print(f"Found {len(products)} products\n")
    print("="*60)
    
    updated = 0
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] {product['product_name']}")
        
        # Delete old links
        supabase.table("buy_links").delete().eq("product_id", product['id']).execute()
        print("    🗑️  Deleted old links")
        
        # Get new real links
        real_links = scrape_real_buy_links(
            product['product_name'],
            product.get('brand', '')
        )
        
        # Insert new links
        for link in real_links:
            try:
                supabase.table("buy_links").insert({
                    "product_id": product['id'],
                    "store_name": link["store_name"],
                    "url": link["url"],
                    "price": link.get("price"),
                    "currency": link.get("currency")
                }).execute()
            except Exception as e:
                print(f"      ❌ Failed: {e}")
        
        updated += 1
        print(f"    ✅ Added {len(real_links)} new links")
        
        # Rate limiting (important for SerpAPI!)
        time.sleep(2)
    
    print("\n" + "="*60)
    print(f"🎉 Updated {updated} products with real buy links!")
    print("="*60)


if __name__ == "__main__":
    confirm = input("This will replace ALL buy links. Continue? (y/n): ")
    if confirm.lower() in ["y", "yes"]:
        update_all_products()
    else:
        print("Cancelled.")