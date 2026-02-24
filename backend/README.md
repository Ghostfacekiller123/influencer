# Backend — Influencer Product Search Platform

FastAPI backend that serves the product search API. Data is stored in Supabase and populated by the pipeline scripts.

## Prerequisites

- Python 3.9+
- [Supabase](https://supabase.com) project (free tier works)
- [Groq API key](https://console.groq.com) (free)
- ffmpeg (for audio transcription): `sudo apt install ffmpeg`

## Setup

### 1. Install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:

| Variable | Where to get it |
|----------|----------------|
| `SUPABASE_URL` | Supabase project → Settings → API |
| `SUPABASE_KEY` | Supabase project → Settings → API (anon public) |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) → API Keys |
| `INSTA_USERNAME` | Your throwaway Instagram account |
| `INSTA_PASSWORD` | Your throwaway Instagram account |

### 3. Set up the database

Run the SQL schema in your Supabase project:

1. Open your Supabase dashboard → SQL Editor
2. Paste the contents of `../database/schema.sql`
3. Click **Run**

### 4. Run the data pipeline

```bash
cd scripts

# Run everything (TikTok + Instagram)
python run_all.py

# Run without Instagram (faster for MVP)
python run_all.py --skip-instagram

# Run individual steps
python 1_scrape_tiktok.py
python 2_scrape_instagram.py
python 3_transcribe.py
python 4_extract_products.py
python 5_load_database.py
```

### 5. Start the API server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/search?q=Charlotte Tilbury` | Smart product search |
| GET | `/products` | List all products |
| GET | `/influencers` | List all influencers |
| GET | `/categories` | List all categories |

### Search Examples

```bash
# Search by influencer name
curl "http://localhost:8000/search?q=Sarah%20Hany"

# Search by product/brand
curl "http://localhost:8000/search?q=Charlotte%20Tilbury"

# Search by category
curl "http://localhost:8000/search?q=skincare"
```

## Deployment (Railway)

1. Create a new [Railway](https://railway.app) project
2. Connect your GitHub repository
3. Set environment variables in Railway dashboard
4. Railway will auto-deploy using `railway.json` and `nixpacks.toml`

## Troubleshooting

**TikTok scraping fails**
→ Add your `TIKTOK_SESSION_ID` cookie to `.env`

**Instagram rate limited**
→ Add delays between requests; use a fresh throwaway account

**Whisper is slow**
→ Use `WHISPER_MODEL=tiny` for speed, or `base` for better accuracy

**Groq API errors**
→ Check your API key at [console.groq.com](https://console.groq.com)
