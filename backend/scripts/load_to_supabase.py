"""
Load products to Supabase using REST API
"""
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

INFLUENCERS_FILE = Path("influencers.json")
PRODUCTS_FILE = Path("data/processed/products.json")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def load_influencers():
    """Load influencers into database"""
    if not INFLUENCERS_FILE.exists():
        print("⚠️  influencers.json not found")
        return 0
    
    with open(INFLUENCERS_FILE) as f:
        influencers = json.load(f)
    
    inserted = 0
    for inf in influencers:
        data = {
            "name": inf["name"],
            "instagram_handle": inf.get("instagram", ""),
            "tiktok_handle": inf.get("tiktok", ""),
            "platform": "instagram" if inf.get("instagram") else "tiktok"
        }
        
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/influencers",
                headers=HEADERS,
                json=data
            )
            
            if response.status_code in [200, 201]:
                inserted += 1
                print(f"  ✅ {inf['name']}")
            else:
                print(f"  ⚠️  {inf['name']}: {response.text}")
        except Exception as e:
            print(f"  ❌ {inf['name']}: {e}")
    
    return inserted

def load_products():
    """Load products and buy links"""
    if not PRODUCTS_FILE.exists():
        print(f"❌ {PRODUCTS_FILE} not found")
        return 0, 0
    
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    
    inserted_products = 0
    inserted_links = 0
    
    for product in products:
        # Insert product
        product_data = {
            "influencer_name": product.get("influencer", "Unknown"),
            "product_name": product.get("product_name", ""),
            "brand": product.get("brand", ""),
            "category": product.get("category", "other"),
            "quote": product.get("quote", ""),
            "platform": product.get("platform", "tiktok")
        }
        
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/products",
                headers=HEADERS,
                json=product_data
            )
            
            if response.status_code in [200, 201]:
                inserted_products += 1
                product_id = response.json()[0]["id"]
                
                # Create buy links
                buy_links = [
                    {
                        "product_id": product_id,
                        "store": "Amazon Egypt",
                        "url": f"https://www.amazon.eg/s?k={product['product_name'].replace(' ', '+')}",
                        "price": None
                    },
                    {
                        "product_id": product_id,
                        "store": "Noon Egypt",
                        "url": f"https://www.noon.com/egypt-en/search/?q={product['product_name'].replace(' ', '+')}",
                        "price": None
                    },
                    {
                        "product_id": product_id,
                        "store": "Jumia Egypt",
                        "url": f"https://www.jumia.com.eg/catalog/?q={product['product_name'].replace(' ', '+')}",
                        "price": None
                    }
                ]
                
                for link in buy_links:
                    try:
                        r = requests.post(
                            f"{SUPABASE_URL}/rest/v1/buy_links",
                            headers=HEADERS,
                            json=link
                        )
                        if r.status_code in [200, 201]:
                            inserted_links += 1
                    except:
                        pass
                
                print(f"  ✅ {product['product_name'][:50]}")
            else:
                print(f"  ❌ {response.text[:100]}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return inserted_products, inserted_links

def main():
    print("="*60)
    print("Loading Data to Supabase")
    print("="*60)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Set SUPABASE_URL and SUPABASE_KEY in .env")
        return
    
    print("\n📤 Loading influencers...")
    inf_count = load_influencers()
    print(f"✅ Loaded {inf_count} influencers\n")
    
    print("📤 Loading products...")
    prod_count, link_count = load_products()
    print(f"\n✅ Loaded {prod_count} products")
    print(f"✅ Created {link_count} buy links")
    
    print("\n" + "="*60)
    print("✅ Upload complete!")
    print("="*60)

if __name__ == "__main__":
    main()