import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database
import logging
import sys
import threading
from threading import Thread
import asyncio
import re
from datetime import datetime, timezone, timedelta

# Replit detection
IS_REPLIT = os.path.exists('/home/runner')
if IS_REPLIT:
    print('🦊 Running on Replit!')

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LupinBot')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()

# Setup dashboard integration if running in same process
def setup_dashboard_integration():
    """Setup dashboard integration with bot instance and optionally start server on Replit."""
    try:
        import dashboard
        dashboard.set_bot_instance(bot)
        logger.info('Dashboard integration enabled')

        # On Replit, start dashboard server in background thread on the primary port
        if IS_REPLIT:
            def run_dash():
                try:
                    # Use port 8080 for Replit's public webview
                    port = int(os.environ.get('PORT', '8080'))
                    dashboard.run_dashboard(host='0.0.0.0', port=port, debug=False)
                except Exception as e:
                    logger.error(f'Dashboard error: {e}')
            
            # Start the dashboard in a daemon thread
            dashboard_thread = Thread(target=run_dash, daemon=True)
            dashboard_thread.start()
            logger.info(f'📊 Dashboard started in background on http://0.0.0.0:{os.environ.get("PORT", "8080")}')
            
    except Exception as e:
        logger.debug(f'Dashboard integration not available: {e}')

def _iter_daily_code_channels(guild: discord.Guild):
    """Yield channels to process: configured daily-code channel if set, otherwise channels containing 'daily-code'."""
    configured_id = db.get_daily_code_channel(guild.id)
    if configured_id:
        ch = guild.get_channel(configured_id)
        if ch and isinstance(ch, discord.TextChannel):
            yield ch
            return
    for ch in guild.text_channels:
        if 'daily-code' in ch.name.lower():
            yield ch

async def backfill_guild_history(guild: discord.Guild):
    """On startup: populate users from daily-code history and process missed messages since last seen/processed."""
    # Determine window
    last_seen_str = db.get_last_seen(guild.id)
    last_seen_dt = None
    if last_seen_str:
        try:
            last_seen_dt = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            last_seen_dt = None
    # Fallback window if no state: last 7 days
    fallback_after = datetime.utcnow() - timedelta(days=7)

    streaks_cog = bot.get_cog('Streaks')
    if not streaks_cog:
        logger.warning('Streaks cog not loaded; skipping backfill')
        return

    processed_any = False

    for channel in _iter_daily_code_channels(guild):
        try:
            last_processed_id = db.get_last_processed(guild.id, channel.id)
            messages = []
            if last_processed_id:
                after_obj = discord.Object(id=last_processed_id)
                async for msg in channel.history(limit=None, after=after_obj, oldest_first=True):
                    messages.append(msg)
            else:
                # Use last_seen_dt if available; else fallback window
                after_dt = last_seen_dt if last_seen_dt else fallback_after
                async for msg in channel.history(limit=None, after=after_dt, oldest_first=True):
                    messages.append(msg)

            # Process messages oldest->newest
            pending_day: dict[int, tuple[int, discord.Message]] = {}
            pending_code: dict[int, discord.Message] = {}
            last_id = last_processed_id

            for msg in messages:
                # Track user info in DB for dashboard
                try:
                    db.upsert_user(
                        msg.author.id,
                        getattr(msg.author, 'name', None),
                        getattr(msg.author, 'display_name', None),
                        str(msg.author.display_avatar.url) if msg.author and msg.author.display_avatar else None
                    )
                except Exception:
                    pass

                # Extract data
                day_match = re.search(r'#\s*day[\s-]*(\d+)', msg.content or '', re.IGNORECASE)
                day_num = int(day_match.group(1)) if day_match else None
                has_code = await streaks_cog.has_media_or_code(msg)
                msg_date = msg.created_at.date()
                today_date = datetime.utcnow().date()

                if day_num is not None and has_code:
                    # Process normally if today
                    if msg_date == today_date:
                        await streaks_cog.process_streak_message(msg, day_num)
                    else:
                        # Record historical log without changing streak counts
                        db.log_specific_day(msg.author.id, guild.id, msg_date.strftime('%Y-%m-%d'), day_num)
                elif day_num is not None and not has_code:
                    # Remember day for user
                    pending_day[msg.author.id] = (day_num, msg)
                    # If we already saw code for this user, pair
                    if msg.author.id in pending_code:
                        code_msg = pending_code.pop(msg.author.id)
                        if msg_date == today_date:
                            await streaks_cog.process_streak_message(code_msg, day_num)
                        else:
                            db.log_specific_day(code_msg.author.id, guild.id, code_msg.created_at.strftime('%Y-%m-%d'), day_num)
                        pending_day.pop(msg.author.id, None)
                elif has_code and day_num is None:
                    # Remember code
                    pending_code[msg.author.id] = msg
                    if msg.author.id in pending_day:
                        dn, day_msg = pending_day.pop(msg.author.id)
                        if msg_date == today_date:
                            await streaks_cog.process_streak_message(msg, dn)
                        else:
                            db.log_specific_day(msg.author.id, guild.id, msg_date.strftime('%Y-%m-%d'), dn)
                        pending_code.pop(msg.author.id, None)
                # update last id
                last_id = msg.id
                processed_any = True

            if last_id:
                db.set_last_processed(guild.id, channel.id, last_id)
        except Exception as e:
            logger.error(f'Backfill error in guild {guild.id} channel {channel.id}: {e}')
            continue

    # Update last seen
    now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    db.set_last_seen(guild.id, now_str)
    if processed_any:
        logger.info(f'Backfill completed for guild {guild.name}')
    else:
        logger.info(f'No new messages to backfill for guild {guild.name}')

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Setup dashboard integration and start dashboard (if Replit)
    setup_dashboard_integration()

    # Backfill for each guild
    for guild in bot.guilds:
        try:
            await backfill_guild_history(guild)
        except Exception as e:
            logger.error(f'Failed backfill for guild {guild.id}: {e}')
    
    logger.info('Lupin Bot is ready!')

@bot.event
async def on_guild_join(guild):
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # Extract the message content without the bot mention
        content = message.content
        for mention in message.mentions:
            if mention.id == bot.user.id:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
        content = content.strip()
        
        # If there's additional content (a question/request), use AI to respond
        if content:
            try:
                # Show typing indicator
                async with message.channel.typing():
                    import gemini
                    import aiohttp
                    
                    # Process attachments
                    attachments_data = []
                    image_data = []
                    
                    for attachment in message.attachments:
                        # Check if it's a code file
                        code_extensions = [
                            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php',
                            '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
                            '.html', '.css', '.scss', '.sass', '.less', '.xml',
                            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
                            '.sql', '.sh', '.bash', '.ps1', '.bat', '.cmd',
                            '.md', '.txt', '.log', '.conf', '.config'
                        ]
                        
                        if any(attachment.filename.lower().endswith(ext) for ext in code_extensions):
                            # Download and read text file
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(attachment.url) as resp:
                                        if resp.status == 200:
                                            file_content = await resp.text()
                                            attachments_data.append({
                                                'filename': attachment.filename,
                                                'content': file_content,
                                                'mime_type': attachment.content_type or 'text/plain'
                                            })
                            except Exception as e:
                                logger.error(f"Failed to download attachment {attachment.filename}: {e}")
                        
                        # Check if it's an image
                        elif attachment.content_type and attachment.content_type.startswith('image/'):
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(attachment.url) as resp:
                                        if resp.status == 200:
                                            image_bytes = await resp.read()
                                            image_data.append({
                                                'data': image_bytes,
                                                'mime_type': attachment.content_type
                                            })
                            except Exception as e:
                                logger.error(f"Failed to download image {attachment.filename}: {e}")
                    
                    # Get AI response
                    answer = await gemini.answer_question(content, attachments_data, image_data)
                    
                    # Send response as a reply
                    embed = discord.Embed(
                        title="🤖 Lupin AI Assistant",
                        description=answer,
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text=f"Asked by {message.author.name}")
                    
                    await message.reply(embed=embed, mention_author=False)
                    logger.info(f"Answered question from {message.author} in {message.guild.name}")
                    return
                    
            except Exception as e:
                logger.error(f"Error answering question: {e}")
                await message.reply("❌ Sorry, I encountered an error while processing your question. Please try again!")
                return
        
        # If no additional content, show introduction embed
        embed = discord.Embed(
            title="🦊 Hey there! I'm Lupin",
            description="Your **AI-powered coding streak companion**! 🚀\n\nI help you build **consistent coding habits** with smart streak tracking, motivational features, and fun challenges designed specifically for developers!",
            color=discord.Color.blue()
        )
        
        # Getting Started Section
        embed.add_field(
            name="🎯 **How to Start Your Streak**",
            value="""
1. Share any code in #daily-code
2. Upload code files or screenshots
3. Use #DAY-1, #DAY-2, etc. (optional)
4. I'll detect and track automatically!
""",
            inline=False
        )
        
        # Core Features
        embed.add_field(
            name="🔥 **Core Features**",
            value="`/mystats` - Your progress & achievements\n`/streak_calendar` - Visual streak calendar\n`/leaderboard` - Server rankings\n`/streaks_history` - Your streak timeline",
            inline=True
        )
        
        # Protection & Fun
        embed.add_field(
            name="🛡️ **Streak Protection**",
            value="`/use_freeze` - Protect your streak\n`/restore` - Restore lost streaks\n❄️ **Grace period**: 2-day buffer\n🏆 **Achievements**: Unlock badges!",
            inline=True
        )
        
        # Fun & Motivation
        embed.add_field(
            name="🎮 **Fun & Motivation**",
            value="`/challenge` - Random coding challenges\n`/meme` - Programming memes\n`/quote` - Inspirational quotes\n`/joke` - Developer jokes",
            inline=True
        )
        
        # AI Features
        embed.add_field(
            name="🤖 **AI-Powered Features**",
            value="✨ **Smart code detection** in messages\n📁 **File analysis** (20+ languages)\n🖼️ **Image recognition** for screenshots\n💬 **Ask me questions**: @Lupin explain this code",
            inline=False
        )
        
        # Quick Tips
        embed.add_field(
            name="💡 **Pro Tips**",
            value="• **No #DAY needed**: Just share code!\n• **File uploads**: `.py`, `.js`, `.java`, etc.\n• **Screenshots**: I can read code in images\n• **Ask me anything**: Tag me with a question!",
            inline=False
        )
        
        embed.set_footer(
            text="Ready to start your coding journey? Share some code now! 💻 | Use /help for complete guide"
        )
        embed.timestamp = discord.utils.utcnow()
        
        # Add a fun thumbnail or author icon
        embed.set_author(
            name="Lupin Bot",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"
        )
        
        await message.channel.send(embed=embed)
        return
    
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    from discord.ext import commands as _commands
    if isinstance(error, _commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, _commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, _commands.CommandNotFound):
        pass
    else:
        logger.error(f'Error: {error}', exc_info=True)
        await ctx.send("❌ An error occurred while processing the command.")

async def load_cogs():
    cogs = ['cogs.streaks', 'cogs.fun', 'cogs.moderation', 'cogs.utilities', 'cogs.challenges']
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'Loaded {cog}')
        except Exception as e:
            logger.error(f'Failed to load {cog}: {e}')

async def main():
    async with bot:
        await load_cogs()
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error('DISCORD_TOKEN not found in environment variables')
            return
        await bot.start(token)

if __name__ == '__main__':
    # The setup_dashboard_integration function is called in on_ready,
    # which is the correct place to start it after the bot is initialized.
    # No keep-alive thread is needed here as the dashboard serves that purpose.
    asyncio.run(main())