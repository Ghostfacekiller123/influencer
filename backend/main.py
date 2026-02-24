"""
FastAPI backend for the Influencer Product Search Platform.

Endpoints:
    GET /                    - Health check
    GET /search?q={query}    - Smart product search
    GET /products            - List all products
    GET /influencers         - List all influencers
    GET /categories          - List all categories

Environment variables:
    SUPABASE_URL
    SUPABASE_KEY
"""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# ── Supabase client ────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY environment variables must be set."
    )

from supabase import create_client, Client  # noqa: E402

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Influencer Product Search API",
    description="Search for products used by Egyptian/MENA influencers",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch_buy_links(product_ids: list[str]) -> dict[str, list[dict]]:
    """Return a mapping of product_id → list of buy links."""
    if not product_ids:
        return {}

    resp = (
        supabase.table("buy_links")
        .select("*")
        .in_("product_id", product_ids)
        .execute()
    )
    links: dict[str, list[dict]] = {}
    for row in resp.data:
        pid = row["product_id"]
        links.setdefault(pid, []).append(row)
    return links


def enrich_products(products: list[dict]) -> list[dict]:
    """Attach buy_links to each product record."""
    ids = [p["id"] for p in products]
    links_map = fetch_buy_links(ids)
    for p in products:
        p["buy_links"] = links_map.get(p["id"], [])
    return products


def detect_influencer(query: str, influencers: list[dict]) -> Optional[str]:
    """Return influencer name if query contains their name (case-insensitive)."""
    query_lower = query.lower()
    for inf in influencers:
        if inf["name"].lower() in query_lower:
            return inf["name"]
    return None


KNOWN_CATEGORIES = [
    "skincare", "makeup", "haircare", "fragrance", "fashion",
    "food", "tech", "lifestyle", "beauty", "other",
]


def detect_category(query: str) -> Optional[str]:
    """Return category if query contains a known category keyword."""
    query_lower = query.lower()
    for cat in KNOWN_CATEGORIES:
        if cat in query_lower:
            return cat
    return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Influencer Product Search API"}


@app.get("/search")
def search(q: str = Query(..., min_length=1, description="Search query")):
    """
    Smart search endpoint.

    Detects influencer names and/or categories in the query and filters
    accordingly, falling back to full-text search across product fields.
    """
    try:
        # Fetch influencers to check for name matches
        inf_resp = supabase.table("influencers").select("name").execute()
        influencers = inf_resp.data or []

        influencer_name = detect_influencer(q, influencers)
        category = detect_category(q)

        query_builder = supabase.table("products").select("*")

        if influencer_name:
            query_builder = query_builder.ilike("influencer_name", f"%{influencer_name}%")

        if category:
            query_builder = query_builder.ilike("category", f"%{category}%")

        if not influencer_name and not category:
            # Full-text search across product_name, brand, quote
            query_builder = query_builder.or_(
                f"product_name.ilike.%{q}%,brand.ilike.%{q}%,quote.ilike.%{q}%"
            )

        resp = query_builder.limit(50).execute()
        products = resp.data or []
        products = enrich_products(products)

        return {
            "query": q,
            "detected_influencer": influencer_name,
            "detected_category": category,
            "count": len(products),
            "results": products,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/products")
def list_products(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all products with buy links."""
    try:
        resp = (
            supabase.table("products")
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )
        products = enrich_products(resp.data or [])
        return {"count": len(products), "results": products}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/influencers")
def list_influencers():
    """List all influencers."""
    try:
        resp = supabase.table("influencers").select("*").execute()
        return {"count": len(resp.data), "results": resp.data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/categories")
def list_categories():
    """List all distinct product categories."""
    try:
        resp = supabase.table("products").select("category").execute()
        categories = sorted(
            {row["category"] for row in (resp.data or []) if row.get("category")}
        )
        return {"count": len(categories), "results": categories}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
