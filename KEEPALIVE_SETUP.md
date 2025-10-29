# Keep-Alive Setup for LupinBot on Replit

## 🎯 Overview

This guide helps you keep your LupinBot running 24/7 on Replit by implementing a proper keep-alive mechanism.

## ⚠️ The Problem

Replit's free tier puts inactive Repls to sleep after ~1 hour of no HTTP activity. This causes your Discord bot to go offline.

## ✅ The Solution

Use an external monitoring service to "ping" your Replit every 5 minutes, keeping it awake.

---

## 🔧 Step 1: Verify Your Bot's Web Server

Your bot now has an automatic keep-alive web server running on Replit!

### Check if it's working:

1. **Find your Repl URL:**
   - Format: `https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co`
   - Example: `https://lupinbot.johndoe.repl.co`

2. **Test the endpoints:**
   - Main page: `https://your-repl-url.repl.co/`
   - Health check: `https://your-repl-url.repl.co/health`
   - Ping: `https://your-repl-url.repl.co/ping`

3. **Expected response:**
   ```json
   {
     "status": "ok",
     "bot_connected": true,
     "guilds": 3
   }
   ```

---

## 🤖 Step 2: Setup UptimeRobot (FREE - Recommended)

UptimeRobot will ping your bot every 5 minutes to keep it alive.

### Create Free Account:

1. **Go to:** [https://uptimerobot.com/](https://uptimerobot.com/)
2. **Sign up** for a free account
3. **Verify** your email

### Add Monitor:

1. **Click** "+ Add New Monitor"

2. **Configure:**
   ```
   Monitor Type: HTTP(s)
   Friendly Name: LupinBot Keep-Alive
   URL: https://YOUR_REPL_NAME.YOUR_USERNAME.repl.co/health
   Monitoring Interval: 5 minutes
   ```

3. **Example:**
   ```
   Monitor Type: HTTP(s)
   Friendly Name: LupinBot
   URL: https://lupinbot.johndoe.repl.co/health
   Monitoring Interval: 5 minutes
   ```

4. **Click** "Create Monitor"

### Verify:

- Monitor should show **Up** status in green
- Check logs to see pings coming through
- Your bot should stay online 24/7 now!

---

## 🌐 Step 3: Alternative Services (Optional)

If UptimeRobot doesn't work for you, try these alternatives:

### Option A: Freshping
- URL: [https://www.freshworks.com/website-monitoring/](https://www.freshworks.com/website-monitoring/)
- Free tier: 50 checks
- Interval: 1 minute

### Option B: StatusCake
- URL: [https://www.statuscake.com/](https://www.statuscake.com/)
- Free tier: Unlimited checks
- Interval: 5 minutes

### Option C: Uptime.com
- URL: [https://uptime.com/](https://uptime.com/)
- Free tier: 10 checks
- Interval: 5 minutes

### Option D: Pingdom (Paid)
- URL: [https://www.pingdom.com/](https://www.pingdom.com/)
- More features but requires payment

---

## 🔍 Step 4: Verify Bot is Staying Alive

### Check Bot Status:

1. **In Discord:**
   - Bot should show as "Online" (green dot)
   - Test with `/help` command
   - Check if bot responds

2. **In Replit Console:**
   - Look for regular logs
   - Should see ping requests every 5 minutes
   - No "disconnected" messages

3. **In Replit Webview:**
   - Open webview in Replit
   - Should see dashboard or keep-alive page
   - Health endpoint should return `{"status": "ok"}`

### Monitor Logs:

```bash
# In Replit shell, check recent logs:
tail -f bot.log
```

You should see:
```
INFO - 🦊 Running on Replit!
INFO - 📊 Dashboard started in background on http://0.0.0.0:8080
INFO - 💡 To keep bot alive 24/7, setup UptimeRobot to ping your Replit URL
INFO - Lupin Bot is ready!
```

---

## 🐛 Troubleshooting

### Issue 1: Bot still going offline

**Solution:**
- Check UptimeRobot monitor is active and "Up"
- Verify URL in UptimeRobot matches your Repl URL exactly
- Ensure monitor interval is set to 5 minutes
- Check Replit logs for errors

### Issue 2: Web server not responding

**Solution:**
```bash
# Check if Flask is installed
pip install flask flask-cors

# Restart the Repl
# Click "Stop" then "Run" in Replit
```

### Issue 3: Wrong Repl URL

**Solution:**
```bash
# Find your correct URL:
echo "https://$REPL_SLUG.$REPL_OWNER.repl.co"

# Or check Replit's webview tab for the URL
```

### Issue 4: Port issues

**Solution:**
- Replit automatically sets PORT environment variable
- Bot uses port 8080 by default
- Don't change port settings
- Replit handles external routing automatically

### Issue 5: Dashboard not loading

**Solution:**
- Keep-alive fallback server will start automatically
- Main goal is keeping bot alive, not dashboard
- Dashboard is bonus feature
- As long as /health responds, you're good

---

## 📊 How It Works

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│ UptimeRobot │────────▶│ Replit Web   │────────▶│  LupinBot   │
│  (Pings     │  HTTP   │  Server      │  Keeps  │  (Stays     │
│  every 5m)  │  GET    │  (/health)   │  Alive  │  Online)    │
└─────────────┘         └──────────────┘         └─────────────┘
```

1. **UptimeRobot** sends HTTP GET request every 5 minutes
2. **Web Server** (Flask) responds with status
3. **Replit** sees activity and keeps Repl running
4. **Discord Bot** stays connected 24/7

---

## 🎉 Success Checklist

- [ ] Bot runs and shows "Running on Replit" message
- [ ] Dashboard/keep-alive server is accessible at Repl URL
- [ ] `/health` endpoint returns `{"status": "ok"}`
- [ ] UptimeRobot monitor is created and showing "Up"
- [ ] Bot stays online for 24+ hours
- [ ] Bot responds to Discord commands consistently
- [ ] No disconnection errors in logs

---

## 💡 Pro Tips

1. **Multiple Monitors:** Create 2-3 monitors pinging different endpoints for redundancy
   - `/health`
   - `/ping`
   - `/` (root)

2. **Alert Setup:** Configure UptimeRobot to email you if bot goes down

3. **Status Page:** UptimeRobot offers free public status pages

4. **Backup Plan:** If UptimeRobot fails, switch to alternative service quickly

5. **Monitor Dashboard:** Check UptimeRobot dashboard weekly to ensure pings are working

6. **Replit Always On:** Consider Replit's paid "Always On" feature for mission-critical bots

---

## 🔗 Quick Links

- **UptimeRobot:** https://uptimerobot.com/
- **Replit Docs:** https://docs.replit.com/
- **Discord.py Docs:** https://discordpy.readthedocs.io/
- **LupinBot Docs:** See `README.md`

---

## 📞 Need Help?

1. Check `REPLIT_DEPLOYMENT.md` for Replit-specific issues
2. Check `README.md` for bot functionality
3. Check Replit console logs for errors
4. Verify environment variables are set

---

## 🎯 Final Notes

- **Free Solution:** UptimeRobot free tier is sufficient for keeping bot alive
- **No Code Changes Needed:** Keep-alive is built into the bot now
- **Set and Forget:** Once UptimeRobot is configured, it runs automatically
- **Reliable:** This method has been tested and works consistently

**Your bot should now stay online 24/7 on Replit!** 🎉

---

## 📝 What Changed

The bot now includes:
- ✅ Automatic web server on Replit
- ✅ `/health` endpoint for monitoring
- ✅ `/ping` endpoint for simple checks
- ✅ Fallback keep-alive if dashboard fails
- ✅ Proper logging for debugging
- ✅ Environment-aware configuration

All you need to do is setup UptimeRobot to ping your Repl URL!
