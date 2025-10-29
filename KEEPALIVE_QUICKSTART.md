# 🚀 Quick Keep-Alive Setup - 5 Minutes

## ✅ Step 1: Verify Bot is Running (30 seconds)

```bash
# In Replit shell:
python main.py
```

**Look for these messages:**
```
🦊 Running on Replit!
📊 Dashboard started in background on http://0.0.0.0:8080
💡 To keep bot alive 24/7, setup UptimeRobot to ping your Replit URL
```

## ✅ Step 2: Get Your Repl URL (30 seconds)

**Find your URL:**
- Format: `https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co`
- Check Replit's "Webview" tab for exact URL
- Or run: `echo "https://$REPL_SLUG.$REPL_OWNER.repl.co"`

**Test endpoints:**
- Open: `https://your-repl-url.repl.co/health`
- Should see: `{"status": "ok", "bot_connected": true, ...}`

## ✅ Step 3: Setup UptimeRobot (3 minutes)

1. **Go to:** https://uptimerobot.com/
2. **Sign up** for free account (30 seconds)
3. **Verify email** (30 seconds)
4. **Click** "+ Add New Monitor" (10 seconds)
5. **Fill in:**
   ```
   Monitor Type: HTTP(s)
   Friendly Name: LupinBot
   URL: https://YOUR_REPL.USERNAME.repl.co/health
   Monitoring Interval: 5 minutes
   ```
6. **Click** "Create Monitor" (10 seconds)

## ✅ Step 4: Verify (1 minute)

```bash
# In Replit shell:
python verify_keepalive.py
```

**Expected output:**
```
✅ Running on Replit
✅ DISCORD_TOKEN is set
✅ Health Check is responding
✅ All systems operational!
```

## 🎉 Done!

Your bot will now stay online 24/7!

---

## 🔗 Quick Links

- **Full Guide:** `KEEPALIVE_SETUP.md`
- **UptimeRobot:** https://uptimerobot.com/
- **Deployment Guide:** `REPLIT_DEPLOYMENT.md`
- **Bot Docs:** `README.md`

---

## 🆘 Troubleshooting

**Bot still offline?**
- Check UptimeRobot monitor shows "Up" (green)
- Verify URL in UptimeRobot is correct
- Wait 5-10 minutes for first ping
- Check bot logs for errors

**Health endpoint not working?**
```bash
pip install flask flask-cors
# Restart bot
python main.py
```

**Need more help?**
- Read `KEEPALIVE_SETUP.md` for detailed instructions
- Check Replit console logs
- Verify DISCORD_TOKEN is set

---

## ⚡ That's It!

Total time: **5 minutes**
Cost: **$0 (completely free)**
Result: **Bot stays online 24/7** 🎉
