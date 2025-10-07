import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from database import Database
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'),
              logging.StreamHandler()])
logger = logging.getLogger('LupinBot')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
db = Database()


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')

    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

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
            title="👋 Hello! I'm Lupin",
            description=
            "I'm here to help your coding community track streaks and stay motivated!",
            color=discord.Color.blue())
        embed.add_field(
            name="🔥 Streak Tracking",
            value=
            "Post `#DAY-1`, `#DAY-2` .... or post the screenshot of your code in `#daily-code` chanel to track your daily coding progress!",
            inline=False)
        embed.add_field(
            name="📊 Commands",
            value=
            "Use `/leaderboard` to see top streaks\nUse `/stats` for server statistics\nUse `/help` to see all commands",
            inline=False)
        embed.set_footer(text="Let's code together! 💻")
        await message.channel.send(embed=embed)

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
    cogs = [
        'cogs.streaks', 'cogs.fun', 'cogs.moderation', 'cogs.utilities',
        'cogs.challenges'
    ]
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
    import asyncio
    asyncio.run(main())
