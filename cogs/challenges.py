import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
import logging
import random
from datetime import datetime, timezone

logger = logging.getLogger('LupinBot.challenges')

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self._weekly_sent_mem = set()  # (guild_id, yearweek)
        self.weekly_challenge.start()
        
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
        self.weekly_challenge.cancel()
    
    @tasks.loop(minutes=5)
    async def weekly_challenge(self):
        """Post a weekly challenge every Monday 09:00 UTC to the configured challenge channel."""
        now = datetime.utcnow()
        # Monday == 0
        if now.weekday() != 0:
            return
        if not (now.hour == 9 and 0 <= now.minute < 5):
            return
        
        isoyear, isoweek, _ = now.isocalendar()
        week_key = f"{isoyear}-W{isoweek:02d}"
        
        for guild in self.bot.guilds:
            try:
                # Avoid duplicate within process
                if (guild.id, week_key) in self._weekly_sent_mem:
                    continue
                
                # Avoid duplicate across restarts using DB meta
                last_week = self.db.get_last_week_sent(guild.id)
                if last_week == week_key:
                    continue
                
                settings = self.db.get_server_settings(guild.id)
                if not settings:
                    continue
                _, _, challenge_channel_id, _ = settings
                if not challenge_channel_id:
                    continue
                channel = guild.get_channel(challenge_channel_id)
                if not channel:
                    continue
                
                challenge = random.choice(self.challenge_pool)
                embed = discord.Embed(
                    title="💻 Weekly Coding Challenge",
                    description=challenge,
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Share your solution and help others! 🚀")
                await channel.send(embed=embed)
                
                # Mark sent
                self._weekly_sent_mem.add((guild.id, week_key))
                self.db.set_last_week_sent(guild.id, week_key)
                logger.info(f'Sent weekly challenge to {guild.name}')
            except Exception as e:
                logger.error(f'Error sending weekly challenge in guild {guild.id}: {e}')
    
    @weekly_challenge.before_loop
    async def before_weekly_challenge(self):
        await self.bot.wait_until_ready()
    
    @app_commands.command(name="challenge", description="Get a random coding challenge")
    async def challenge(self, interaction: discord.Interaction):
        challenge = random.choice(self.challenge_pool)
        
        embed = discord.Embed(
            title="💻 Coding Challenge",
            description=challenge,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Good luck! Share your solution when done 🚀")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} requested a coding challenge')

async def setup(bot):
    await bot.add_cog(Challenges(bot))
