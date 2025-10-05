# Lupin Discord Bot

## Overview

Lupin is a multi-purpose Discord bot designed for coding communities. It tracks daily coding streaks by monitoring messages containing `#DAY-n` patterns, provides entertainment commands (memes, quotes, jokes), utility features (server stats, polls, coding challenges), and moderation tools. The bot uses SQLite for data persistence and is built with discord.py using a cog-based architecture for modular feature organization.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Structure

**Modular Cog System**: The bot uses discord.py's cog system to separate features into distinct modules (`streaks.py`, `fun.py`, `utilities.py`, `moderation.py`, `challenges.py`). This design enables independent development and testing of features, cleaner code organization, and easier maintenance. Each cog is self-contained with its own commands and event listeners.

**Command Interface**: The bot implements both traditional prefix commands (`!command`) and modern Discord slash commands (application commands) via the `app_commands` module. This dual approach provides flexibility for users while transitioning to Discord's recommended slash command system.

**Event-Driven Architecture**: The bot relies heavily on Discord event listeners, particularly `on_message` for streak detection and automated responses. This allows real-time processing of user activity without polling.

### Data Persistence

**SQLite Database**: A lightweight, file-based SQLite database stores all persistent data. This choice eliminates the need for external database servers while providing sufficient performance for a Discord bot's typical workload.

**Database Schema Design**:
- `streaks` table: Tracks per-user, per-guild streak data with current/longest streak counts and last log date
- `server_settings` table: Stores guild-specific configurations (prefix, reminder times, channel IDs)
- `user_settings` table: Manages individual user preferences (opt-out status, custom reminder times)

**Database Access Pattern**: A `Database` class provides connection management and initialization. Each cog instantiates its own database instance for isolated data access, following a simple data access pattern without an ORM.

### Core Features

**Streak Tracking System**: Uses regex pattern matching to detect `#DAY-n` messages. The system validates day number sequences, detects code content (via code blocks or programming keywords), and automatically reacts with emojis (🔥 for continuation, 🔄 for reset). Streak data is stored per-user per-guild to support multi-server deployments.

**Scheduled Tasks**: Implements `discord.ext.tasks` loops for automated reminders and weekly summaries. The daily reminder system checks guild-specific settings and user preferences before sending notifications, respecting opt-out flags and custom times.

**Permission-Based Access Control**: Moderation commands verify Discord permissions (`kick_members`, `ban_members`) and role hierarchy to ensure proper authorization. This prevents privilege escalation and unauthorized actions.

**Achievement System**: Streak milestones trigger badge awards (🔰 Beginner, 🌟 Rising Star, ⭐ Champion, 💎 Master, 🏆 Legend) based on streak length, gamifying the coding practice experience.

### External API Integration

**External Services**: The bot integrates with third-party APIs for content delivery:
- Reddit meme API (`meme-api.com`) for programming memes
- Quotable API for inspirational quotes
- Error handling with timeouts and fallback messages for resilient operation

**Challenge Pool System**: Daily coding challenges are stored in-memory as a predefined list, randomly selected and posted to configured channels. This design allows easy updates without database queries.

### Logging and Monitoring

**Structured Logging**: Uses Python's `logging` module with both file (`bot.log`) and console handlers. Each cog has its own logger namespace (`LupinBot.{cog_name}`) for granular log filtering and debugging.

### Configuration Management

**Environment-Based Secrets**: Bot token and sensitive data are loaded from `.env` files using `python-dotenv`, keeping credentials out of source control.

**Per-Guild Customization**: Server-specific settings (command prefix, reminder times, designated channels) are stored in the database, allowing the bot to serve multiple Discord servers with different configurations simultaneously.

## External Dependencies

### Discord Integration
- **discord.py**: Primary library for Discord API interaction, event handling, and command processing
- **Discord Intents**: Requires `message_content`, `members`, and `guilds` intents for full functionality

### Data Storage
- **SQLite3**: Built-in Python database for persistent storage of streaks, settings, and configurations

### External APIs
- **meme-api.com**: Provides programming memes from Reddit's r/ProgrammerHumor
- **api.quotable.io**: Delivers inspirational and technology-related quotes
- **requests**: HTTP client library for API communication

### Development Tools
- **python-dotenv**: Environment variable management for secure credential storage
- **logging**: Built-in Python logging for monitoring and debugging

### Runtime Requirements
- **Python 3.10+**: Minimum Python version for modern async/await syntax and type hints
- **File System Access**: Required for SQLite database and log file storage