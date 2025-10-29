# LupinBot - Discord Coding Streak Tracker

A multi-purpose Discord bot for coding communities that tracks daily coding streaks and provides fun commands.

## 🚀 Features

### Core Features
- **📅 Daily Streak Tracking** - Track your coding progress with `#DAY-n` posts
- **🤖 AI Code Detection** - Automatically detects code in images using Google Gemini
- **💬 AI Q&A Assistant** - Ask Lupin questions by tagging it with your query
- **🏆 Achievement System** - Earn badges as you reach milestones
- **📊 Leaderboards** - Compete with others on your server
- **🧊 Grace Period** - 2-day buffer before streak resets
- **⏰ Daily Reminders** - Automated notifications to keep you motivated
- **📈 Weekly Summaries** - Top performers get featured

### AI Q&A Feature
Tag Lupin with your question to get AI-powered help:
- **Ask anything**: `@Lupin explain this code`
- **With code files**: Upload `.py`, `.js`, `.java` files and ask about them
- **With images**: Share screenshots and ask Lupin to analyze them
- **Debug help**: `@Lupin why is this giving an error?`
- **Explanations**: `@Lupin what does this function do?`

Examples:
```
@Lupin explain what recursion is
@Lupin [attach code file] can you review this?
@Lupin [attach screenshot] what's wrong with this code?
```

### New Commands
- `/serverstats` - View server-wide coding statistics
- `/streaks_history` - View your personal streak history (last 30 days)
- `/checkreminder` - Check if daily reminders are properly configured (troubleshooting)

### Fun Commands
- `/meme` - Get programming memes
- `/quote` - Inspirational quotes
- `/joke` - Programming jokes
- `/challenge` - Random coding challenges

### Web Dashboard
- Real-time statistics
- Interactive charts
- Live leaderboards
- Auto-refresh functionality
- Guild dropdown selector

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- Discord Bot Token
- (Optional) Google Gemini API Key for image code detection

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LupinBotV
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # Or with uv:
   uv pip install -r requirements.txt
   ```

3. **Create `.env` file**
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Get Discord Bot Token**
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to "Bot" section and copy the token
   - Enable "Message Content Intent" in Privileged Gateway Intents

5. **Invite Bot to Server**
   - In OAuth2 > URL Generator, select "bot" scope
   - Select permissions: Send Messages, Read Messages, Manage Messages, Add Reactions
   - Copy and visit the generated URL

## 🎮 Running

### Start the Bot
```bash
python main.py
```

### Start the Web Dashboard
```bash
python dashboard.py
```
Then open: http://localhost:5000

### Running Both
Open two terminals:
- Terminal 1: `python main.py`
- Terminal 2: `python dashboard.py`

## 🎯 Usage

### Tracking Streaks
Post a message with:
- `#DAY-1`, `#DAY-2`, etc. - Track daily progress
- Or share code images/snippets in designated channels

### Available Commands
See all commands with: `/help`

### Dashboard
1. Go to http://localhost:5000
2. Select a guild from the dropdown
3. View real-time statistics and leaderboards

## 🛠️ Troubleshooting

### Bot won't start
- Check that `.env` file exists with `DISCORD_TOKEN`
- Verify token is valid

### Commands not working
- Make sure bot has proper permissions
- Check that "Message Content Intent" is enabled

### Dashboard not loading
- Ensure Flask is installed: `pip install flask`
- Check that dashboard.py is running
- Verify database exists (`database.db`)

### Reminders not working
- **Most common issue**: Reminder channel not set
- Run `/checkreminder` to see current configuration
- Make sure both are configured:
  1. `/setreminder time:"HH:MM AM/PM"` (e.g., "09:30 PM" in IST)
  2. `/setreminderchannel channel:#your-channel`
- Verify bot has permissions to send messages in the reminder channel
- See `REMINDER_FIX_SUMMARY.md` for detailed troubleshooting

## 📊 Technologies Used

- **Discord.py** - Discord API wrapper
- **Flask** - Web dashboard framework
- **Chart.js** - Data visualization
- **SQLite** - Database
- **Google Gemini AI** - Image code detection
- **AsyncIO** - Asynchronous operations
- **AioSQLite** - Async database operations

## 🏗️ Project Structure

```
LupinBotV/
├── cogs/
│   ├── streaks.py      # Core streak tracking
│   ├── fun.py           # Fun commands
│   ├── moderation.py    # Admin commands
│   ├── utilities.py      # Utility commands
│   └── challenges.py    # Challenge system
├── main.py              # Bot entry point
├── dashboard.py         # Web dashboard
├── database.py          # Database operations
├── database_async.py    # Async database
├── gemini.py            # AI integration
├── cache.py             # Caching system
└── templates/
    └── dashboard.html   # Dashboard UI
```

## 🔧 Recent Improvements

- ✅ Caching system for API calls
- ✅ HTTP connection pooling
- ✅ Async database support
- ✅ New `/serverstats` and `/streaks_history` commands
- ✅ Web dashboard with real-time stats
- ✅ Better error handling
- ✅ Input validation
- ✅ Fixed timedelta import bug

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

