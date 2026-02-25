"""
Extract product mentions from transcriptions using Groq AI
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Paths
TRANSCRIPTS_FILE = Path("data/processed/transcriptions.json")
OUTPUT_FILE = Path("data/processed/products.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Groq setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a product extraction assistant for beauty and lifestyle influencer content.

Extract products mentioned in video transcripts and return a JSON array.

Each product must have:
- product_name: specific product name with brand (e.g., "Fenty Beauty Pro Filt'r Foundation")
- brand: brand name (e.g., "Fenty Beauty")
- category: one of [skincare, makeup, haircare, fragrance, fashion, food, tech, other]
- quote: exact quote from transcript where product is mentioned

Rules:
- Only extract real, specific products with brand names
- If no products found, return empty array []
- Return ONLY the JSON array, no other text
"""

def extract_products(transcript: dict) -> list[dict]:
    """Extract products from one transcript using Groq"""
    text = transcript.get("text", "").strip()
    
    if not text or len(text) < 20:
        return []
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract products from:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Clean markdown
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        products = json.loads(raw.strip())
        
        if not isinstance(products, list):
            return []
        
        # Add metadata
        enriched = []
        for p in products:
            if p.get("product_name"):
                enriched.append({
                    "influencer": transcript.get("video_id", "Unknown"),
                    "platform": transcript.get("platform", "Unknown"),
                    "product_name": p.get("product_name", ""),
                    "brand": p.get("brand", ""),
                    "category": p.get("category", "other"),
                    "quote": p.get("quote", ""),
                })
        
        return enriched
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return []

def main():
    print("="*60)
    print("Extracting Products with AI")
    print("="*60)
    
    if not TRANSCRIPTS_FILE.exists():
        print(f"❌ File not found: {TRANSCRIPTS_FILE.absolute()}")
        return
    
    with open(TRANSCRIPTS_FILE, "r", encoding="utf-8") as f:
        transcripts = json.load(f)
    
    print(f"\n📄 Found {len(transcripts)} transcriptions\n")
    
    all_products = []
    
    for i, transcript in enumerate(transcripts, 1):
        video_id = transcript.get("video_id", f"video_{i}")
        print(f"{i}/{len(transcripts)}: {video_id}")
        
        products = extract_products(transcript)
        
        if products:
            all_products.extend(products)
            print(f"  ✅ Found {len(products)} products")
        else:
            print(f"  ⏭️  No products")
    
    # Save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, indent=2)
    
    print(f"\n💾 Saved {len(all_products)} products to: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()