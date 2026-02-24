# What Does She Use? 💄

> Search for products used by top Egyptian & MENA beauty influencers — and find where to buy them in Egypt.

![Screenshot placeholder](https://placehold.co/1200x600/ec4899/ffffff?text=What+Does+She+Use%3F+%F0%9F%92%84)

---

## Features

- 🔍 **Multi-influencer search** — search by influencer name, product, brand, or category
- 🌍 **Arabic & English support** — Whisper + Groq handle bilingual content
- 📹 **Video proof** — every product links back to the original TikTok/Instagram video
- 🛒 **Egyptian e-commerce** — buy links for Amazon.eg, Noon Egypt, and Jumia Egypt
- ⚡ **Automated pipeline** — scrape → transcribe → extract → deploy, end-to-end

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- ffmpeg: `sudo apt install ffmpeg`
- A [Supabase](https://supabase.com) account (free)
- A [Groq](https://console.groq.com) API key (free)

### 1. Get API Keys

| Service | URL | Notes |
|---------|-----|-------|
| Supabase | [supabase.com](https://supabase.com) | Free tier — create project, copy URL & anon key |
| Groq | [console.groq.com](https://console.groq.com) | Free — create API key |
| Instagram | [instagram.com](https://instagram.com) | Create throwaway account |

### 2. Set Up Database

1. Open your Supabase project → **SQL Editor**
2. Paste the contents of `database/schema.sql`
3. Click **Run**

### 3. Configure Environment

```bash
# Backend
cp backend/.env.example backend/.env
# Fill in SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY

# Frontend
cp frontend/.env.example frontend/.env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 5. Run the Data Pipeline

```bash
cd backend/scripts
python run_all.py --skip-instagram  # TikTok only (faster for MVP)
```

This will:
1. Scrape TikTok videos from 50 influencers
2. Extract captions / transcribe with Whisper
3. Extract product mentions using Groq AI
4. Load everything into Supabase

### 6. Start the Backend API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 7. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) 🎉

---

## Architecture

```
User searches ──► Next.js frontend ──► FastAPI backend ──► Supabase (PostgreSQL)
                                                 ↑
                           Automated pipeline (scripts/)
                           1. Scrape TikTok / Instagram
                           2. Transcribe with Whisper
                           3. Extract products with Groq AI
                           4. Load into database
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.9 |
| Database | Supabase (PostgreSQL) |
| AI / NLP | Groq (Llama 3.1 70B), OpenAI Whisper |
| Scraping | TikTokApi, instaloader, Playwright |
| Deployment | Railway (backend), Vercel (frontend) |

---

## Deployment

### Backend → Railway

1. Create a [Railway](https://railway.app) project
2. Connect your GitHub repository
3. Set the **Root Directory** to `backend`
4. Add environment variables (from `backend/.env.example`)
5. Railway auto-deploys via `railway.json`

### Frontend → Vercel

1. Import repository at [vercel.com](https://vercel.com)
2. Set Root Directory to `frontend`
3. Add `NEXT_PUBLIC_API_URL` = your Railway backend URL
4. Deploy

---

## Development

```bash
# Run backend with hot reload
cd backend && uvicorn main:app --reload

# Run individual pipeline steps
cd backend/scripts
python 1_scrape_tiktok.py
python 4_extract_products.py   # re-run AI extraction without re-scraping
python 5_load_database.py      # reload database after changes

# Run frontend with hot reload
cd frontend && npm run dev
```

---

## Roadmap

| Timeline | Goal |
|----------|------|
| Week 1 | MVP with TikTok captions for 50 influencers |
| Week 2 | Add Instagram reels support |
| Week 3 | Arabic full-text search improvements |
| Month 2 | Scale to 100+ influencers, real-time price updates |
| Month 3 | User accounts, wishlists, price alerts |

---

## License

MIT — see [LICENSE](LICENSE) for details.
