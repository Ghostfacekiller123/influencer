# Frontend — Influencer Product Search Platform

Next.js 14 frontend with TypeScript and Tailwind CSS.

## Prerequisites

- Node.js 18+
- npm or yarn
- Running backend API (see `../backend/README.md`)

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env.local
# Edit .env.local — point NEXT_PUBLIC_API_URL to your backend
```

For local development:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production (after deploying backend to Railway):
```
NEXT_PUBLIC_API_URL=https://your-railway-app.up.railway.app
```

### 3. Run development server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Building for Production

```bash
npm run build
npm run start
```

## Deployment (Vercel — recommended)

1. Push your repository to GitHub
2. Import the repo at [vercel.com](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Add environment variable `NEXT_PUBLIC_API_URL` with your Railway backend URL
5. Click **Deploy**

## Pages

| Path | Description |
|------|-------------|
| `/` | Main search page |

## Components

| Component | Description |
|-----------|-------------|
| `SearchBar` | Search input with submit button and Enter-key support |
| `ProductCard` | Product card with buy links, quote, and video link |

## Customisation

- **Colors**: Edit `tailwind.config.ts` → `theme.extend.colors`
- **API URL**: Set `NEXT_PUBLIC_API_URL` in `.env.local`
- **Category tags**: Edit `CATEGORY_COLORS` in `ProductCard.tsx`

## Troubleshooting

**"Failed to fetch results"**
→ Make sure the backend is running at `NEXT_PUBLIC_API_URL`

**CORS errors in browser console**
→ The backend already enables CORS for all origins. Ensure the URL in `.env.local` is correct.

**Fonts not loading**
→ Requires internet access for Google Fonts. Add `unoptimized: true` to `next.config.js` if deploying offline.
