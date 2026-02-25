"""
Telegram Bot for The Monster - AI-powered influencer product tracker.
Talks in gangsta/savage Egyptian slang with full attitude.
"""

import json
import os
from datetime import datetime, date

from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# ── DB helpers ─────────────────────────────────────────────────────────────────

def get_db_stats() -> dict:
    """Fetch live stats from the database."""
    try:
        products_resp = supabase.table("products").select("id, created_at").execute()
        all_products = products_resp.data or []
        total_products = len(all_products)

        today_str = date.today().isoformat()
        products_today = sum(
            1 for p in all_products
            if (p.get("created_at") or "").startswith(today_str)
        )

        watchlist_resp = (
            supabase.table("influencer_watchlist")
            .select("id")
            .eq("status", "active")
            .execute()
        )
        active_count = len(watchlist_resp.data or [])

        config_resp = supabase.table("monster_config").select("*").limit(1).execute()
        config = config_resp.data[0] if config_resp.data else {}
        is_active = config.get("is_active", False)

        # Top 5 influencers by product count
        top_resp = (
            supabase.table("products")
            .select("influencer_name")
            .execute()
        )
        influencer_counts: dict = {}
        for row in (top_resp.data or []):
            name = row.get("influencer_name", "unknown")
            influencer_counts[name] = influencer_counts.get(name, 0) + 1

        top_list = sorted(influencer_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_list_str = ", ".join(f"{name}({cnt})" for name, cnt in top_list)

        return {
            "total_products": total_products,
            "products_today": products_today,
            "active_count": active_count,
            "is_active": "RUNNING 🔥" if is_active else "PAUSED 😴",
            "top_list": top_list_str or "none yet",
        }
    except Exception as e:
        return {
            "total_products": 0,
            "products_today": 0,
            "active_count": 0,
            "is_active": "UNKNOWN",
            "top_list": "error fetching",
        }


# ── AI chat ────────────────────────────────────────────────────────────────────

def ai_chat(user_message: str) -> str:
    """Send user message to Groq with gangsta personality, return response."""
    stats = get_db_stats()

    system_prompt = f"""You are "The Monster" - an AI managing influencer product tracking.

Database Stats:
- Total Products: {stats['total_products']}
- Products Today: {stats['products_today']}
- Active Watchlist: {stats['active_count']} influencers
- Monster Status: {stats['is_active']}
- Top Influencers: {stats['top_list']}

PERSONALITY (CRITICAL):
- Talk like a savage gangsta with Egyptian slang
- Use: "yo", "ayy", "fam", "babe", "boss", "ya basha", "no cap"
- Call influencers "bitches" casually
- Emojis: 🔥💪👑💯🍽️💰🎯
- Confident, bragging, hustler mentality
- Keep it real, street-smart responses
- "We eating", "built different", "crushing it", "the game don't stop"
- Never be corporate or formal - pure street energy

User Message: {user_message}

Respond naturally with gangsta energy. If asking stats, give numbers with attitude. If chatting, keep it savage!"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": system_prompt}],
            temperature=0.8,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ayy something broke fam 😤 Error: {e}"


# ── Intent detection ──────────────────────────────────────────────────────────

def detect_intent(user_message: str) -> dict:
    """Use AI to detect what the user wants to do."""
    prompt = f"""Analyze this message and detect the user's intent.

User message: "{user_message}"

Return JSON with intent and parameters:

Possible intents:
- "parse_influencer" - user wants to scrape an influencer
- "delete_product" - user wants to delete a product
- "edit_link" - user wants to change a product link
- "list_products" - user wants to see products from an influencer
- "start_monster" - activate monitoring
- "stop_monster" - pause monitoring
- "status" - check stats
- "hunt_influencers" - find top trending influencers
- "add_to_watchlist" - add influencer to auto-monitoring
- "chat" - just chatting, no action

Examples:
"parse sarah.hany" → {{"intent": "parse_influencer", "handle": "sarah.hany", "count": 10}}
"delete product #23" → {{"intent": "delete_product", "product_id": 23}}
"show me what sarah has" → {{"intent": "list_products", "handle": "sarah"}}
"hunt top beauty influencers" → {{"intent": "hunt_influencers", "category": "beauty", "count": 10}}
"change link for product 15" → {{"intent": "edit_link", "product_id": 15}}

Return ONLY JSON, no markdown.
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return {"intent": "chat"}


# ── Product management helpers ─────────────────────────────────────────────────

def list_products_by_influencer(handle: str) -> str:
    """List all products from an influencer with IDs."""
    try:
        resp = supabase.table("products").select("*").ilike("influencer_name", f"%{handle}%").execute()
        products = resp.data or []

        if not products:
            return f"Yo fam, ain't got no products from {handle} yet! 💀"

        msg = f"📦 **Products from {products[0].get('influencer_name', handle)}** ({len(products)} total):\n\n"
        for p in products[:50]:
            msg += f"🆔 **ID {p['id']}**: {p['product_name']}\n"
            if p.get("brand"):
                msg += f"   Brand: {p['brand']}\n"
            if p.get("post_url"):
                msg += f"   Link: {p['post_url'][:60]}...\n"
            msg += "\n"
        return msg
    except Exception as e:
        return f"Error fetching products: {e}"


def delete_product(product_id: int) -> str:
    """Delete a product by ID."""
    try:
        resp = supabase.table("products").select("product_name, influencer_name").eq("id", product_id).execute()
        if not resp.data:
            return f"Yo, product #{product_id} don't exist babe! 🤷"

        product = resp.data[0]
        supabase.table("products").delete().eq("id", product_id).execute()
        return f"✅ Deleted that shit! Product '{product['product_name']}' from {product['influencer_name']} is GONE! 🗑️🔥"
    except Exception as e:
        return f"Error deleting: {e}"


def edit_product_link(product_id: int, new_link: str) -> str:
    """Update product link."""
    try:
        resp = supabase.table("products").select("product_name").eq("id", product_id).execute()
        if not resp.data:
            return f"Product #{product_id} not found babe!"

        supabase.table("products").update({"post_url": new_link}).eq("id", product_id).execute()
        return f"✅ Updated link for product #{product_id}! New link saved! 🔗✨"
    except Exception as e:
        return f"Error updating: {e}"


def hunt_trending_influencers(category: str = "beauty", count: int = 10) -> str:
    """Search for trending influencers in a category."""
    prompt = f"""List the top {count} trending {category} influencers on Instagram in Egypt/MENA region in 2024-2026.

Return ONLY a JSON array of handles (without @):
["handle1", "handle2", "handle3"]

Focus on active influencers with recent content.
"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        handles = json.loads(response.choices[0].message.content.strip())
        msg = f"🔥 **Top {category.title()} Influencers:**\n\n"
        for i, handle in enumerate(handles[:count], 1):
            msg += f"{i}. @{handle}\n"
        msg += f"\n💬 Which one you want me to parse, boss? Tell me the handle and how many reels! 🎯"
        return msg
    except Exception as e:
        return f"Couldn't hunt influencers: {e}"


# ── Command handlers ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ayy what's good boss! 👑 I'm THE MONSTER 🤖🔥\n\n"
        "I track influencer products 24/7 with zero chill!\n\n"
        "Commands:\n"
        "/status - Stats with attitude\n"
        "/start_monster - Activate monitoring\n"
        "/stop_monster - Pause monitoring\n"
        "/parse @handle - Parse an influencer now\n"
        "/watchlist - Who we watching\n"
        "/add @handle - Add to watchlist\n"
        "/remove @handle - Remove from watchlist\n"
        "/logs - Recent activity\n\n"
        "Or just talk to me fam! I understand natural language 💯"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_db_stats()
    await update.message.reply_text(
        f"Ayy here's the rundown boss! 🔥\n\n"
        f"📦 Total Products: {stats['total_products']}\n"
        f"📈 Added Today: {stats['products_today']}\n"
        f"👀 Watching: {stats['active_count']} bitches\n"
        f"🤖 Monster Status: {stats['is_active']}\n"
        f"👑 Top Bitches: {stats['top_list']}\n\n"
        f"The grind never stops fam! 💪💯"
    )


async def cmd_start_monster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config_resp = supabase.table("monster_config").select("id").limit(1).execute()
        if config_resp.data:
            supabase.table("monster_config").update(
                {"is_active": True, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", config_resp.data[0]["id"]).execute()
        else:
            supabase.table("monster_config").insert(
                {"is_active": True, "monitoring_interval": 21600}
            ).execute()
        await update.message.reply_text(
            "YO THE MONSTER IS ACTIVATED! 🔥🤖 We out here grinding 24/7 babe! "
            "Monitoring all the bitches, no cap! 💪👑"
        )
    except Exception as e:
        await update.message.reply_text(f"Ayy something went wrong fam 😤: {e}")


async def cmd_stop_monster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        config_resp = supabase.table("monster_config").select("id").limit(1).execute()
        if config_resp.data:
            supabase.table("monster_config").update(
                {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
            ).eq("id", config_resp.data[0]["id"]).execute()
        await update.message.reply_text(
            "Aight the monster is chilling for now 😴 Say /start_monster when you ready to get back to the grind boss! 💯"
        )
    except Exception as e:
        await update.message.reply_text(f"Ayy something went wrong fam 😤: {e}")


async def cmd_parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Yo gimme a handle fam! Usage: /parse @handle or /parse handle 🎯"
        )
        return

    handle = args[0].lstrip("@")
    await update.message.reply_text(
        f"Say less boss! 🔥 I'm on @{handle} right now, pulling everything..."
    )

    try:
        from monster import Monster
        monster = Monster()

        influencer = {"handle": handle, "platform": "instagram", "total_products_found": 0}
        result = monster.process_influencer(influencer)

        # Auto-add to watchlist if not there
        try:
            existing = (
                supabase.table("influencer_watchlist")
                .select("id")
                .eq("handle", handle)
                .eq("platform", "instagram")
                .execute()
            )
            if not existing.data:
                supabase.table("influencer_watchlist").insert(
                    {
                        "handle": handle,
                        "platform": "instagram",
                        "status": "active",
                        "added_by": "telegram",
                    }
                ).execute()
        except Exception:
            pass

        if result["products_saved"] > 0:
            await update.message.reply_text(
                f"✅ YOOO we just pulled {result['products_saved']} new products from @{handle}! "
                f"Database updated, we eating! 🍽️💰"
            )
        else:
            await update.message.reply_text(
                f"👀 Checked @{handle} - found {result['products_found']} products but they all already in the DB fam! "
                f"No duplicates, we clean! 💯"
            )
    except Exception as e:
        await update.message.reply_text(
            f"Damn something broke fam 😤 Error: {e}"
        )


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = (
            supabase.table("influencer_watchlist")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        items = resp.data or []

        if not items:
            await update.message.reply_text(
                "Yo watchlist empty fam! Use /add @handle to add some bitches! 🎯"
            )
            return

        lines = [f"👑 We watching {len(items)} bitches:\n"]
        for item in items[:20]:
            status_icon = "🟢" if item.get("status") == "active" else "🔴"
            lines.append(
                f"{status_icon} @{item['handle']} | "
                f"{item.get('total_products_found', 0)} products"
            )

        await update.message.reply_text("\n".join(lines) + "\n\nThe game don't stop fam! 💪🔥")
    except Exception as e:
        await update.message.reply_text(f"Ayy error fam 😤: {e}")


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Gimme a handle yo! Usage: /add @handle 🎯"
        )
        return

    handle = args[0].lstrip("@")
    try:
        existing = (
            supabase.table("influencer_watchlist")
            .select("id")
            .eq("handle", handle)
            .eq("platform", "instagram")
            .execute()
        )
        if existing.data:
            await update.message.reply_text(
                f"Ayy @{handle} already in the watchlist fam! We already on that! 💯"
            )
            return

        supabase.table("influencer_watchlist").insert(
            {
                "handle": handle,
                "platform": "instagram",
                "status": "active",
                "added_by": "telegram",
            }
        ).execute()
        await update.message.reply_text(
            f"✅ YO! @{handle} added to the watchlist boss! We watching her now 24/7! 👑🔥"
        )
    except Exception as e:
        await update.message.reply_text(f"Ayy error fam 😤: {e}")


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Gimme a handle yo! Usage: /remove @handle 🎯"
        )
        return

    handle = args[0].lstrip("@")
    try:
        supabase.table("influencer_watchlist").delete().eq(
            "handle", handle
        ).eq("platform", "instagram").execute()
        await update.message.reply_text(
            f"🗑️ @{handle} removed from watchlist fam! She out! 💯"
        )
    except Exception as e:
        await update.message.reply_text(f"Ayy error fam 😤: {e}")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = (
            supabase.table("processing_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        logs = resp.data or []

        if not logs:
            await update.message.reply_text(
                "No logs yet fam! Run the monster and come back! 🔥"
            )
            return

        lines = ["📊 Recent Activity:\n"]
        for log in logs:
            status_icon = "✅" if log.get("status") == "success" else "❌"
            lines.append(
                f"{status_icon} @{log.get('influencer_handle', '?')} - "
                f"{log.get('products_saved', 0)} saved | "
                f"{log.get('created_at', '')[:16]}"
            )

        await update.message.reply_text("\n".join(lines) + "\n\nWe grinding non-stop babe! 💪")
    except Exception as e:
        await update.message.reply_text(f"Ayy error fam 😤: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all messages with intent detection."""
    user_message = update.message.text or ""

    # Handle pending link-edit state
    if context.user_data.get("editing_product"):
        product_id = context.user_data["editing_product"]
        new_link = user_message
        result = edit_product_link(product_id, new_link)
        await update.message.reply_text(result)
        context.user_data["editing_product"] = None
        return

    # Detect intent
    intent_data = detect_intent(user_message)
    intent = intent_data.get("intent", "chat")

    if intent == "parse_influencer":
        handle = intent_data.get("handle", "")
        count = intent_data.get("count", 10)
        await update.message.reply_text(
            f"🔥 Say less boss! Parsing @{handle}, pulling {count} reels... Give me a sec! 💪"
        )
        try:
            from monster import Monster
            monster = Monster()
            influencer = {"handle": handle, "platform": "instagram", "total_products_found": 0}
            result = monster.process_influencer(influencer)
            try:
                existing = (
                    supabase.table("influencer_watchlist")
                    .select("id")
                    .eq("handle", handle)
                    .eq("platform", "instagram")
                    .execute()
                )
                if not existing.data:
                    supabase.table("influencer_watchlist").insert(
                        {"handle": handle, "platform": "instagram", "status": "active", "added_by": "telegram"}
                    ).execute()
            except Exception:
                pass
            if result["products_saved"] > 0:
                await update.message.reply_text(
                    f"✅ YOOO we just pulled {result['products_saved']} new products from @{handle}! We eating! 🍽️💰"
                )
            else:
                await update.message.reply_text(
                    f"👀 Checked @{handle} - found {result['products_found']} products but they all already in the DB fam! No duplicates, we clean! 💯"
                )
        except Exception as e:
            await update.message.reply_text(f"Damn something broke fam 😤 Error: {e}")

    elif intent == "delete_product":
        product_id = intent_data.get("product_id")
        if product_id is None:
            await update.message.reply_text("Yo gimme the product ID fam! Like 'delete product #23' 🎯")
        else:
            result = delete_product(int(product_id))
            await update.message.reply_text(result)

    elif intent == "edit_link":
        product_id = intent_data.get("product_id")
        if product_id is None:
            await update.message.reply_text("Yo gimme the product ID fam! Like 'change link for product 15' 🔗")
        else:
            context.user_data["editing_product"] = int(product_id)
            await update.message.reply_text(
                f"Aight! Send me the new CDN link for product #{product_id}! 🔗"
            )

    elif intent == "list_products":
        handle = intent_data.get("handle", "")
        if not handle:
            await update.message.reply_text("Yo gimme a handle fam! Like 'show me sarah's products' 🎯")
        else:
            result = list_products_by_influencer(handle)
            await update.message.reply_text(result, parse_mode="Markdown")

    elif intent == "hunt_influencers":
        category = intent_data.get("category", "beauty")
        count = intent_data.get("count", 10)
        result = hunt_trending_influencers(category, count)
        await update.message.reply_text(result, parse_mode="Markdown")

    elif intent == "start_monster":
        try:
            config_resp = supabase.table("monster_config").select("id").limit(1).execute()
            if config_resp.data:
                supabase.table("monster_config").update(
                    {"is_active": True, "updated_at": datetime.utcnow().isoformat()}
                ).eq("id", config_resp.data[0]["id"]).execute()
            else:
                supabase.table("monster_config").insert(
                    {"is_active": True, "monitoring_interval": 21600}
                ).execute()
            await update.message.reply_text("🔥 MONSTER ACTIVATED! Let's get this bread! 💰💪")
        except Exception as e:
            await update.message.reply_text(f"Ayy something went wrong fam 😤: {e}")

    elif intent == "stop_monster":
        try:
            config_resp = supabase.table("monster_config").select("id").limit(1).execute()
            if config_resp.data:
                supabase.table("monster_config").update(
                    {"is_active": False, "updated_at": datetime.utcnow().isoformat()}
                ).eq("id", config_resp.data[0]["id"]).execute()
            await update.message.reply_text("😴 Monster taking a nap. Wake me up when you ready fam!")
        except Exception as e:
            await update.message.reply_text(f"Ayy something went wrong fam 😤: {e}")

    elif intent == "add_to_watchlist":
        handle = intent_data.get("handle", "")
        if not handle:
            await update.message.reply_text("Yo gimme a handle fam! 🎯")
        else:
            try:
                existing = (
                    supabase.table("influencer_watchlist")
                    .select("id")
                    .eq("handle", handle)
                    .eq("platform", "instagram")
                    .execute()
                )
                if existing.data:
                    await update.message.reply_text(
                        f"Ayy @{handle} already in the watchlist fam! We already on that! 💯"
                    )
                else:
                    supabase.table("influencer_watchlist").insert(
                        {"handle": handle, "platform": "instagram", "status": "active", "added_by": "telegram"}
                    ).execute()
                    await update.message.reply_text(
                        f"✅ YO! @{handle} added to the watchlist boss! We watching her now 24/7! 👑🔥"
                    )
            except Exception as e:
                await update.message.reply_text(f"Ayy error fam 😤: {e}")

    elif intent == "status":
        stats = get_db_stats()
        await update.message.reply_text(
            f"Ayy here's the rundown boss! 🔥\n\n"
            f"📦 Total Products: {stats['total_products']}\n"
            f"📈 Added Today: {stats['products_today']}\n"
            f"👀 Watching: {stats['active_count']} bitches\n"
            f"🤖 Monster Status: {stats['is_active']}\n"
            f"👑 Top Bitches: {stats['top_list']}\n\n"
            f"The grind never stops fam! 💪💯"
        )

    else:
        # Regular chat
        response = ai_chat(user_message)
        await update.message.reply_text(response)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable must be set.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("start_monster", cmd_start_monster))
    app.add_handler(CommandHandler("stop_monster", cmd_stop_monster))
    app.add_handler(CommandHandler("parse", cmd_parse))
    app.add_handler(CommandHandler("watchlist", cmd_watchlist))
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("remove", cmd_remove))
    app.add_handler(CommandHandler("logs", cmd_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Monster Telegram Bot is running! 🔥")
    app.run_polling()


if __name__ == "__main__":
    main()
