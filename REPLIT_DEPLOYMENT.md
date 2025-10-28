# Deploy LupinBot to Replit - Complete Guide

## 📋 Overview

This guide will help you safely deploy LupinBot to Replit with all features working correctly.

## ⚠️ Important: Before Exporting

### Files to Include ✅

```
LupinBotV/
├── main.py                      # Bot entry point
├── pyproject.toml               # Dependencies
├── .env                         # Environment variables (see below)
├── database.py                  # Database handler
├── dashboard.py                 # Dashboard server
├── cache.py                     # Caching system
├── gemini.py                    # AI integrations
├── start_dashboard.py           # Dashboard launcher
├── cogs/                        # All cog files
│   ├── __init__.py
│   ├── streaks.py
│   ├── fun.py
│   ├── challenges.py
│   ├── moderation.py
│   └── utilities.py
└── templates/                   # Dashboard HTML
    └── dashboard.html
```

### Files to EXCLUDE ❌

```
❌ database.db                   # Will be created fresh
❌ __pycache__/                  # Python cache
❌ *.log                         # Log files
❌ .env                          # (Copy manually, don't commit secret)
❌ replit.db                     # If exists
❌ README_DEV.md                  # Internal docs
```

## 🔐 Step 1: Environment Variables

### Critical: Copy Your .env

**DO NOT** commit your `.env` file with real credentials! Instead:

1. **Copy your `.env` contents** to a notepad
2. **In Replit**, add secrets via the Secrets tab
3. **Never commit** `.env` to version control

### Required Environment Variables

```bash
# Required
DISCORD_TOKEN=your_bot_token_here

# Optional - Gemini AI features
GEMINI_API_KEY=your_gemini_key_here

# Optional - Replit Nix environment (auto-set by Replit)
REPL_ID=your_repl_id
REPL_SLUG=your_repl_slug
```

## 📦 Step 2: Export to Replit

### Option A: GitHub Import (Recommended)

1. **Create a .gitignore first:**
   ```bash
   # Add to .gitignore
   database.db
   __pycache__/
   *.log
   .env
   .DS_Store
   ```

2. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/LupinBot.git
   git push -u origin main
   ```

3. **In Replit:**
   - Click "Import from GitHub"
   - Enter your repository URL
   - Click "Import"

### Option B: Manual Upload

1. **Create a new Repl:**
   - Choose "Python" as language
   - Name it "LupinBot"

2. **Upload files via Replit's file upload**

## 🔧 Step 3: Setup in Replit

### 1. Install Dependencies

Replit will auto-install from `pyproject.toml`, but if needed:

```bash
# In Replit shell
pip install -r requirements.txt
```

Or if using `pyproject.toml`:
```bash
pip install -e .
```

### 2. Set Up Secrets

1. Go to **Secrets** tab (lock icon) in Replit
2. Add these secrets:

| Key | Value | Example |
|-----|-------|---------|
| `DISCORD_TOKEN` | Your Discord bot token | `MTIzNDU2Nzg5MDEyMzQ1Njc...` |
| `GEMINI_API_KEY` | Your Gemini API key | `AIzaSyA...` |

### 3. Create .env File in Replit

```bash
# In Replit shell
cat > .env << EOF
DISCORD_TOKEN=$DISCORD_TOKEN
GEMINI_API_KEY=$GEMINI_API_KEY
EOF
```

## 🚀 Step 4: Database Configuration

### Database File Location

Replit uses `/home/runner/` as the persistent directory.

Update `database.py` for Replit compatibility:

```python
# In database.py __init__
import os

def __init__(self, db_name: str = "database.db"):
    # Use /home/runner/ for persistent storage in Replit
    if os.path.exists('/home/runner'):
        self.db_name = f'/home/runner/{db_name}'
    else:
        self.db_name = db_name
    self.init_db()
```

Or keep it simple - SQLite works fine in Replit's file system.

## ⚙️ Step 5: Configure main.py

### Update for Replit

Add Replit-specific configuration in `main.py`:

```python
# At the top of main.py
import os

# Replit detection
IS_REPLIT = os.path.exists('/home/runner')
if IS_REPLIT:
    print('🦊 Running on Replit!')
```

### Optional: Always On Keep-Alive

For Replit's free tier, add a keep-alive ping:

```python
# Add to main.py

from flask import Flask
from threading import Thread

# Keep-alive server for Replit free tier
def create_keep_alive():
    server = Flask(__name__)
    
    @server.route('/')
    def home():
        return "LupinBot is running! 🦊"
    
    @server.route('/health')
    def health():
        return jsonify({"status": "ok"})
    
    server.run(host='0.0.0.0', port=8080)

# Start keep-alive in background
if IS_REPLIT:
    keep_alive = Thread(target=create_keep_alive, daemon=True)
    keep_alive.start()
```

## 🎮 Step 6: Run the Bot

### Start the Bot

```python
# In Replit's run configuration or in main.py

if __name__ == '__main__':
    import asyncio
    print('🚀 Starting LupinBot on Replit...')
    asyncio.run(main())
```

### Run Command

In Replit, just click **Run** or use the shell:

```bash
python main.py
```

## 📊 Step 7: Dashboard (Optional)

### If You Want the Dashboard on Replit

The dashboard can run alongside the bot:

```python
# Add to main.py

from dashboard import run_dashboard as start_dashboard

def start_dashboard_thread():
    """Start dashboard in background thread."""
    try:
        start_dashboard(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logger.error(f'Dashboard error: {e}')

# In main() function before bot.start():
if IS_REPLIT:
    dashboard_thread = Thread(target=start_dashboard_thread, daemon=True)
    dashboard_thread.start()
    logger.info('📊 Dashboard available at: http://0.0.0.0:5000')
```

Access dashboard at: `https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co`

## 🔒 Security Checklist

Before deploying to Replit:

- [ ] `.env` is NOT committed to git
- [ ] Discord token is in Replit Secrets
- [ ] Gemini API key is in Replit Secrets
- [ ] `.gitignore` includes sensitive files
- [ ] Database file is in persistent directory
- [ ] Bot intents are properly configured

## 📝 Replit-Specific Files

### Create `.replit` (Optional)

```toml
run = "python main.py"
entrypoint = "main.py"
interpreter = [["python", "-u", "$file"]]

[nix]
channel = "stable-22_11"

[deploy]
run = ["sh", "-c", "python main.py"]
```

### Create `replit.nix` (Optional)

```nix
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.python311Packages.pylint
  ];
}
```

## 🌐 Web View (Optional)

### Enable Web View

1. Go to **Tools** → **Webview** in Replit
2. Set to **Enabled**
3. Your dashboard will be accessible publicly

### Web View URLs

- **Main:** `https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co`
- **Dashboard:** `https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co:5000`

## 🛠️ Troubleshooting

### Issue: Bot disconnects frequently

**Solution:** Add keep-alive ping:
```python
# In main.py
import time

# Keep-alive loop
def keep_alive():
    while True:
        time.sleep(300)  # Ping every 5 minutes
        logger.info("Keep-alive ping")

thread = Thread(target=keep_alive, daemon=True)
thread.start()
```

### Issue: Database not persisting

**Solution:** Use persistent directory:
```python
import os

# Check if running on Replit
if os.path.exists('/home/runner'):
    DB_PATH = '/home/runner/database.db'
else:
    DB_PATH = 'database.db'
```

### Issue: "Module not found" errors

**Solution:** Install dependencies:
```bash
# In Replit shell
pip install discord.py python-dotenv aiohttp
```

### Issue: Secrets not working

**Solution:**
1. Check **Secrets** tab has correct key names
2. Ensure `.env` file is updated
3. Restart the Repl

## 📦 Complete File Structure for Replit

```
replit/
├── main.py                      # ✅ Start here
├── pyproject.toml               # ✅ Dependencies
├── .replit                      # ✅ Replit config
├── replit.nix                   # ✅ Nix environment
├── .env                         # ⚠️  Add manually in Replit
├── .gitignore                   # ✅ Don't commit secrets
├── database.py                  # ✅ Database handler
├── cache.py                     # ✅ Caching
├── gemini.py                    # ✅ AI features
├── dashboard.py                 # ✅ Dashboard server
├── start_dashboard.py           # ✅ Dashboard launcher
├── cogs/                        # ✅ All cogs
│   ├── streaks.py
│   ├── fun.py
│   ├── challenges.py
│   ├── moderation.py
│   └── utilities.py
└── templates/                   # ✅ Dashboard UI
    └── dashboard.html
```

## 🚀 Quick Start Commands

### In Replit Shell:

```bash
# Install dependencies
pip install -r requirements.txt

# Or if using pyproject.toml
pip install -e .

# Set up .env (already done if you used Secrets)
# Run the bot
python main.py
```

## ✅ Deployment Checklist

- [ ] All files uploaded to Replit
- [ ] `.env` configured with Discord token
- [ ] Gemini API key added (if using)
- [ ] Dependencies installed
- [ ] Database path configured
- [ ] Bot intents enabled
- [ ] Bot runs without errors
- [ ] Dashboard accessible (if enabled)
- [ ] Keep-alive configured (for free tier)

## 🎉 Success!

Once deployed:

1. **Bot Status:** Check logs for "Bot is ready!"
2. **Dashboard:** Access at Replit URL
3. **Test Commands:** Try `/help` in Discord
4. **Monitor:** Watch logs for any errors

## 📞 Need Help?

Check these files:
- `SETUP.md` - Original setup
- `README.md` - Bot documentation
- `DASHBOARD_SETUP.md` - Dashboard info
- `DEPLOYMENT_STATUS.md` - Deployment info

## 🔄 Updating the Bot

### To update from GitHub:

```bash
# In Replit shell
git pull origin main
```

### To update manually:

1. Re-upload changed files
2. Click **Run** to restart

## 💡 Pro Tips

1. **Always On:** Use Replit's "Always On" feature for free tier stability
2. **Logs:** Check Replit's Logs panel for debugging
3. **Secrets:** Never hardcode tokens in code
4. **Backup:** Export `database.db` periodically
5. **Testing:** Test commands before promoting to production

---

**Ready to deploy!** 🚀

Follow these steps and your LupinBot will be running on Replit in minutes!

