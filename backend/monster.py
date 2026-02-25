"""
Monster - 24/7 background worker for automated influencer product monitoring.
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
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.config = {}

    def load_config(self) -> dict:
        """Load settings from monster_config table."""
        try:
            result = self.supabase.table("monster_config").select("*").limit(1).execute()
            if result.data:
                self.config = result.data[0]
            else:
                self.config = {"is_active": False, "monitoring_interval": 21600}
        except Exception as e:
            print(f"⚠️  Failed to load config: {e}")
            self.config = {"is_active": False, "monitoring_interval": 21600}
        return self.config

    def log_activity(self, influencer_handle: str, platform: str, action: str,
                     status: str, products_found: int = 0, products_saved: int = 0,
                     error_message: str = None, execution_time_seconds: float = None):
        """Log activity to processing_logs table."""
        try:
            self.supabase.table("processing_logs").insert({
                "influencer_handle": influencer_handle,
                "platform": platform,
                "action": action,
                "status": status,
                "products_found": products_found,
                "products_saved": products_saved,
                "error_message": error_message,
                "execution_time_seconds": execution_time_seconds,
            }).execute()
        except Exception as e:
            print(f"⚠️  Failed to log activity: {e}")

    def fetch_instagram_content(self, handle: str, limit: int = 20) -> list:
        """Fetch Instagram posts/reels via Apify."""
        try:
            from apify_client import ApifyClient
            client = ApifyClient(APIFY_API_TOKEN)
            print(f"  📥 Fetching Instagram content for @{handle}...")
            run = client.actor("apify/instagram-reel-scraper").call(
                run_input={"username": [handle], "resultsLimit": limit}
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            print(f"  ✅ Found {len(items)} posts")
            return items
        except Exception as e:
            print(f"  ❌ Failed to fetch content for @{handle}: {e}")
            return []

    def extract_products_with_ai(self, items: list, handle: str) -> list:
        """Use Groq AI to extract products from post captions."""
        if not items:
            return []

        captions = []
        for item in items[:20]:
            caption = item.get("caption") or item.get("text") or ""
            url = item.get("url") or item.get("shortCode") or ""
            if url and not url.startswith("http"):
                url = f"https://www.instagram.com/p/{url}/"
            if caption:
                captions.append({"caption": caption[:500], "url": url})

        if not captions:
            return []

        captions_text = "\n\n".join(
            [f"Post URL: {c['url']}\nCaption: {c['caption']}" for c in captions]
        )

        prompt = f"""Extract ALL products from these Instagram posts.
Return a JSON array only, no other text:
[{{
  "product_name": "...",
  "brand": "...",
  "category": "...",
  "influencer_quote": "...",
  "post_url": "..."
}}]

Instagram posts from @{handle}:
{captions_text}"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()

            # Extract JSON array from response
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                return []

            products = json.loads(raw[start:end])
            return products if isinstance(products, list) else []

        except Exception as e:
            print(f"  ⚠️  AI extraction failed: {e}")
            return []

    def save_products_to_db(self, products: list, handle: str, platform: str) -> int:
        """Save products to database with deduplication. Returns count saved."""
        saved = 0
        for product in products:
            product_name = product.get("product_name", "").strip()
            if not product_name:
                continue
            try:
                existing = self.supabase.table("products").select("id").eq(
                    "product_name", product_name
                ).eq("influencer_handle", handle).execute()

                if existing.data and len(existing.data) > 0:
                    continue  # Skip duplicate

                self.supabase.table("products").insert({
                    "product_name": product_name,
                    "brand": product.get("brand", ""),
                    "category": product.get("category", ""),
                    "influencer_quote": product.get("influencer_quote", ""),
                    "post_url": product.get("post_url", ""),
                    "influencer_handle": handle,
                    "platform": platform,
                }).execute()
                saved += 1

            except Exception as e:
                print(f"  ⚠️  Failed to save product '{product_name}': {e}")

        return saved

    def process_influencer(self, handle: str, platform: str = "instagram") -> dict:
        """Run full pipeline for one influencer."""
        start_time = time.time()
        print(f"\n{'='*50}")
        print(f"🔍 Processing @{handle} ({platform})")

        try:
            items = self.fetch_instagram_content(handle)
            products = self.extract_products_with_ai(items, handle)
            saved = self.save_products_to_db(products, handle, platform)

            elapsed = time.time() - start_time

            # Update last_checked_at and total_products_found
            try:
                self.supabase.table("influencer_watchlist").update({
                    "last_checked_at": datetime.utcnow().isoformat(),
                    "total_products_found": saved,
                }).eq("handle", handle).eq("platform", platform).execute()
            except Exception as e:
                print(f"  ⚠️  Failed to update watchlist: {e}")

            self.log_activity(
                influencer_handle=handle,
                platform=platform,
                action="monitor",
                status="success",
                products_found=len(products),
                products_saved=saved,
                execution_time_seconds=elapsed,
            )

            print(f"  ✅ Done: {len(products)} found, {saved} saved ({elapsed:.1f}s)")
            return {"success": True, "products_found": len(products), "products_saved": saved}

        except Exception as e:
            elapsed = time.time() - start_time
            self.log_activity(
                influencer_handle=handle,
                platform=platform,
                action="monitor",
                status="error",
                error_message=str(e),
                execution_time_seconds=elapsed,
            )
            print(f"  ❌ Failed: {e}")
            return {"success": False, "error": str(e)}

    def get_active_influencers(self) -> list:
        """Get all active influencers from watchlist."""
        try:
            result = self.supabase.table("influencer_watchlist").select("*").eq(
                "status", "active"
            ).execute()
            return result.data or []
        except Exception as e:
            print(f"⚠️  Failed to get watchlist: {e}")
            return []

    def run_monitoring_cycle(self):
        """Check all active influencers in the watchlist."""
        print(f"\n{'#'*60}")
        print(f"🤖 MONSTER CYCLE START: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{'#'*60}")

        influencers = self.get_active_influencers()
        print(f"📋 {len(influencers)} influencers to process")

        for inf in influencers:
            self.process_influencer(inf["handle"], inf.get("platform", "instagram"))

        print(f"\n✅ Monitoring cycle complete")

    def start(self):
        """Main loop: run every monitoring_interval seconds."""
        print("🤖 Monster starting up...")
        while True:
            self.load_config()
            if self.config.get("is_active", False):
                self.run_monitoring_cycle()
            else:
                print(f"😴 Monster is inactive. Checking again in 60s...")
                time.sleep(60)
                continue

            interval = self.config.get("monitoring_interval", 21600)
            print(f"\n⏰ Next cycle in {interval // 3600}h {(interval % 3600) // 60}m. Sleeping...")
            time.sleep(interval)


if __name__ == "__main__":
    monster = Monster()
    monster.start()
