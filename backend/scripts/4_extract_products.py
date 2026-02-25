"""
Script 4: Extract product mentions from transcripts using Groq AI.

Usage:
    python 4_extract_products.py

Requires:
    GROQ_API_KEY  (get free key at https://console.groq.com)
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TRANSCRIPTS_FILE = DATA_DIR / "processed" / "transcriptions.json"
OUTPUT_FILE = DATA_DIR / "products.json"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-70b-versatile"

SYSTEM_PROMPT = """You are a product extraction assistant specializing in beauty and lifestyle content 
from Egyptian and MENA influencers. Your task is to identify products mentioned in video transcripts.

Extract products and return a JSON array. Each product must have:
- product_name: specific product name (e.g., "Charlotte Tilbury Pillow Talk Lipstick")
- brand: brand name (e.g., "Charlotte Tilbury")
- category: one of [skincare, makeup, haircare, fragrance, fashion, food, tech, other]
- quote: the exact quote from the transcript where this product is mentioned (in original language)

Rules:
- Only extract real, specific products with brand names
- If the transcript is in Arabic, keep the quote in Arabic
- If no products are found, return an empty array []
- Do NOT invent products not mentioned in the transcript
- Return ONLY the JSON array, no other text
"""


def extract_products(client, transcript: dict) -> list[dict]:
    """Call Groq API to extract products from one transcript."""
    text = transcript.get("transcript", "").strip()
    if not text or len(text) < 20:
        return []

    user_prompt = f"""Extract all products mentioned in this video transcript from influencer {transcript['influencer']}:

---
{text}
---

Return a JSON array of products."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        products = json.loads(raw)
        if not isinstance(products, list):
            return []

        # Attach metadata to each product
        enriched = []
        for p in products:
            if not p.get("product_name"):
                continue
            enriched.append(
                {
                    "influencer": transcript["influencer"],
                    "platform": transcript["platform"],
                    "video_url": transcript["url"],
                    "product_name": p.get("product_name", ""),
                    "brand": p.get("brand", ""),
                    "category": p.get("category", "other"),
                    "quote": p.get("quote", ""),
                }
            )
        return enriched

    except json.JSONDecodeError as exc:
        print(f"    [WARN] JSON parse error: {exc}")
        return []
    except Exception as exc:
        print(f"    [WARN] API error: {exc}")
        return []


def main():
    if not GROQ_API_KEY:
        print("[ERROR] GROQ_API_KEY not set in .env file")
        return

    try:
        from groq import Groq
    except ImportError:
        print("[ERROR] groq not installed. Run: pip install groq")
        return

    print("=" * 60)
    print("Step 4: Extracting products with AI")
    print("=" * 60)

    if not TRANSCRIPTS_FILE.exists():
        print("[ERROR] transcripts.json not found. Run script 3 first.")
        return

    with open(TRANSCRIPTS_FILE) as f:
        transcripts = json.load(f)

    print(f"Loaded {len(transcripts)} transcripts\n")

    client = Groq(api_key=GROQ_API_KEY)
    all_products: list[dict] = []

    for i, transcript in enumerate(transcripts, 1):
        print(f"[{i}/{len(transcripts)}] Processing {transcript['influencer']} — {transcript['url']}")
        products = extract_products(client, transcript)
        print(f"    Found {len(products)} product(s)")
        all_products.extend(products)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved {len(all_products)} products to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
