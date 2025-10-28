# LupinBot Dashboard - Vercel Deployment Guide

## Overview

The LupinBot Dashboard can be deployed to Vercel as a static site, but **requires the bot to be running** to serve the API data.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Vercel       │  HTTP   │   Your Bot       │  SQLite │  database.db │
│   (Frontend)   │ ────>   │   API Server     │  ────>  │              │
│   Static HTML  │ <────   │   (dashboard.py) │ <────   │              │
└─────────────────┘         └──────────────────┘         └──────────────┘
```

## Deployment Options

### Option 1: Deploy Static Dashboard to Vercel (Recommended)

The dashboard HTML can be deployed to Vercel as a static site that fetches data from your bot's API.

**Prerequisites:**
1. Your bot must be running and accessible via URL
2. Bot's `dashboard.py` must be running on a public URL

**Steps:**

1. **Update Dashboard HTML** to point to your bot's API:
   ```javascript
   // In templates/dashboard.html, change API URLs:
   const API_BASE_URL = 'https://your-bot-domain.com';  // Your bot's public URL
   ```

2. **Deploy to Vercel:**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Deploy
   vercel
   ```

3. **Set Environment Variables** (if needed):
   - None required for static deployment

### Option 2: Run Dashboard with Your Bot

Since the dashboard requires database access, the easiest approach is to run it alongside your bot:

1. **Install Dependencies:**
   ```bash
   pip install flask
   ```

2. **Run the Bot (which includes dashboard):**
   ```bash
   python main.py  # This starts the Discord bot
   python dashboard.py  # In a separate terminal, start the dashboard
   ```

3. **Access Dashboard:**
   - Open `http://localhost:5000` in your browser
   - The dashboard will fetch data from your local database

### Option 3: Deploy Bot + Dashboard Together

If you want everything on one platform:

1. **Use Railway/Render/Heroku** for the bot (supports databases)
2. **Deploy dashboard** as part of the bot's Flask app

## Quick Start (Running Locally)

The simplest way to use the dashboard:

```bash
# Terminal 1: Start the Discord bot
python main.py

# Terminal 2: Start the dashboard
python dashboard.py
```

Then open `http://localhost:5000` in your browser.

## Current Files

- **`dashboard.py`** - Flask app for dashboard API
- **`templates/dashboard.html`** - Dashboard frontend
- **`api/dashboard.py`** - Serverless API stub (for future use)
- **`vercel.json`** - Vercel configuration

## Why Not Directly on Vercel?

Vercel is serverless and doesn't support SQLite databases out of the box. The dashboard needs:
1. Access to `database.db` file
2. Persistent file storage
3. Database connections

## Recommended Approach

**For Now (Until you set up a cloud database):**
- Run the dashboard locally with the bot
- Access at `http://localhost:5000`
- All data is read from your local `database.db`

**Future (With Cloud Database):**
- Deploy to Vercel with static files
- Connect to Supabase/PlanetScale/PostgreSQL
- API endpoints fetch from cloud database

## Files Included

✅ **Ready for Deploy:**
- `dashboard.py` - Flask app
- `templates/dashboard.html` - Frontend
- `vercel.json` - Config
- `api/dashboard.py` - Serverless stub

## Next Steps

1. **Test Locally:**
   ```bash
   python dashboard.py
   ```

2. **Deploy to Vercel:**
   ```bash
   vercel
   ```

3. **Or Deploy Bot to Render/Railway** (better for database access)

## Environment Variables

If deploying to Vercel with a remote bot API:

```bash
vercel env add API_BASE_URL
# Enter: https://your-bot-url.com
```

Then update `dashboard.html` to use this URL.

