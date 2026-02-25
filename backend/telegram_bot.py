"""
Telegram bot for controlling the Monster influencer monitoring system.
"""

import os

from dotenv import load_dotenv
from groq import Groq
from supabase import create_client, Client
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# ── Database helpers ───────────────────────────────────────────────────────────

def get_database_stats() -> dict:
    """Get total products, watchlist counts, today's stats, and monster status."""
    try:
        products_result = supabase.table("products").select("id", count="exact").execute()
        total_products = products_result.count or 0

        influencers_result = supabase.table("products").select("influencer_handle").execute()
        unique_handles = set(r["influencer_handle"] for r in (influencers_result.data or []) if r.get("influencer_handle"))
        total_influencers = len(unique_handles)

        watchlist_result = supabase.table("influencer_watchlist").select("id", count="exact").eq(
            "status", "active"
        ).execute()
        watchlist_count = watchlist_result.count or 0

        from datetime import datetime
        today = datetime.utcnow().date().isoformat()
        logs_result = supabase.table("processing_logs").select("products_saved").gte(
            "created_at", today
        ).execute()
        products_today = sum(l.get("products_saved", 0) for l in (logs_result.data or []))

        config_result = supabase.table("monster_config").select("is_active").limit(1).execute()
        is_active = config_result.data[0].get("is_active", False) if config_result.data else False

        top_inf = {}
        if influencers_result.data:
            for r in influencers_result.data:
                h = r.get("influencer_handle", "")
                if h:
                    top_inf[h] = top_inf.get(h, 0) + 1
        top_influencer = max(top_inf, key=top_inf.get) if top_inf else "N/A"
        top_count = top_inf.get(top_influencer, 0)

        return {
            "total_products": total_products,
            "total_influencers": total_influencers,
            "watchlist_count": watchlist_count,
            "products_today": products_today,
            "is_active": is_active,
            "top_influencer": top_influencer,
            "top_influencer_count": top_count,
        }
    except Exception as e:
        return {"error": str(e)}


async def ai_chat(user_message: str, stats: dict) -> str:
    """Send message to Groq with database context and personality."""
    system_prompt = f"""You are "The Monster" - an AI managing an influencer product tracking system.

Current stats:
- Total products: {stats.get('total_products', 0)}
- Total influencers tracked: {stats.get('total_influencers', 0)}
- Watchlist (active): {stats.get('watchlist_count', 0)}
- Products added today: {stats.get('products_today', 0)}
- Monster status: {'🟢 ACTIVE' if stats.get('is_active') else '🔴 INACTIVE'}
- Top influencer: {stats.get('top_influencer', 'N/A')} ({stats.get('top_influencer_count', 0)} products)

Personality: Confident, savage, Egyptian/MENA slang. Use "babe", "ya basha", "boss", emojis 🔥💪👑.
Keep responses concise but informative."""

    try:
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI error: {e}"


# ── Command handlers ───────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 THE MONSTER is online!\n\n"
        "Commands:\n"
        "/status - System status\n"
        "/start_monster - Activate monitoring\n"
        "/stop_monster - Deactivate monitoring\n"
        "/parse @handle - Parse an influencer now\n"
        "/watchlist - Show watchlist\n"
        "/add @handle - Add to watchlist\n"
        "/remove @handle - Remove from watchlist\n"
        "/logs - Recent activity\n\n"
        "Or just chat with me! 🔥"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_database_stats()
    if "error" in stats:
        await update.message.reply_text(f"❌ Error fetching stats: {stats['error']}")
        return

    state = "🟢 ACTIVE" if stats["is_active"] else "🔴 INACTIVE"
    msg = (
        f"{state}\n\n"
        f"📊 {stats['total_products']:,} products from {stats['total_influencers']} influencers\n"
        f"👀 {stats['watchlist_count']} on watchlist\n"
        f"💪 Added {stats['products_today']} products today\n"
        f"👑 Top: @{stats['top_influencer']} ({stats['top_influencer_count']} products)"
    )
    await update.message.reply_text(msg)


async def start_monster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from datetime import datetime
        supabase.table("monster_config").update({
            "is_active": True,
            "updated_at": datetime.utcnow().isoformat(),
        }).neq("id", "00000000-0000-0000-0000-000000000000").execute()
        await update.message.reply_text("🔥 Monster ACTIVATED! Watching 24/7 ya basha!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def stop_monster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from datetime import datetime
        supabase.table("monster_config").update({
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat(),
        }).neq("id", "00000000-0000-0000-0000-000000000000").execute()
        await update.message.reply_text("😴 Monster stopped. Taking a nap babe.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /parse @handle")
        return

    handle = context.args[0].lstrip("@")
    await update.message.reply_text(f"🔥 Parsing @{handle}... Hold tight babe!")

    try:
        from monster import Monster
        monster = Monster()
        result = monster.process_influencer(handle, "instagram")
        if result.get("success"):
            saved = result.get("products_saved", 0)
            found = result.get("products_found", 0)
            await update.message.reply_text(
                f"✅ Done! Found {found} products, saved {saved} new ones! 🔥"
            )
        else:
            await update.message.reply_text(f"❌ Failed: {result.get('error')}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = supabase.table("influencer_watchlist").select("handle", "platform", "status", "total_products_found").order(
            "created_at", desc=True
        ).execute()
        items = result.data or []
        if not items:
            await update.message.reply_text("📋 Watchlist is empty babe!")
            return
        lines = [f"📋 Watchlist ({len(items)} influencers):"]
        for item in items[:20]:
            status_icon = "🟢" if item.get("status") == "active" else "🔴"
            lines.append(f"{status_icon} @{item['handle']} - {item.get('total_products_found', 0)} products")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def add_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /add @handle")
        return
    handle = context.args[0].lstrip("@")
    try:
        supabase.table("influencer_watchlist").insert({
            "handle": handle,
            "platform": "instagram",
            "status": "active",
            "added_by": "telegram",
        }).execute()
        await update.message.reply_text(f"✅ Added @{handle} to watchlist! 💪")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def remove_from_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /remove @handle")
        return
    handle = context.args[0].lstrip("@")
    try:
        supabase.table("influencer_watchlist").delete().eq("handle", handle).execute()
        await update.message.reply_text(f"✅ Removed @{handle} from watchlist.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = supabase.table("processing_logs").select("*").order(
            "created_at", desc=True
        ).limit(10).execute()
        items = result.data or []
        if not items:
            await update.message.reply_text("📜 No logs yet babe!")
            return
        lines = ["📜 Recent activity:"]
        for log in items:
            status_icon = "✅" if log.get("status") == "success" else "❌"
            lines.append(
                f"{status_icon} @{log.get('influencer_handle', '?')} - "
                f"{log.get('products_saved', 0)} saved | "
                f"{log.get('created_at', '')[:16]}"
            )
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages with AI chat."""
    user_message = update.message.text
    stats = get_database_stats()
    response = await ai_chat(user_message, stats)
    await update.message.reply_text(response)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable must be set.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("start_monster", start_monster))
    app.add_handler(CommandHandler("stop_monster", stop_monster))
    app.add_handler(CommandHandler("parse", parse))
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(CommandHandler("add", add_to_watchlist))
    app.add_handler(CommandHandler("remove", remove_from_watchlist))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Telegram bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
