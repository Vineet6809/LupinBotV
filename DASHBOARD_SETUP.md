# LupinBot Dashboard Setup Guide

## 🎯 Quick Start (Recommended)

### Run Dashboard Locally

The easiest way to use the dashboard is to run it locally alongside your bot:

```bash
# Install Flask if not already installed
pip install flask

# Run the dashboard
python start_dashboard.py
```

Then open: **http://localhost:5000**

## 📋 Requirements

- Python 3.8+
- Flask (`pip install flask`)
- The bot's `database.db` file (created when you run the bot)

## 🚀 Running the Dashboard

### Option 1: Quick Start Script
```bash
python start_dashboard.py
```

### Option 2: Direct Python
```bash
python dashboard.py
```

### Option 3: With Custom Port
```bash
python dashboard.py 8080  # Runs on port 8080
```

## 🌐 Deployment Options

### Option A: Run Locally (Easiest)

Since the dashboard reads from your local `database.db`:

1. **Start your Discord bot:**
   ```bash
   python main.py
   ```

2. **Start the dashboard:**
   ```bash
   python start_dashboard.py
   ```

3. **Access the dashboard:**
   - Open http://localhost:5000
   - Select a guild from the dropdown
   - View real-time statistics

### Option B: Deploy to Railway/Render (Full Stack)

If you want to host the dashboard publicly:

1. **Deploy the bot** to Railway or Render
   - They support persistent file storage
   - Your `database.db` will persist
   
2. **Dashboard automatically works** since it's part of the bot

### Option C: Static Site on Vercel (Requires API)

If you want Vercel specifically:

1. **First, host your bot's API** on Railway/Render
2. **Modify `dashboard.py`** to expose a public endpoint
3. **Update `templates/dashboard.html`** to fetch from that API
4. **Deploy static files** to Vercel

**Note:** Vercel serverless functions don't support SQLite well, so you'll need an external database or API.

## 📊 Dashboard Features

✅ **Server Statistics**
- Total coders
- Active today
- Total days coded
- Average streak
- Activity rate

✅ **Leaderboard**
- Top 10 coders
- Current streaks
- Longest streaks
- Medal system (🥇🥈🥉)

✅ **Interactive Charts**
- Leaderboard trends
- Activity distribution

✅ **Auto-Refresh**
- Updates every 10 seconds
- Toggle on/off

## 🔧 Troubleshooting

### "database.db not found"
**Solution:** Run your bot at least once to create the database:
```bash
python main.py
```

### "Flask not installed"
**Solution:** Install Flask:
```bash
pip install flask
```

### "No guilds found"
**Solution:** The bot needs to have tracked at least one user. Have someone run a command like `/mystats` or share code.

### Port 5000 already in use
**Solution:** Use a different port:
```bash
python dashboard.py 8080  # Use port 8080
```

## 💡 How It Works

The dashboard reads directly from your local `database.db` file:

```
Discord Bot (main.py)
        ↓
Writes to database.db ← Reads dashboard.py
        ↓
Displays on web UI (http://localhost:5000)
```

## 🎨 Customization

### Change Port
Edit `dashboard.py`:
```python
run_dashboard(host='0.0.0.0', port=8080)  # Your custom port
```

### Change Host
For network access:
```python
run_dashboard(host='0.0.0.0', port=5000)  # Accessible on local network
```

Then access via: `http://YOUR_IP:5000`

## 📁 File Structure

```
LupinBotV/
├── dashboard.py              # Flask server
├── start_dashboard.py         # Easy launcher
├── database.db               # Database (created by bot)
├── templates/
│   └── dashboard.html        # Frontend UI
├── vercel.json               # Vercel config (for static deploy)
├── api/
│   ├── dashboard.py          # Serverless stub
│   └── requirements.txt      # Dependencies
└── DASHBOARD_SETUP.md        # This file
```

## 🚨 Important Notes

1. **Keep the bot running** - The dashboard reads from `database.db` in real-time
2. **Database is local** - The `database.db` file stores all your data
3. **Public deployment** requires hosting both bot and dashboard on Railway/Render/Heroku
4. **Vercel limitation** - Vercel doesn't support persistent file storage easily

## ✅ Current Status

The dashboard is **ready to use**! Just run:
```bash
python start_dashboard.py
```

Then open: http://localhost:5000

## 🎯 For Vercel Deployment

If you specifically need Vercel:

1. **Host your bot API** on Railway/Render (https://your-bot-api.com)
2. **Create a simple API endpoint** in your bot that serves JSON
3. **Deploy static HTML** to Vercel that calls your bot's API
4. See `VERCEL_DEPLOYMENT.md` for details

## 🆘 Need Help?

Check:
- `README.md` - General bot info
- `SETUP.md` - Bot setup
- `VERCEL_DEPLOYMENT.md` - Vercel-specific deployment

