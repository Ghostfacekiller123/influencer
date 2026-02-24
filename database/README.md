# Database Setup

This directory contains the SQL schema for the Influencer Product Search Platform.

## Prerequisites

- A [Supabase](https://supabase.com) account (free tier is sufficient)

## Setup Steps

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **New Project**
3. Fill in project details and choose a region close to Egypt (e.g., EU West)
4. Save your database password

### 2. Run the Schema

1. Open your Supabase project dashboard
2. Go to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the entire contents of `schema.sql`
5. Paste into the editor and click **Run**

You should see: `Success. No rows returned`

### 3. Get Your API Keys

1. Go to **Settings** → **API** in your Supabase dashboard
2. Copy:
   - **Project URL** → use as `SUPABASE_URL`
   - **anon public** key → use as `SUPABASE_KEY`

### 4. Configure Backend

Add the keys to `backend/.env`:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
```

## Tables

| Table | Description |
|-------|-------------|
| `influencers` | Influencer profiles (name, handles, platform) |
| `products` | Products mentioned in videos with quotes and video URLs |
| `buy_links` | Purchase links for each product (store, price, URL) |

## Troubleshooting

**Error: extension "uuid-ossp" already exists**
→ Safe to ignore, the extension is already installed.

**Error: relation already exists**
→ The table was already created. Drop it first with `DROP TABLE IF EXISTS table_name CASCADE;`

**Row Level Security blocking reads**
→ Make sure the public read policies were created successfully.
