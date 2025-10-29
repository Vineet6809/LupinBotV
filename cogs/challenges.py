import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
import logging
import random
from datetime import datetime, timedelta
import pytz
import re
from typing import Optional
import gemini

logger = logging.getLogger('LupinBot.challenges')

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
DAY_TO_INDEX = {name: idx for idx, name in enumerate(DAYS)}  # Monday=0

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.weekly_challenge_loop.start()
        
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
        self.weekly_challenge_loop.cancel()

    def _get_ist_now(self):
        return datetime.now(pytz.timezone('Asia/Kolkata'))

    def _guild_weekday_target(self, guild_id: int) -> int:
        # default Sunday (index 6), but we use Monday=0 convention
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS challenge_settings (
                guild_id INTEGER PRIMARY KEY,
                weekday TEXT DEFAULT 'Sunday',
                time_ist TEXT DEFAULT '09:00',
                output_channel_id INTEGER
            )
        """)
        conn.commit()
        cur.execute("SELECT weekday FROM challenge_settings WHERE guild_id = ?", (guild_id,))
        row = cur.fetchone()
        conn.close()
        day_name = (row[0] if row and row[0] else 'Sunday')
        return DAY_TO_INDEX.get(day_name, 6)

    def _guild_challenge_time_ist(self, guild_id: int) -> str:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT time_ist FROM challenge_settings WHERE guild_id = ?", (guild_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row and row[0] else '09:00'

    def _guild_challenge_channel(self, guild_id: int) -> Optional[int]:
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT output_channel_id FROM challenge_settings WHERE guild_id = ?", (guild_id,))
        row = cur.fetchone()
        conn.close()
        return int(row[0]) if row and row[0] else None

    def _set_challenge_settings(self, guild_id: int, weekday: Optional[str] = None, time_ist: Optional[str] = None, channel_id: Optional[int] = None):
        conn = self.db.get_connection()
        cur = conn.cursor()
        # Ensure row exists
        cur.execute("INSERT OR IGNORE INTO challenge_settings (guild_id) VALUES (?)", (guild_id,))
        if weekday is not None:
            cur.execute("UPDATE challenge_settings SET weekday = ? WHERE guild_id = ?", (weekday, guild_id))
        if time_ist is not None:
            cur.execute("UPDATE challenge_settings SET time_ist = ? WHERE guild_id = ?", (time_ist, guild_id))
        if channel_id is not None:
            cur.execute("UPDATE challenge_settings SET output_channel_id = ? WHERE guild_id = ?", (channel_id, guild_id))
        conn.commit()
        conn.close()

    async def _collect_last7_history_snippets(self, guild: discord.Guild) -> list[str]:
        """Collect minimal snippets from daily-code channel over last 7 days to seed Gemini challenge."""
        ist = pytz.timezone('Asia/Kolkata')
        cutoff_utc = (self._get_ist_now() - timedelta(days=7)).astimezone(pytz.utc)
        snippets: list[str] = []
        
        for channel in guild.text_channels:
            if 'daily-code' not in channel.name.lower():
                continue
            try:
                async for msg in channel.history(limit=1000, after=cutoff_utc, oldest_first=True):
                    text = (msg.content or '').strip()
                    # Keep it concise
                    if text:
                        if len(text) > 300:
                            text = text[:300]
                        snippets.append(text)
                    # Pull small code sections from attachments' filenames
                    for a in msg.attachments:
                        if a.filename:
                            snippets.append(f"file:{a.filename}")
                    if len(snippets) >= 50:
                        break
            except Exception:
                continue
        return snippets

    async def _post_weekly_challenge_if_due(self, guild: discord.Guild):
        ist_now = self._get_ist_now()
        target_weekday = self._guild_weekday_target(guild.id)  # Monday=0
        time_ist = self._guild_challenge_time_ist(guild.id)  # 'HH:MM'
        try:
            hour, minute = map(int, time_ist.split(':'))
        except Exception:
            hour, minute = 9, 0

        if ist_now.weekday() != target_weekday:
            return
        if not (ist_now.hour == hour and ist_now.minute == minute):
            return

        # Avoid duplicate within week using DB flag
        week_key = ist_now.strftime('%G-W%V')
        last_week = self.db.get_last_week_sent(guild.id)
        if last_week == week_key:
            return

        output_channel_id = self._guild_challenge_channel(guild.id)
        if not output_channel_id:
            # fallback to reminder_channel if unset
            settings = self.db.get_server_settings(guild.id)
            if settings:
                _, _, _, reminder_channel_id = settings
                output_channel_id = reminder_channel_id
        if not output_channel_id:
            return

        channel = guild.get_channel(output_channel_id)
        if not channel:
            return

        # Build challenge from last 7 days
        try:
            snippets = await self._collect_last7_history_snippets(guild)
            challenge_text = gemini.generate_challenge_from_history(snippets, guild.name, channel.name)
        except Exception:
            challenge_text = random.choice(self.challenge_pool)

        embed = discord.Embed(
            title="💻 Weekly Coding Challenge",
            description=challenge_text,
            color=discord.Color.purple()
        )
        embed.set_footer(text="This challenge was generated based on recent activity in #daily-code (IST timezone)")
        await channel.send(embed=embed)
        self.db.set_last_week_sent(guild.id, week_key)
        logger.info(f'Sent weekly challenge to {guild.name}')

    @tasks.loop(minutes=1)
    async def weekly_challenge_loop(self):
        for guild in self.bot.guilds:
            try:
                await self._post_weekly_challenge_if_due(guild)
            except Exception as e:
                logger.error(f'Weekly challenge loop error in guild {guild.id}: {e}')

    @weekly_challenge_loop.before_loop
    async def before_weekly(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="setweeklychallenge", description="Admin: Configure weekly challenge day/time (IST) and output channel")
    @app_commands.describe(day="Day of week", time_ist="Time in HH:MM (24h) IST", channel="Channel to post weekly challenge (optional)")
    async def setweeklychallenge(self, interaction: discord.Interaction, day: str, time_ist: str, channel: Optional[discord.TextChannel] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        day_norm = day.strip().capitalize()
        if day_norm not in DAYS:
            await interaction.response.send_message("❌ Invalid day. Choose one of: " + ", ".join(DAYS), ephemeral=True)
            return
        if not re.match(r'^([01]?\d|2[0-3]):([0-5]\d)$', time_ist):
            await interaction.response.send_message("❌ Invalid time. Use 24h HH:MM format (IST)", ephemeral=True)
            return
        channel_id = channel.id if channel else None
        self._set_challenge_settings(interaction.guild_id, weekday=day_norm, time_ist=time_ist, channel_id=channel_id)
        msg = f"Weekly challenge scheduled: **{day_norm} {time_ist} IST**"
        if channel:
            msg += f" in {channel.mention}"
        await interaction.response.send_message(msg)

    @app_commands.command(name="challenge", description="Get a random coding challenge (inspired by last 7 days)")
    async def challenge(self, interaction: discord.Interaction):
        # Prefer Gemini-based challenge using history
        try:
            snippets = await self._collect_last7_history_snippets(interaction.guild)
            challenge_text = gemini.generate_challenge_from_history(snippets, interaction.guild.name, interaction.channel.name)
        except Exception:
            challenge_text = random.choice(self.challenge_pool)
        
        embed = discord.Embed(
            title="💻 Coding Challenge",
            description=challenge_text,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Inspired by recent #daily-code activity (IST timezone)")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setchallengechannel", description="Admin: Set the default output channel for weekly challenges")
    async def setchallengechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        self._set_challenge_settings(interaction.guild_id, channel_id=channel.id)
        await interaction.response.send_message(f"✅ Weekly challenges will be posted in {channel.mention}")

async def setup(bot):
    await bot.add_cog(Challenges(bot))
