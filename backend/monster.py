"""
The Monster - 24/7 background worker for influencer product monitoring.
Monitors influencers from watchlist every 6 hours, extracts products via Groq AI,
and saves to database with deduplication.
"""

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")


class Monster:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.running = False

    # ── Instagram content via Apify ────────────────────────────────────────────

    def fetch_instagram_content(self, handle: str) -> list[dict]:
        """Fetch Instagram posts/reels for the given handle via Apify."""
        from apify_client import ApifyClient

        client = ApifyClient(APIFY_API_TOKEN)
        print(f"  📥 Fetching Instagram content for @{handle}...")

        run = client.actor("apify/instagram-reel-scraper").call(
            run_input={"username": [handle], "resultsLimit": 20}
        )
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"  ✅ Fetched {len(items)} posts")
        return items

    # ── AI product extraction ──────────────────────────────────────────────────

    def extract_products_with_ai(self, posts: list[dict], handle: str) -> list[dict]:
        """Use Groq AI to extract products from Instagram posts."""
        if not posts:
            return []

        captions = []
        for post in posts:
            caption = post.get("caption") or post.get("text", "")
            url = (
                post.get("url")
                or post.get("shortCode")
                and f"https://www.instagram.com/p/{post['shortCode']}/"
                or ""
            )
            if caption.strip():
                captions.append({"caption": caption, "url": url})

        if not captions:
            return []

        posts_text = "\n\n".join(
            f"Post URL: {c['url']}\nCaption: {c['caption']}" for c in captions[:15]
        )

        prompt = f"""Analyze Instagram posts from @{handle} and extract ALL products.

For each product return:
{{
  "product_name": "exact name",
  "brand": "brand or Unknown",
  "category": "skincare/makeup/haircare/fragrance/other",
  "influencer_quote": "direct quote about product",
  "post_url": "instagram url"
}}

Posts:
{posts_text}

Return ONLY JSON array. If no products: []"""

        try:
            response = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
            )

            raw = response.choices[0].message.content.strip()

            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:-1])
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            json_start = raw.find("[")
            json_end = raw.rfind("]") + 1
            if json_start != -1 and json_end > 0:
                raw = raw[json_start:json_end]

            products = json.loads(raw)
            print(f"  🤖 AI extracted {len(products)} products")
            return products

        except Exception as e:
            print(f"  ⚠️ AI extraction failed: {e}")
            return []

    # ── Save products with deduplication ──────────────────────────────────────

    def save_products_to_db(
        self, products: list[dict], handle: str, profile_pic: str = ""
    ) -> int:
        """Save products to database, skipping duplicates. Returns count saved."""
        saved = 0

        for product in products:
            product_name = product.get("product_name", "").strip()
            if not product_name:
                continue

            try:
                existing = (
                    self.supabase.table("products")
                    .select("id")
                    .eq("product_name", product_name)
                    .eq("influencer_name", handle)
                    .execute()
                )

                if existing.data:
                    continue  # Don't save duplicate

                self.supabase.table("products").insert(
                    {
                        "product_name": product_name,
                        "brand": product.get("brand", "Unknown"),
                        "category": product.get("category", "other"),
                        "quote": product.get("influencer_quote", ""),
                        "influencer_name": handle,
                        "influencer_profile_pic": profile_pic,
                        "platform": "instagram",
                        "video_url": product.get("post_url", ""),
                    }
                ).execute()
                saved += 1

            except Exception as e:
                print(f"  ⚠️ Failed to save product '{product_name}': {e}")

        return saved

    # ── Process one influencer ─────────────────────────────────────────────────

    def process_influencer(self, influencer: dict) -> dict:
        """Run the full monitoring pipeline for a single influencer."""
        handle = influencer["handle"]
        platform = influencer.get("platform", "instagram")
        start_time = time.time()

        print(f"\n🔍 Processing @{handle} ({platform})")

        result = {
            "handle": handle,
            "platform": platform,
            "products_found": 0,
            "products_saved": 0,
            "status": "success",
            "error": None,
        }

        try:
            posts = self.fetch_instagram_content(handle)

            profile_pic = ""
            if posts:
                profile_pic = posts[0].get("ownerProfilePicUrl") or ""

            products = self.extract_products_with_ai(posts, handle)
            result["products_found"] = len(products)

            saved = self.save_products_to_db(products, handle, profile_pic)
            result["products_saved"] = saved

            # Update watchlist entry
            self.supabase.table("influencer_watchlist").update(
                {
                    "last_checked_at": datetime.utcnow().isoformat(),
                    "total_products_found": (
                        influencer.get("total_products_found", 0) + saved
                    ),
                }
            ).eq("handle", handle).eq("platform", platform).execute()

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"  ❌ Error processing @{handle}: {e}")

        execution_time = time.time() - start_time

        # Log the run
        try:
            self.supabase.table("processing_logs").insert(
                {
                    "influencer_handle": handle,
                    "platform": platform,
                    "action": "monitor",
                    "status": result["status"],
                    "products_found": result["products_found"],
                    "products_saved": result["products_saved"],
                    "error_message": result.get("error"),
                    "execution_time_seconds": execution_time,
                }
            ).execute()
        except Exception as log_err:
            print(f"  ⚠️ Failed to write log: {log_err}")

        print(
            f"  ✅ Done: {result['products_found']} found, "
            f"{result['products_saved']} saved ({execution_time:.1f}s)"
        )
        return result

    # ── Run a full monitoring cycle ────────────────────────────────────────────

    def run_monitoring_cycle(self):
        """Process all active influencers in the watchlist."""
        print(f"\n{'='*60}")
        print(f"🤖 MONSTER CYCLE START: {datetime.utcnow().isoformat()}")
        print(f"{'='*60}")

        try:
            resp = (
                self.supabase.table("influencer_watchlist")
                .select("*")
                .eq("status", "active")
                .execute()
            )
            watchlist = resp.data or []
        except Exception as e:
            print(f"❌ Failed to fetch watchlist: {e}")
            return

        print(f"👀 Monitoring {len(watchlist)} influencers")

        for influencer in watchlist:
            self.process_influencer(influencer)
            time.sleep(5)  # Polite delay between influencers

        print(f"\n✅ MONSTER CYCLE COMPLETE: {datetime.utcnow().isoformat()}")

    # ── Main loop ──────────────────────────────────────────────────────────────

    def start(self):
        """Run the monster loop until is_active is set to false in DB."""
        self.running = True
        print("🔥 THE MONSTER IS ALIVE! 🔥")

        while self.running:
            try:
                config_resp = self.supabase.table("monster_config").select("*").limit(1).execute()
                config = config_resp.data[0] if config_resp.data else {}

                if not config.get("is_active", False):
                    print("😴 Monster is paused. Checking again in 60s...")
                    time.sleep(60)
                    continue

                interval = config.get("monitoring_interval", 21600)
                self.run_monitoring_cycle()

                print(f"💤 Sleeping for {interval}s until next cycle...")
                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n🛑 Monster stopped by user")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Monster loop error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    monster = Monster()
    monster.start()
