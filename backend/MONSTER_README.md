# 🤖 THE MONSTER - Smart AI Automation System

A 24/7 background worker with AI-powered Telegram bot that monitors influencers and tracks products with gangsta energy.

---

## 🎯 What It Does

- **Background Worker** – Monitors influencers from watchlist every 6 hours automatically
- **AI Product Extraction** – Groq AI extracts products from Instagram posts
- **Telegram Bot** – Control everything from your phone with savage personality
- **Smart AI Chat** – Understands natural language, responds with gangsta attitude
- **Auto-Watchlist** – Manually added influencers are auto-tracked
- **Deduplication** – No duplicate products ever saved

---

## 🗃️ Database Setup

Run the migration in your Supabase SQL editor:

```bash
# Copy contents of backend/migrations/create_monster_tables.sql
# Paste into Supabase SQL editor and run
```

Creates three tables:
- `influencer_watchlist` – Who we're watching
- `monster_config` – Monster on/off switch and settings
- `processing_logs` – Activity logs

---

## 🔐 Environment Setup

Add to `backend/.env`:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
```

### Get Your Telegram Bot Token:
1. Open Telegram and message **@BotFather**
2. Send `/newbot`
3. Follow the prompts, pick a name and username
4. Copy the token BotFather gives you
5. Paste it in `.env` as `TELEGRAM_BOT_TOKEN`

---

## 📦 Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## 🚀 How to Run (3 Terminals)

**Terminal 1 – Telegram Bot:**
```bash
cd backend
python telegram_bot.py
```

**Terminal 2 – Monster Worker:**
```bash
cd backend
python monster.py
```

**Terminal 3 – FastAPI Server:**
```bash
cd backend
uvicorn main:app --reload
```

---

## 📱 Telegram Commands

| Command | What It Does |
|---------|-------------|
| `/start` | Introduction and command list |
| `/status` | Show stats with gangsta attitude |
| `/start_monster` | Activate 24/7 monitoring |
| `/stop_monster` | Pause monitoring |
| `/parse @handle` | Parse an influencer right now |
| `/watchlist` | Show who we're watching |
| `/add @handle` | Add influencer to watchlist |
| `/remove @handle` | Remove from watchlist |
| `/logs` | Show recent activity |

---

## 💬 AI Chat Examples

Just talk to the bot naturally – no commands needed!

```
You: "yo what's good"
Monster: "Ayy what's good boss! 🔥 We crushing it! 1,247 products, 67 today, watching 47 bitches! 💪👑"

You: "parse huda beauty"
Monster: "Say less boss! 🔥 I'm on that shit right now, pulling everything from @huda_beauty..."
Monster: "✅ YOOO we just pulled 12 new products from her! Database updated, we eating! 🍽️💰"

You: "who's killing it this week"
Monster: "Huda Beauty running the game rn no cap! 👑 She dropped 45 products this week! 💯🔥"

You: "how many products we got"
Monster: "We sitting on 1,247 products from 89 bitches fam! 💰 Added 67 today alone! 📊🔥"
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/monster/status` | Get monster status and stats |
| POST | `/admin/monster/start` | Activate monitoring |
| POST | `/admin/monster/stop` | Pause monitoring |
| POST | `/admin/monster/parse-now/{handle}` | Parse influencer immediately |
| GET | `/admin/watchlist` | Get full watchlist |
| POST | `/admin/watchlist/add` | Add to watchlist |
| DELETE | `/admin/watchlist/remove/{handle}` | Remove from watchlist |

---

## ⚙️ Configuration

The monster is configured via the `monster_config` database table:

| Field | Default | Description |
|-------|---------|-------------|
| `is_active` | `false` | Turn monster on/off |
| `monitoring_interval` | `21600` | Seconds between cycles (6 hours) |
| `max_influencers_to_monitor` | `100` | Max per cycle |

Use the API or Telegram bot to change settings.

---

## 🔧 Troubleshooting

**Bot not responding?**
- Check `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Make sure `python telegram_bot.py` is running

**Monster not monitoring?**
- Send `/start_monster` in Telegram, or call `POST /admin/monster/start`
- Check `is_active` is `true` in `monster_config` table

**No products being extracted?**
- Check `APIFY_API_TOKEN` is set in `.env`
- Check `GROQ_API_KEY` is set in `.env`
- Check `/logs` in Telegram for error messages

**Duplicate products?**
- The system auto-deduplicates by `(product_name, influencer_name)`
- If duplicates exist, they were added before deduplication was enabled

---

## 🔥 RESULT: Smart AI automation + Gangsta personality + Mobile control = UNSTOPPABLE 🤖💪
