# Export LupinBot to Replit - Quick Reference

## 🚀 Quick Start

### Option 1: GitHub Import (Easiest)

1. **Make sure you have a `.gitignore`:**
   ```bash
   # Check if .gitignore exists
   ls -la .gitignore
   ```

2. **Commit to Git:**
   ```bash
   git add .
   git commit -m "Export to Replit"
   ```

3. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/LupinBot.git
   git push -u origin main
   ```

4. **In Replit:**
   - Click "Import from GitHub"
   - Paste your repo URL
   - Done! ✅

### Option 2: Manual Upload

1. **Create `.gitignore`** (already created)
2. **Export files** to a ZIP (excluding sensitive files)
3. **Upload ZIP to Replit**
4. **Extract in Replit**
5. **Add secrets** in Replit's Secrets tab
6. **Run:** `python main.py`

## 📋 Pre-Export Checklist

### Files You MUST Export ✅

```
✅ main.py
✅ pyproject.toml
✅ database.py
✅ dashboard.py
✅ cache.py
✅ gemini.py
✅ start_dashboard.py
✅ cogs/*.py (all files in cogs folder)
✅ templates/dashboard.html
✅ REPLIT_DEPLOYMENT.md (this guide)
✅ .gitignore
```

### Files You MUST NOT Export ❌

```
❌ .env (contains secrets - add manually in Replit)
❌ database.db (will be created fresh)
❌ __pycache__/ (cache files)
❌ *.log (log files)
❌ .DS_Store (macOS files)
❌ replit.db (if exists)
```

## 🔐 Add Secrets in Replit

After importing, go to **Secrets** tab and add:

1. **DISCORD_TOKEN** - Your bot's token from Discord Developer Portal
2. **GEMINI_API_KEY** - (Optional) For Gemini AI features

## ⚙️ First Run

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # OR
   pip install discord.py python-dotenv aiohttp google-genai
   ```

2. **Run the bot:**
   ```bash
   python main.py
   ```

3. **Watch for:**
   - "Bot is ready!" message
   - Any error messages

## 🐛 Common Issues

### "Module not found"
```bash
pip install discord.py python-dotenv aiohttp
```

### "DISCORD_TOKEN not found"
- Check Secrets tab in Replit
- Ensure variable name is exactly: `DISCORD_TOKEN`

### "Database error"
- Bot will create `database.db` automatically
- No action needed

## 📚 Next Steps

1. ✅ Files exported
2. ✅ Secrets added
3. ✅ Bot running
4. 📖 Read `REPLIT_DEPLOYMENT.md` for full guide
5. 🎮 Invite bot to your server
6. 🧪 Test with `/help` command

## 🆘 Need Help?

- 📖 Full guide: `REPLIT_DEPLOYMENT.md`
- 🔧 Setup: `SETUP.md`
- 📊 Dashboard: `DASHBOARD_SETUP.md`
- 💬 Discord: Your server!

---

**Happy Deploying!** 🦊

