# 🤖 THE MONSTER - Full Automation System

A 24/7 background worker that monitors influencers, extracts products with AI, and is controlled via Telegram bot with Groq AI chat.

---

## What It Does

- **Automatic monitoring** every 6 hours (configurable)
- **Fetches Instagram content** via Apify
- **Extracts products** from captions using Groq AI
- **Auto-saves to database** with deduplication
- **Telegram bot** for mobile control from anywhere
- **AI-powered chat** — ask questions in natural language
- **Auto-adds** manually added influencers to the watchlist

---

## Setup

### 1. Run SQL Migration

Go to your Supabase project → SQL Editor → paste and run:

```
backend/migrations/create_monster_tables.sql
```

### 2. Create Telegram Bot

1. Open Telegram and message `@BotFather`
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the token you receive

### 3. Configure Environment

Add to `backend/.env`:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

Make sure these are also set:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GROQ_API_KEY`
- `APIFY_API_TOKEN`

### 4. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 5. Run the System (3 terminals)

**Terminal 1 – Main API:**
```bash
python main.py
```

**Terminal 2 – Monster worker:**
```bash
python monster.py
```

**Terminal 3 – Telegram bot:**
```bash
python telegram_bot.py
```

---

## Telegram Commands

| Command | Description |
|---|---|
| `/start` | Show welcome message and command list |
| `/status` | Monster status, product counts, today's activity |
| `/start_monster` | Activate 24/7 monitoring |
| `/stop_monster` | Deactivate monitoring |
| `/parse @handle` | Parse a specific influencer immediately |
| `/watchlist` | Show all monitored influencers |
| `/add @handle` | Add influencer to watchlist |
| `/remove @handle` | Remove influencer from watchlist |
| `/logs` | Show recent processing activity |

---

## AI Chat Examples

Just send a normal message — no command needed!

```
You: "How many products do we have?"
Bot: "We have 1,247 products from 89 influencers babe! 🔥"

You: "Who's the top influencer?"
Bot: "Huda Beauty is dominating! 156 products total! 👑"

You: "Is the monster running?"
Bot: "🟢 Yeah basha, it's active and watching 24/7! 💪"
```

---

## REST API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/admin/monster/status` | Get monster status and stats |
| POST | `/admin/monster/start` | Activate monitoring |
| POST | `/admin/monster/stop` | Deactivate monitoring |
| POST | `/admin/monster/parse-now/{handle}` | Parse influencer immediately |
| GET | `/admin/watchlist` | List watchlist |
| POST | `/admin/watchlist/add` | Add to watchlist |
| DELETE | `/admin/watchlist/remove/{handle}` | Remove from watchlist |

---

## Troubleshooting

**Monster not running?**
- Check `monster_config` table: `is_active` must be `true`
- Run `/start_monster` in Telegram or `POST /admin/monster/start`

**Telegram bot not responding?**
- Verify `TELEGRAM_BOT_TOKEN` is set in `.env`
- Ensure `telegram_bot.py` process is running

**No products extracted?**
- Check `APIFY_API_TOKEN` and `GROQ_API_KEY` are valid
- Check `processing_logs` table for error messages

**Duplicate products?**
- Deduplication is automatic (by `product_name` + `influencer_handle`)
- Existing products are silently skipped
