"""
Backfill database from daily-code channel history
"""
import discord
from discord.ext import commands
import os
import asyncio
from database import Database
from datetime import datetime
import re
import logging

logger = logging.getLogger('backfill')
logging.basicConfig(level=logging.DEBUG)

db = Database()

# Load bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Pattern to detect code blocks
code_pattern = re.compile(r'```[\s\S]*?```|`[^`]+`')

def detect_code_in_message(content: str) -> bool:
    """Detect if message contains code."""
    if not content:
        return False
        
    # Check for code blocks first
    if code_pattern.search(content):
        return True
    
    # Check for day patterns (if it mentions a day, it's likely a coding entry)
    day_patterns = [
        r'#\s*day[\s-]*\d+',
        r'day\s*\d+',
        r'#day\d+',
        r'day-\d+',
        r'coding',
        r'programming',
        r'challenge'
    ]
    
    for pattern in day_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    # Check for code keywords
    code_keywords = [
        'def ', 'class ', 'import ', 'function ', 'const ', 'let ', 'var ',
        'public ', 'private ', 'void ', 'int ', 'string ', 'return ',
        'if ', 'else ', 'for ', 'while ', 'try ', 'catch ', '#include',
        'console.log', 'print(', 'System.out', 'printf', 'cout',
        'function(', '=>', 'async', 'await', 'promise'
    ]
    return any(keyword in content.lower() for keyword in code_keywords)

def extract_day_number(content: str) -> int:
    """Extract day number from message (#DAY-n format)."""
    # Try multiple patterns
    patterns = [
        r'#\s*day[\s-]*(\d+)',  # #DAY-17, #DAY 17, etc.
        r'day\s*(\d+)',         # day 17
        r'#day(\d+)',          # #day17
        r'day-(\d+)',          # day-17
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None

async def backfill_channel(guild_id: int, channel_name: str = 'daily-code'):
    """Backfill database from a specific channel's history."""
    logger.info(f"Starting backfill for guild {guild_id}, channel {channel_name}")
    
    # Find the channel
    for guild in bot.guilds:
        if guild.id == guild_id:
            logger.info(f"Found guild: {guild.name}")
            for channel in guild.text_channels:
                if channel_name.lower() in channel.name.lower():
                    logger.info(f"Found channel: {channel.name}")
                    
                    # Track processed messages
                    processed = 0
                    skipped = 0
                    
                    # Store only Lupin bot messages first, then process chronologically
                    messages = []
                    async for message in channel.history(limit=None):  # Read all messages
                        # Only process messages from Lupin bot that contain streak information
                        if (message.author.bot and 
                            message.author.name == 'Lupin' and 
                            message.embeds and 
                            any('streak' in embed.title.lower() or 'day' in embed.title.lower() 
                                for embed in message.embeds if embed.title)):
                            messages.append(message)
                    
                    # Sort messages by date (oldest first)
                    messages.sort(key=lambda m: m.created_at)
                    
                    # Track user streaks chronologically
                    user_streaks = {}  # user_id -> {'current': int, 'longest': int, 'last_date': date, 'last_day': int}
                    
                    for message in messages:
                        # Extract streak information from Lupin bot embeds
                        if not message.embeds:
                            skipped += 1
                            continue
                            
                        embed = message.embeds[0]  # Take first embed
                        
                        # Extract user ID from embed description or fields
                        user_id = None
                        current_streak = 0
                        longest_streak = 0
                        day_number = 1
                        
                        # Look for user mention in description
                        if embed.description:
                            user_mention = re.search(r'<@(\d+)>', embed.description)
                            if user_mention:
                                user_id = int(user_mention.group(1))
                        
                        # Extract streak information from fields
                        for field in embed.fields:
                            if 'current' in field.name.lower() and 'streak' in field.name.lower():
                                # Extract number from "X days" or "X day"
                                streak_match = re.search(r'(\d+)', field.value)
                                if streak_match:
                                    current_streak = int(streak_match.group(1))
                            elif 'longest' in field.name.lower() and 'streak' in field.name.lower():
                                # Extract number from "X days" or "X day"
                                streak_match = re.search(r'(\d+)', field.value)
                                if streak_match:
                                    longest_streak = int(streak_match.group(1))
                            elif 'next' in field.name.lower() and 'day' in field.name.lower():
                                # Extract day number from "Day X"
                                day_match = re.search(r'day\s*(\d+)', field.value, re.IGNORECASE)
                                if day_match:
                                    day_number = int(day_match.group(1))
                        
                        # Skip if no user ID found
                        if not user_id:
                            skipped += 1
                            logger.debug(f"Skipped (no user ID): {embed.title}")
                            continue
                        
                        # Get the date of the message
                        message_date = message.created_at.date()
                        
                        # Initialize user streak tracking if not exists
                        if user_id not in user_streaks:
                            user_streaks[user_id] = {
                                'current': 0,
                                'longest': 0,
                                'last_date': None,
                                'last_day': 0
                            }
                        
                        # Use the extracted streak values from the embed
                        streak_info = user_streaks[user_id]
                        
                        # Update with the latest streak information from the bot
                        streak_info['current'] = current_streak
                        streak_info['longest'] = max(streak_info['longest'], longest_streak)
                        streak_info['last_date'] = message_date
                        streak_info['last_day'] = day_number
                        
                        logger.info(f"Processed: User {user_id} - Day {day_number} ({message_date}) - Current: {current_streak}, Longest: {longest_streak}")
                        processed += 1
                    
                    # Now update the database with calculated streaks
                    for user_id, streak_info in user_streaks.items():
                        if streak_info['current'] > 0:  # Only update if user has entries
                            # Get or create streak record
                            existing_streak = db.get_streak(user_id, guild_id)
                            if existing_streak:
                                # Update existing streak
                                db.update_streak(user_id, guild_id, streak_info['current'], streak_info['longest'], streak_info['last_day'])
                            else:
                                # Create new streak
                                db.update_streak(user_id, guild_id, streak_info['current'], streak_info['longest'], streak_info['last_day'])
                            
                            logger.info(f"Updated {user_id}: Current={streak_info['current']}, Longest={streak_info['longest']}, Last Day={streak_info['last_day']}")
                    
                    logger.info(f"Backfill complete! Processed: {processed}, Skipped: {skipped}")
                    return
                    
    logger.warning(f"Could not find guild {guild_id} or channel '{channel_name}'")

async def main():
    """Main function."""
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error('DISCORD_TOKEN not found')
        return
    
    @bot.event
    async def on_ready():
        logger.info(f'{bot.user} is ready!')
        
        # Get guild ID from environment or user input
        # For now, use the guild ID from database
        guild_id = 1422243427122151485  # Your guild ID
        
        # Run backfill
        await backfill_channel(guild_id, 'daily-code')
        
        # Close bot
        await bot.close()
    
    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())

