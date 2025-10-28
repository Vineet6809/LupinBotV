import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database
import logging
import sys

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
    """Setup dashboard integration with bot instance."""
    try:
        import dashboard
        dashboard.set_bot_instance(bot)
        logger.info('Dashboard integration enabled')
    except Exception as e:
        logger.debug(f'Dashboard integration not available: {e}')

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Setup dashboard integration
    setup_dashboard_integration()
    
    logger.info('Lupin Bot is ready!')

@bot.event
async def on_guild_join(guild):
    logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        embed = discord.Embed(
            title="🦊 Hey there! I'm Lupin",
            description="Your **AI-powered coding streak companion**! 🚀\n\nI help you build **consistent coding habits** with smart streak tracking, motivational features, and fun challenges designed specifically for developers!",
            color=discord.Color.blue()
        )
        
        # Getting Started Section
        embed.add_field(
            name="🎯 **How to Start Your Streak**",
            value="```\n1. Share any code in #daily-code\n2. Upload code files or screenshots\n3. Use #DAY-1, #DAY-2, etc. (optional)\n4. I'll detect and track automatically!\n```",
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
            name="🤖 **AI-Powered Detection**",
            value="✨ **Smart code detection** in messages\n📁 **File analysis** (20+ languages)\n🖼️ **Image recognition** for screenshots\n🔍 **Pattern matching** for day numbers",
            inline=False
        )
        
        # Quick Tips
        embed.add_field(
            name="💡 **Pro Tips**",
            value="• **No #DAY needed**: Just share code!\n• **File uploads**: `.py`, `.js`, `.java`, etc.\n• **Screenshots**: I can read code in images\n• **Flexible**: Works with any coding activity",
            inline=False
        )
        
        embed.set_footer(
            text="Ready to start your coding journey? Share some code now! 💻 | Use /help for complete guide"
        )
        embed.timestamp = discord.utils.utcnow()
        
        # Add a fun thumbnail or author icon
        embed.set_author(
            name="Lupin Bot",
            icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # You can replace with actual bot avatar
        )
        
        await message.channel.send(embed=embed)
        return  # Return early after handling mention
    
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    elif isinstance(error, commands.CommandNotFound):
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
        setup_dashboard_integration()  # Setup dashboard early
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error('DISCORD_TOKEN not found in environment variables')
            return
        await bot.start(token)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
