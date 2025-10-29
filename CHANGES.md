# LupinBot – Changes Implemented (October 2025)

This document summarizes all changes made to the repository, grouped by feature and file.

## Summary
- **NEW**: AI Q&A Assistant - Ask Lupin questions by tagging with text, code files, or images
- Fixed daily reminders to trigger reliably per IST for each guild
- Added `/checkreminder` command to troubleshoot reminder configuration
- Enhanced reminder setup commands with better warnings and feedback
- Added IST-aware weekly challenges generated from last 7 days of daily-code activity using Gemini
- Implemented startup backfill to prevent streak mismatches when the bot was offline
- Added explicit daily-code channel configuration
- Made the Flask dashboard Replit-ready and safe; added health endpoint
- Fixed several runtime and logic issues (cache TTL, moderation clear, bugfixes)

---

## Latest Features (October 29, 2025)

### 1) AI Q&A Assistant 🤖
- Tag @Lupin with any question to get AI-powered help
- Supports text questions, code files (20+ languages), and images
- Powered by Google Gemini AI (gemini-2.5-flash)
- Examples:
  - `@Lupin explain recursion`
  - `@Lupin [attach code.py] review this code`
  - `@Lupin [attach error.png] what's this error?`

Files:
- `gemini.py` - Added `answer_question()` function
- `main.py` - Enhanced `on_message` handler to detect questions and process attachments
- `AI_QA_FEATURE.md` - Complete documentation for the feature

### 2) Reminder Troubleshooting
- Added `/checkreminder` command to check reminder configuration
- Enhanced `/setreminder` to warn if channel not configured
- Enhanced `/setreminderchannel` to show complete setup status
- Improved logging in reminder task for better debugging
- Fixed issue where reminders wouldn't send if channel not configured

Files:
- `cogs/utilities.py` - Added `/checkreminder`, enhanced setup commands
- `cogs/streaks.py` - Improved logging and error handling in reminder task
- `README.md` - Added reminder troubleshooting section
- `REMINDER_FIX_SUMMARY.md` - Complete guide for reminder issues
- `check_reminders.py` - Test script to verify reminder configuration

---

## New Admin Slash Commands
- `/checkreminder` (new)
  - Check current reminder configuration and troubleshoot issues
- `/setweeklychallenge day:<dropdown> time_ist_12:<HH:MM AM/PM> channel:<optional>`
  - Configure weekly challenge day (IST) and time (12-hour format). Optional output channel.
- `/setchallengechannel <#channel>`
  - Set (or override) output channel for weekly challenges.
- `/setdailycodechannel <#channel>`
  - Explicitly set daily-code activity channel used for detection, weekly challenge generation, and backfill.
- `/setreminder "HH:MM AM/PM"` (enhanced)
  - Set daily reminder time in IST; stored as UTC internally. Now warns if channel not set.
- `/setreminderchannel <#channel>` (enhanced)
  - Set channel for daily reminders. Now shows complete status when both settings configured.
- `/sync_commands` (existing)
  - Manually sync slash commands with Discord.

---

## Feature Changes

### 1) Weekly Challenges (IST + Gemini-driven)
- Added a minute-based scheduler that checks each guild’s configured IST day/time and posts a weekly challenge.
- Challenge is generated using last 7 days of daily-code history (messages and attachment filenames) via Gemini.
- Dedupe per ISO week using `bot_meta.last_week_sent` to avoid duplicate posts.
- Admin can route the weekly challenge to a custom channel or fallback to the reminder channel.

Files:
- `cogs/challenges.py` – rewritten
- `gemini.py` – added `generate_challenge_from_history(...)`
- `database.py` – auxiliary tables/helpers used by the flow

### 2) Daily Reminders (IST-based, reliable)
- Fixed reminder loop to convert stored UTC time to IST on the fly and trigger at the correct minute per guild.
- Labeled time as IST in reminder embed.

Files:
- `cogs/streaks.py`
- `cogs/utilities.py` (existing `/setreminder` uses IST input, stored as UTC)

### 3) Startup Backfill + Users Cache
- On bot ready, backfills daily-code messages since last processed ID (or last seen / last 7 days fallback) to:
  - Avoid mismatches when bot was offline
  - Pair day-number and code posts similarly to runtime logic
  - Log historical `daily_logs` records for past days without altering current streaks
- Populates `users` table for dashboard (username/display_name/avatar) so UI works offline.

Files:
- `main.py`
- `database.py`

### 4) Daily-Code Channel Configuration
- New `/setdailycodechannel` slash command for admins to explicitly select the activity channel.
- Backfill and weekly challenge generator prefer this configured channel and fallback to channel names containing `daily-code`.

Files:
- `cogs/utilities.py`
- `database.py`
- `main.py`
- `cogs/streaks.py`
- `cogs/challenges.py`

### 5) Dashboard (Replit-ready)
- Dashboard starts in the background on Replit at `0.0.0.0:PORT` (or `5000`).
- Added `/health` endpoint for uptime pings.
- All endpoints are DB-backed (no Discord calls in request context) – safe when bot gateway is disconnected.

Files:
- `dashboard.py`
- `main.py` (background start logic)

### 6) Reliability and Bugfixes
- `cache.py`: Implemented per-entry TTL
- `cogs/moderation.py`: `clear` now respects Discord’s 14-day bulk delete restrictions and deletes older messages individually
- `cogs/streaks.py`: fixed unreachable return, fixed `use_freeze` messaging and values, improved detection and daily-code channel logic
- `pyproject.toml`: added `pytz` dependency

---

## Database Additions
- `users` – cache for dashboard display of username/display_name/avatar
- `bot_meta` – `last_seen_at`, `last_week_sent`
- `bot_channel_state` – `last_processed_id` per (guild, channel) for incremental backfill
- `daily_code_settings` – configured daily-code channel per guild
- `challenge_settings` – stored in `cogs/challenges.py` (weekday, time_ist, output_channel_id)

---

## Commands Reference (Admin)
- `/setdailycodechannel #daily-code`
- `/setreminder "09:30 PM"`
- `/setreminderchannel #reminders`
- `/setweeklychallenge day:Sunday time_ist_12:"09:00 AM" channel:#announcements`
- `/setchallengechannel #announcements`
- `/sync_commands`

User:
- `/challenge` – generate a challenge immediately (based on last 7 days)
- `/mystats`, `/leaderboard`, `/streak_calendar`, `/streaks_history`

---

## Deployment (Replit)
1) Add Secrets:
   - `DISCORD_TOKEN` (regenerate; never commit)
   - `GEMINI_API_KEY`
2) Run: `python main.py`
3) Keep alive: ping `GET /health` periodically
4) After the bot is online, run `/sync_commands` in your server once

---

## Security & Notes
- Please regenerate your Discord bot token if it was previously exposed
- All times shown in messages are labeled as IST; dashboard can be extended to show IST times if desired

---

## Modified Files List
- `pyproject.toml`
- `cache.py`
- `cogs/moderation.py`
- `cogs/streaks.py`
- `cogs/challenges.py`
- `cogs/utilities.py`
- `database.py`
- `main.py`
- `dashboard.py`
- `gemini.py`

If you want a Git-style diff or a more granular per-line change log, let me know.
