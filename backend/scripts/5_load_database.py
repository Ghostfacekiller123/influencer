"""
Script 5: Load influencers and products into Supabase.

Usage:
    python 5_load_database.py

Requires:
    SUPABASE_URL
    SUPABASE_KEY
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

INFLUENCERS_FILE = ROOT_DIR / "influencers.json"
PRODUCTS_FILE = DATA_DIR / "products.json"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def load_influencers(supabase) -> int:
    """Upsert influencers from influencers.json into the database."""
    with open(INFLUENCERS_FILE) as f:
        influencers = json.load(f)

    records = [
        {
            "name": inf["name"],
            "instagram_handle": inf.get("instagram", ""),
            "tiktok_handle": inf.get("tiktok", ""),
            "platform": "tiktok",
        }
        for inf in influencers
    ]

    inserted = 0
    for record in records:
        try:
            supabase.table("influencers").upsert(record, on_conflict="name").execute()
            inserted += 1
        except Exception as exc:
            print(f"  [WARN] Could not insert {record['name']}: {exc}")

    return inserted


def load_products(supabase) -> tuple[int, int]:
    """Insert products (and placeholder buy links) into the database."""
    if not PRODUCTS_FILE.exists():
        print("[WARN] products.json not found — run script 4 first")
        return 0, 0

    with open(PRODUCTS_FILE) as f:
        products = json.load(f)

    inserted_products = 0
    inserted_links = 0

    for product in products:
        try:
            resp = (
                supabase.table("products")
                .insert(
                    {
                        "influencer_name": product.get("influencer", ""),
                        "product_name": product.get("product_name", ""),
                        "brand": product.get("brand", ""),
                        "category": product.get("category", "other"),
                        "quote": product.get("quote", ""),
                        "video_url": product.get("video_url", ""),
                        "platform": product.get("platform", "tiktok"),
                    }
                )
                .execute()
            )
            product_id = resp.data[0]["id"]
            inserted_products += 1

            # Add placeholder buy links for Egyptian stores
            buy_links = [
                {"store": "Amazon.eg", "url": f"https://www.amazon.eg/s?k={product['product_name'].replace(' ', '+')}", "price": None},
                {"store": "Noon Egypt", "url": f"https://www.noon.com/egypt-en/search/?q={product['product_name'].replace(' ', '+')}", "price": None},
                {"store": "Jumia Egypt", "url": f"https://www.jumia.com.eg/catalog/?q={product['product_name'].replace(' ', '+')}", "price": None},
            ]
            for link in buy_links:
                try:
                    supabase.table("buy_links").insert(
                        {
                            "product_id": product_id,
                            "store": link["store"],
                            "url": link["url"],
                            "currency": "EGP",
                            "in_stock": True,
                        }
                    ).execute()
                    inserted_links += 1
                except Exception as link_exc:
                    print(f"  [WARN] Buy link error: {link_exc}")

        except Exception as exc:
            print(f"  [WARN] Could not insert product '{product.get('product_name')}': {exc}")

    return inserted_products, inserted_links


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    try:
        from supabase import create_client
    except ImportError:
        print("[ERROR] supabase not installed. Run: pip install supabase")
        return

    print("=" * 60)
    print("Step 5: Loading data into Supabase")
    print("=" * 60)

    print(f"Connecting to {SUPABASE_URL} …")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Connected\n")

    print("Loading influencers …")
    n_inf = load_influencers(supabase)
    print(f"  ✅ {n_inf} influencers loaded\n")

    print("Loading products …")
    n_prod, n_links = load_products(supabase)
    print(f"  ✅ {n_prod} products loaded")
    print(f"  ✅ {n_links} buy links loaded\n")

    print("=" * 60)
    print(f"Done! Total: {n_inf} influencers, {n_prod} products, {n_links} buy links")
    print("=" * 60)


if __name__ == "__main__":
    main()
