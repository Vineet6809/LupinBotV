import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import datetime
from database import Database
import logging
import aiohttp
import asyncio
import gemini

logger = logging.getLogger('LupinBot.streaks')

class Streaks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.code_pattern = re.compile(r'```[\s\S]*?```|`[^`]+`')
    
    def get_achievement_badge(self, streak: int) -> str:
        if streak >= 365:
            return "🏆 Legend"
        elif streak >= 100:
            return "💎 Master"
        elif streak >= 30:
            return "⭐ Champion"
        elif streak >= 7:
            return "🌟 Rising Star"
        else:
            return "🔰 Beginner"
    
    def detect_code(self, content: str) -> bool:
        if self.code_pattern.search(content):
            return True
        
        code_keywords = [
            'def ', 'class ', 'import ', 'function ', 'const ', 'let ', 'var ',
            'public ', 'private ', 'void ', 'int ', 'string ', 'return ',
            'if ', 'else ', 'for ', 'while ', 'try ', 'catch ', '#include'
        ]
        
        return any(keyword in content.lower() for keyword in code_keywords)
    
    async def has_media_or_code(self, message) -> bool:
        if self.code_pattern.search(message.content):
            return True
        
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                    mime_type = attachment.content_type
                                    has_code = await asyncio.to_thread(
                                        gemini.detect_code_in_image, 
                                        image_bytes, 
                                        mime_type
                                    )
                                    if has_code:
                                        logger.info(f'Image contains code (verified by Gemini): {attachment.filename}')
                                        return True
                                    else:
                                        logger.info(f'Image does not contain code (verified by Gemini): {attachment.filename}')
                    except Exception as e:
                        logger.error(f'Error analyzing image with Gemini: {e}')
                        return False
            return False
        
        return False
    
    def calculate_days_since_last_log(self, last_log_date: str) -> int:
        if not last_log_date:
            return 999
        try:
            last_date = datetime.strptime(last_log_date, "%Y-%m-%d")
            today = datetime.utcnow()
            delta = (today - last_date).days
            return delta
        except:
            return 999
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.reference:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        pattern = re.compile(r'#\s*day[\s-]*(\d+)', re.IGNORECASE)
        match = pattern.search(message.content)
        
        is_daily_code_channel = message.channel.name.lower() == "daily-code"
        has_content = await self.has_media_or_code(message)
        
        if self.db.has_logged_today(user_id, guild_id):
            if match or (is_daily_code_channel and has_content):
                today_day_number = self.db.get_todays_day_number(user_id, guild_id)
                await message.add_reaction('✅')
                if today_day_number:
                    embed = discord.Embed(
                        title="✅ Already Completed",
                        description=f"{message.author.mention}, you've already completed #DAY-{today_day_number} today! Come back tomorrow to continue your streak.",
                        color=discord.Color.green()
                    )
                    logger.info(f'User {message.author} tried to log again for Day {today_day_number}')
                else:
                    embed = discord.Embed(
                        title="✅ Already Completed",
                        description=f"{message.author.mention}, you've already completed your streak for today! Come back tomorrow to continue.",
                        color=discord.Color.green()
                    )
                    logger.warning(f'User {message.author} tried to log again but day number not found in database')
                await message.channel.send(embed=embed)
            return
        
        if not match and not (is_daily_code_channel and has_content):
            return
        
        streak_data = self.db.get_streak(user_id, guild_id)
        
        if match:
            day_number = int(match.group(1))
        else:
            if streak_data:
                _, _, last_log_date, last_day_number = streak_data
                days_since = self.calculate_days_since_last_log(last_log_date)
                day_number = last_day_number + 1
            else:
                day_number = 1
        
        if streak_data:
            current_streak, longest_streak, last_log_date, last_day_number = streak_data
            days_since = self.calculate_days_since_last_log(last_log_date)
            expected_day = last_day_number + 1
            
            if days_since >= 3:
                self.db.reset_streak(user_id, guild_id)
                await message.add_reaction('🔄')
                
                embed = discord.Embed(
                    title="🔄 Streak Reset",
                    description=f"{message.author.mention}, your streak has been reset after {days_since} days of inactivity.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Previous Streak",
                    value=f"{current_streak} days",
                    inline=True
                )
                embed.set_footer(text="Start fresh! Post #DAY-1 or share code in #daily-code to begin again.")
                await message.channel.send(embed=embed)
                
                logger.info(f'User {message.author} streak reset: {days_since} days inactive')
                return
            
            if days_since == 2 and (day_number == expected_day or not match):
                if not match:
                    day_number = expected_day
                
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
                self.db.update_streak(user_id, guild_id, current_streak, longest_streak, day_number)
                self.db.log_daily_entry(user_id, guild_id, day_number)
                
                await message.add_reaction('🧊')
                
                opt_out = self.db.get_user_setting(user_id, guild_id, 'opt_out_mentions')
                if not opt_out:
                    badge = self.get_achievement_badge(current_streak)
                    embed = discord.Embed(
                        title="🧊 Streak Frozen - Last Day Warning!",
                        description=f"{message.author.mention}, you made it just in time! Your streak was about to break.",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Current Streak", value=f"{current_streak} days", inline=True)
                    embed.add_field(name="Longest Streak", value=f"{longest_streak} days", inline=True)
                    embed.add_field(name="Achievement", value=badge, inline=True)
                    embed.add_field(name="⚠️ Grace Period Used", value="Don't miss tomorrow or your streak will reset!", inline=False)
                    embed.set_footer(text=f"Stay consistent! Next: Day {day_number + 1}")
                    await message.channel.send(embed=embed)
                
                logger.info(f'User {message.author} used grace period: Day {day_number} (Streak: {current_streak})')
            
            elif day_number == expected_day or (not match and days_since <= 1):
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
                
                if not match:
                    day_number = expected_day
                
                self.db.update_streak(user_id, guild_id, current_streak, longest_streak, day_number)
                self.db.log_daily_entry(user_id, guild_id, day_number)
                
                await message.add_reaction('🔥')
                
                opt_out = self.db.get_user_setting(user_id, guild_id, 'opt_out_mentions')
                if not opt_out:
                    badge = self.get_achievement_badge(current_streak)
                    embed = discord.Embed(
                        title=f"🔥 Streak Updated!",
                        description=f"{message.author.mention} is on fire!",
                        color=discord.Color.orange()
                    )
                    embed.add_field(name="Current Streak", value=f"{current_streak} days", inline=True)
                    embed.add_field(name="Longest Streak", value=f"{longest_streak} days", inline=True)
                    embed.add_field(name="Achievement", value=badge, inline=True)
                    embed.set_footer(text=f"Keep it up! Next: Day {day_number + 1}")
                    await message.channel.send(embed=embed)
                
                logger.info(f'User {message.author} continued streak: Day {day_number} (Streak: {current_streak})')
            else:
                self.db.reset_streak(user_id, guild_id)
                await message.add_reaction('🔄')
                
                embed = discord.Embed(
                    title="🔄 Streak Reset",
                    description=f"{message.author.mention}, your streak has been reset.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="⚠️ Day Mismatch",
                    value=f"Expected: Day {expected_day}\nYou posted: Day {day_number}",
                    inline=False
                )
                embed.add_field(
                    name="Previous Streak",
                    value=f"{current_streak} days",
                    inline=True
                )
                embed.set_footer(text="Start fresh! Post #DAY-1 to begin again.")
                await message.channel.send(embed=embed)
                
                logger.info(f'User {message.author} streak reset: Expected Day {expected_day}, got Day {day_number}')
        else:
            if day_number == 1 or not match:
                self.db.update_streak(user_id, guild_id, 1, 1, 1)
                self.db.log_daily_entry(user_id, guild_id, 1)
                await message.add_reaction('🔥')
                
                embed = discord.Embed(
                    title="🎉 Streak Started!",
                    description=f"{message.author.mention} started their coding journey!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Current Streak", value="1 day", inline=True)
                embed.add_field(name="Next Goal", value="7 days 🌟", inline=True)
                embed.set_footer(text="Keep coding every day to build your streak!")
                await message.channel.send(embed=embed)
                
                logger.info(f'User {message.author} started new streak: Day 1')
            else:
                await message.add_reaction('⚠️')
                embed = discord.Embed(
                    title="⚠️ Start with Day 1",
                    description=f"{message.author.mention}, please start your streak with #DAY-1",
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Begin your coding journey today!")
                await message.channel.send(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Show the top coding streaks in this server")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        leaderboard_data = self.db.get_leaderboard(guild_id, 10)
        
        if not leaderboard_data:
            await interaction.response.send_message("No streaks recorded yet! Start coding and post #DAY-1 to begin your journey!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Top Coding Streaks",
            description=f"Leading coders in {interaction.guild.name}",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, (user_id, current_streak, longest_streak, last_log_date) in enumerate(leaderboard_data[:10]):
            try:
                user = await self.bot.fetch_user(user_id)
                medal = medals[idx] if idx < 3 else f"{idx + 1}."
                badge = self.get_achievement_badge(current_streak)
                embed.add_field(
                    name=f"{medal} {user.name}",
                    value=f"🔥 Current: {current_streak} days\n💎 Best: {longest_streak} days\n{badge}",
                    inline=False
                )
            except:
                continue
        
        embed.set_footer(text="Keep coding to climb the leaderboard!")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="restore", description="Restore a user's streak (Admin only)")
    @app_commands.describe(user="The user whose streak to restore", day_number="The day number to restore to")
    async def restore(self, interaction: discord.Interaction, user: discord.Member, day_number: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        if day_number < 1:
            await interaction.response.send_message("❌ Day number must be at least 1.", ephemeral=True)
            return
        
        user_id = user.id
        guild_id = interaction.guild_id
        
        streak_data = self.db.get_streak(user_id, guild_id)
        
        if streak_data:
            _, longest_streak, _, _ = streak_data
            longest_streak = max(longest_streak, day_number)
        else:
            longest_streak = day_number
        
        self.db.update_streak(user_id, guild_id, day_number, longest_streak, day_number)
        
        embed = discord.Embed(
            title="✅ Streak Restored",
            description=f"Successfully restored {user.mention}'s streak",
            color=discord.Color.green()
        )
        embed.add_field(name="Restored to", value=f"Day {day_number}", inline=True)
        embed.add_field(name="Restored by", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'Admin {interaction.user} restored {user}\'s streak to Day {day_number}')
    
    @app_commands.command(name="mystats", description="View your personal coding statistics")
    async def mystats(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        streak_data = self.db.get_streak(user_id, guild_id)
        
        if not streak_data:
            await interaction.response.send_message("You haven't started tracking your streak yet! Post #DAY-1 to begin!", ephemeral=True)
            return
        
        current_streak, longest_streak, last_log_date, last_day_number = streak_data
        badge = self.get_achievement_badge(current_streak)
        
        embed = discord.Embed(
            title=f"📊 {interaction.user.name}'s Coding Stats",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🔥 Current Streak", value=f"{current_streak} days", inline=True)
        embed.add_field(name="💎 Longest Streak", value=f"{longest_streak} days", inline=True)
        embed.add_field(name="📅 Last Day", value=f"Day {last_day_number}", inline=True)
        embed.add_field(name="🏆 Achievement", value=badge, inline=False)
        
        if last_log_date:
            embed.add_field(name="📆 Last Log", value=last_log_date, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Streaks(bot))
