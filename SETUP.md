# LupinBot Setup Guide

## Prerequisites

- Python 3.11 or higher
- Discord Bot Token
- (Optional) Google Gemini API Key for image code detection

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   # Or if using uv
   uv pip install -r requirements.txt
   ```

2. **Create `.env` file**
   Create a `.env` file in the root directory with:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Get a Discord Bot Token**
   - Go to https://discord.com/developers/applications
   - Create a new application or select existing one
   - Go to "Bot" section
   - Copy the token (you'll need to click "Reset Token" if you don't have one)
   - Paste it in your `.env` file as `DISCORD_TOKEN`

4. **Invite Bot to Server**
   - In Discord Developer Portal, go to "OAuth2" > "URL Generator"
   - Select "bot" scope
   - Select permissions: "Send Messages", "Read Messages", "Manage Messages", "Add Reactions"
   - Copy and open the generated URL to invite the bot

## Running the Bot

```bash
python main.py
```

The bot will:
- Load all cogs (streaks, fun, moderation, utilities, challenges)
- Connect to Discord
- Start listening for commands and messages

## New Features

### New Commands Added:
- `/serverstats` - View server-wide coding statistics
- `/streaks_history` - View your personal streak history (last 30 days)

### Improvements:
- ✅ Caching for API calls (memes, quotes, jokes)
- ✅ HTTP connection pooling
- ✅ Better error handling
- ✅ Input validation for security
- ✅ Async database support ready
- ✅ Improved logging

## Troubleshooting

**"DISCORD_TOKEN not found"**
- Make sure you have a `.env` file in the root directory
- Check that `DISCORD_TOKEN=your_token_here` is in the file
- Restart the bot after adding the token

**"No module named 'google'"**
- Run: `pip install google-genai`

**"No module named 'aiosqlite'"**
- Run: `pip install aiosqlite`

## Bot Permissions Needed

- Send Messages
- Read Messages
- Manage Messages
- Add Reactions
- Use Slash Commands
- Attach Files (for image code detection)

## Environment Variables

- `DISCORD_TOKEN` (Required) - Your Discord bot token
- `GEMINI_API_KEY` (Optional) - For image code detection feature

