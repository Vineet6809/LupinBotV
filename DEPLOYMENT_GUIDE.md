# LupinBot Deployment Configuration

## Required Environment Variables

### Essential (Required for bot to function)
- `DISCORD_TOKEN` - Discord bot token (obtain from Discord Developer Portal)
- `GEMINI_API_KEY` - Google Gemini API key for AI-powered features

### Optional (Has defaults)
- `PORT` - Port for Flask dashboard (default: 5000)
- `DASHBOARD_PORT` - Alternative port specification for dashboard (default: uses PORT)
- `ALLOWED_ORIGINS` - CORS allowed origins for dashboard API (default: '*', set to specific domains in production)
- `REPL_ID` or `REPLIT` - Set automatically on Replit, triggers auto-start of dashboard

## Deployment Checklist

### Pre-Deployment
- [ ] Ensure DISCORD_TOKEN is set in environment
- [ ] Ensure GEMINI_API_KEY is set in environment
- [ ] Verify bot has proper permissions in Discord Developer Portal
- [ ] Configure ALLOWED_ORIGINS for production CORS policy
- [ ] Review Discord bot intents (message_content, members, guilds required)

### Database
- [x] Uses SQLite (file-based, no external DB needed)
- [x] Database file: `database.db` (auto-created on first run)
- [x] All migrations handled automatically by application

### Port Configuration
- [x] Dashboard uses environment variable PORT (no hardcoded ports)
- [x] Discord bot doesn't require specific port (connects to Discord Gateway)
- [x] Dashboard is optional and only starts on Replit environments

### External Dependencies
- [x] Discord API (discord.py library)
- [x] Google Gemini API (for AI features, gracefully falls back if unavailable)
- [x] Public APIs (meme API, quote API, joke API - optional, for fun commands)

### Health Checks
- [x] Dashboard `/health` endpoint available at `http://localhost:{PORT}/health`
- [x] Bot logs connection status to Discord Gateway
- [x] Automatic command sync on bot startup

## Running the Application

### Production (Automated via Supervisor)
The bot runs automatically via supervisor configuration at `/etc/supervisor/conf.d/discord_bot.conf`

```bash
# Check status
sudo supervisorctl status discord_bot

# Restart bot
sudo supervisorctl restart discord_bot

# View logs
tail -f /var/log/supervisor/discord_bot.out.log
tail -f /var/log/supervisor/discord_bot.err.log
```

### Manual Start (Development)
```bash
# Ensure .env file exists with required variables
python main.py
```

### Dashboard Only (Optional)
```bash
# Start dashboard separately
python start_dashboard.py
```

## Architecture Notes

This is a **Discord Bot Application**, not a traditional web application:
- Primary component: Discord bot (main.py)
- Secondary component: Flask dashboard (dashboard.py) - optional web interface
- The bot connects to Discord Gateway (no inbound port required for core functionality)
- Dashboard is for monitoring only and runs on configurable port

## Security Considerations

- ✅ No hardcoded secrets in code
- ✅ All sensitive data uses environment variables
- ⚠️ CORS policy set to '*' by default (configure ALLOWED_ORIGINS in production)
- ✅ Database is local SQLite (no network database credentials)
- ✅ Admin commands require Discord administrator permissions
- ✅ API keys loaded from environment only

## Troubleshooting

### Bot Not Connecting
1. Verify DISCORD_TOKEN is correct and valid
2. Check bot has required intents enabled in Discord Developer Portal
3. Review logs: `tail -f /var/log/supervisor/discord_bot.err.log`

### Commands Not Showing
1. Ensure bot is online and connected
2. Wait up to 1 hour for Discord's command cache to update
3. Manually sync: Use `/sync_commands` slash command (admin only)
4. Verify bot has proper OAuth2 scopes (applications.commands)

### Dashboard Not Accessible
1. Dashboard only auto-starts on Replit environments
2. Manually start: `python start_dashboard.py`
3. Check PORT environment variable
4. Verify Flask and flask-cors are installed

### Gemini AI Features Not Working
1. Verify GEMINI_API_KEY is set correctly
2. Check Gemini API quota and rate limits
3. Bot gracefully falls back to static content if Gemini unavailable
4. Review logs for specific Gemini API errors
