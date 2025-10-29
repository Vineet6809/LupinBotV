import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
import logging
import random
from datetime import datetime, date

logger = logging.getLogger('LupinBot.challenges')

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        # Track sends to avoid duplicates
        self._reminder_sent = {}  # guild_id -> YYYY-MM-DD
        self._weekly_sent = set()  # (guild_id, ISOYEAR, ISOWEEK)
        self.daily_reminder.start()
        self.weekly_summary.start()
        
        self.challenge_pool = [
            "Build a simple calculator in your favorite language",
            "Create a function that reverses a string without using built-in methods",
            "Implement a binary search algorithm",
            "Write a program to check if a number is prime",
            "Create a to-do list CLI application",
            "Build a simple URL shortener",
            "Implement a basic hash table",
            "Write a function to find the longest word in a sentence",
            "Create a program that converts between different number bases",
            "Build a simple encryption/decryption tool",
            "Implement the bubble sort algorithm",
            "Create a palindrome checker",
            "Write a function to generate Fibonacci numbers",
            "Build a simple password generator",
            "Implement a stack data structure",
            "Create a function to find duplicates in an array",
            "Write a program to validate email addresses with regex",
            "Build a simple quiz game",
            "Implement a queue data structure",
            "Create a function to merge two sorted arrays"
        ]
    
    def cog_unload(self):
        self.daily_reminder.cancel()
        self.weekly_summary.cancel()
    
    @tasks.loop(minutes=1)
    async def daily_reminder(self):
        try:
            now = datetime.utcnow()
            today_str = now.strftime('%Y-%m-%d')
            
            for guild in self.bot.guilds:
                settings = self.db.get_server_settings(guild.id)
                
                if settings:
                    _, reminder_time, _, reminder_channel_id = settings
                    if not reminder_time:
                        continue
                    
                    if now.strftime('%H:%M') == reminder_time:
                        last_sent = self._reminder_sent.get(guild.id)
                        if last_sent == today_str:
                            continue  # Already sent today
                        
                        if reminder_channel_id:
                            channel = guild.get_channel(reminder_channel_id)
                            if channel:
                                embed = discord.Embed(
                                    title="⏰ Daily Coding Reminder",
                                    description="Don't forget to log your coding progress today!",
                                    color=discord.Color.blue()
                                )
                                embed.add_field(
                                    name="How to log your streak",
                                    value="Post a message with `#DAY-n` (where n is your day number) to track your streak!",
                                    inline=False
                                )
                                embed.set_footer(text="Keep coding, keep growing! 🚀")
                                
                                await channel.send(embed=embed)
                                self._reminder_sent[guild.id] = today_str
                                logger.info(f'Sent daily reminder to {guild.name}')
        except Exception as e:
            logger.error(f'Error in daily reminder: {e}')
    
    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(minutes=5)
    async def weekly_summary(self):
        try:
            now = datetime.utcnow()
            isoyear, isoweek, _ = now.isocalendar()
            week_key = (isoyear, isoweek)
            
            if now.weekday() == 6:  # Sunday
                for guild in self.bot.guilds:
                    if (guild.id, *week_key) in self._weekly_sent:
                        continue
                    
                    leaderboard_data = self.db.get_leaderboard(guild.id, 3)
                    if leaderboard_data:
                        settings = self.db.get_server_settings(guild.id)
                        if settings:
                            _, _, _, reminder_channel_id = settings
                            if reminder_channel_id:
                                channel = guild.get_channel(reminder_channel_id)
                                if channel:
                                    embed = discord.Embed(
                                        title="🏆 Weekly Streak Summary",
                                        description=f"Top 3 coders in {guild.name} this week!",
                                        color=discord.Color.gold()
                                    )
                                    
                                    medals = ["🥇", "🥈", "🥉"]
                                    
                                    for idx, (user_id, current_streak, longest_streak, _) in enumerate(leaderboard_data):
                                        try:
                                            user = await self.bot.fetch_user(user_id)
                                            embed.add_field(
                                                name=f"{medals[idx]} {user.name}",
                                                value=f"Current: {current_streak} days | Best: {longest_streak} days",
                                                inline=False
                                            )
                                        except Exception:
                                            continue
                                    
                                    embed.set_footer(text="Keep up the great work! 💪")
                                    
                                    await channel.send(embed=embed)
                                    self._weekly_sent.add((guild.id, *week_key))
                                    logger.info(f'Sent weekly summary to {guild.name}')
        except Exception as e:
            logger.error(f'Error in weekly summary: {e}')
    
    @weekly_summary.before_loop
    async def before_weekly_summary(self):
        await self.bot.wait_until_ready()
    
    @app_commands.command(name="challenge", description="Get a random coding challenge")
    async def challenge(self, interaction: discord.Interaction):
        challenge = random.choice(self.challenge_pool)
        
        embed = discord.Embed(
            title="💻 Daily Coding Challenge",
            description=challenge,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Good luck! Share your solution when done 🚀")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} requested a coding challenge')

async def setup(bot):
    await bot.add_cog(Challenges(bot))
