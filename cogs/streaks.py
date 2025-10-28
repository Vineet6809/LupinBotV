import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import datetime, timedelta
from database import Database
import logging
import aiohttp
import asyncio
import gemini
from collections import deque

logger = logging.getLogger('LupinBot.streaks')

class Streaks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.user_message_cache = {}  # Cache for messages

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

    def detect_code_heuristically(self, content: str) -> bool:
        """
        Detects code in a message using a language-agnostic heuristic scoring model.
        This serves as a fallback if the AI detection fails.
        """
        if not content:
            return False

        score = 0
        
        # 1. Code Block Formatter (Highest Weight)
        if re.search(r'```[\s\S]*?```|`[^`]+`', content):
            score += 5

        # 2. Symbol-to-Word Ratio
        words = content.split()
        symbols = len(re.findall(r'[(){}\[\]=<>!&|;:,+\-*%/]', content))
        if len(words) > 0:
            ratio = symbols / len(words)
            if ratio > 0.1:
                score += 2
            if ratio > 0.2:
                score += 1

        # 3. Indentation and Multiple Lines
        lines = content.split('\n')
        if len(lines) > 2:
            score += 1
            # Check for consistent indentation (spaces or tabs)
            indentations = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
            if len(set(indentations)) > 1:
                score += 1

        # 4. CamelCase or snake_case
        if re.search(r'\b[a-z]+(?:[A-Z][a-z]*)+\b', content) or re.search(r'\b[a-z]+(?:_[a-z]+)+\b', content):
            score += 1
            
        # 5. Line Length Variance
        line_lengths = [len(line) for line in lines]
        if line_lengths and max(line_lengths) > 40 and min(line_lengths) < 20:
            score +=1

        return score >= 3

    async def detect_code(self, content: str) -> bool:
        """
        Detects code in a message using a hybrid approach: AI-first with a heuristic fallback.
        """
        if not content:
            return False

        try:
            # AI-powered detection
            is_code = await asyncio.to_thread(gemini.detect_code_in_text, content)
            if is_code:
                logger.info("Code detected by Gemini AI.")
                return True
        except Exception as e:
            logger.error(f"Gemini AI detection failed: {e}. Using heuristic fallback.")
            # Fallback to heuristic model
            if self.detect_code_heuristically(content):
                logger.info("Code detected by heuristic fallback.")
                return True
        
        return False

    async def has_media_or_code(self, message) -> bool:
        """Enhanced detection for code content including files, images, and raw text."""
        # 1. Check message content with the hybrid detector
        if await self.detect_code(message.content):
            return True
        
        # 2. Check attachments (files and images)
        if message.attachments:
            for attachment in message.attachments:
                # Check for common code file extensions
                if attachment.filename:
                    code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r', '.html', '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.sql', '.sh', '.bash', '.ps1', '.bat', '.cmd', '.md', '.txt', '.log', '.conf', '.config']
                    if any(attachment.filename.lower().endswith(ext) for ext in code_extensions):
                        logger.info(f'Code file detected: {attachment.filename}')
                        return True
                
                # Analyze images with Gemini AI
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()
                                    mime_type = attachment.content_type
                                    has_code = await asyncio.to_thread(gemini.detect_code_in_image, image_bytes, mime_type)
                                    if has_code:
                                        logger.info(f'Image contains code (verified by Gemini): {attachment.filename}')
                                        return True
                                    else:
                                        logger.info(f'Image does not contain code (verified by Gemini): {attachment.filename}')
                    except Exception as e:
                        logger.error(f'Error analyzing image with Gemini: {e}')
                        # Assume it has code to be safe on error
                        logger.info(f'Assuming image contains code due to Gemini error: {attachment.filename}')
                        return True
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
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f'Error calculating days since last log: {e}')
            return 999

    async def process_streak_message(self, message, day_number):
        user_id = message.author.id
        guild_id = message.guild.id

        if self.db.has_logged_today(user_id, guild_id):
            today_day_number = self.db.get_todays_day_number(user_id, guild_id)
            embed = discord.Embed(
                title="✅ Already Completed",
                description=f"{message.author.mention}, you've already completed #DAY-{today_day_number} today! Come back tomorrow to continue your streak.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
            return

        streak_data = self.db.get_streak(user_id, guild_id)

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
                embed.add_field(name="Previous Streak", value=f"{current_streak} days", inline=True)
                embed.set_footer(text="Start fresh! Post #DAY-1 or share code in #daily-code to begin again.")
                await message.channel.send(embed=embed)
                return

            if day_number is not None and day_number != expected_day:
                embed = discord.Embed(
                    title="⚠️ Day Number Corrected",
                    description=f"{message.author.mention}, you posted Day {day_number}, but your streak is on Day {expected_day}. I've corrected it for you.",
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
            
            day_number = expected_day
            
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
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
        else:
            if day_number is not None and day_number != 1:
                await message.add_reaction('⚠️')
                embed = discord.Embed(
                    title="⚠️ Start with Day 1",
                    description=f"{message.author.mention}, please start your streak with #DAY-1",
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Begin your coding journey today!")
                await message.channel.send(embed=embed)
                return
            
            day_number = 1
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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.reference:
            return

        user_id = message.author.id
        cache_key = (user_id, message.channel.id)
        
        day_match = re.search(r'#\s*day[\s-]*(\d+)', message.content, re.IGNORECASE)
        day_number = int(day_match.group(1)) if day_match else None
        has_code = await self.has_media_or_code(message)

        if day_number is not None and not has_code:
            # Look for code in recent messages
            if cache_key in self.user_message_cache:
                for prev_message_id in self.user_message_cache[cache_key]:
                    try:
                        prev_message = await message.channel.fetch_message(prev_message_id)
                        if await self.has_media_or_code(prev_message):
                            await self.process_streak_message(prev_message, day_number)
                            self.user_message_cache[cache_key].clear()
                            return
                    except discord.NotFound:
                        continue # Message was deleted
            # If no code found, cache the day number message
            if cache_key not in self.user_message_cache:
                self.user_message_cache[cache_key] = deque(maxlen=5)
            self.user_message_cache[cache_key].append(message.id)

        elif has_code and day_number is None:
            # Look for a day number in recent messages
            if cache_key in self.user_message_cache:
                for prev_message_id in self.user_message_cache[cache_key]:
                    try:
                        prev_message = await message.channel.fetch_message(prev_message_id)
                        prev_day_match = re.search(r'#\s*day[\s-]*(\d+)', prev_message.content, re.IGNORECASE)
                        if prev_day_match:
                            prev_day_number = int(prev_day_match.group(1))
                            await self.process_streak_message(message, prev_day_number)
                            self.user_message_cache[cache_key].clear()
                            return
                    except discord.NotFound:
                        continue # Message was deleted
            # If no day number found, cache the code message
            if cache_key not in self.user_message_cache:
                self.user_message_cache[cache_key] = deque(maxlen=5)
            self.user_message_cache[cache_key].append(message.id)

        elif has_code and day_number is not None:
            await self.process_streak_message(message, day_number)
        
        # Daily code channel logic
        elif "daily-code" in message.channel.name and has_code:
             await self.process_streak_message(message, None)
    
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
        
        if day_number < 1 or day_number > 10000:
            await interaction.response.send_message("❌ Day number must be between 1 and 10000.", ephemeral=True)
            return
        
        try:
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
        except Exception as e:
            logger.error(f'Error restoring streak: {e}')
            await interaction.response.send_message(f"❌ An error occurred while restoring the streak: {str(e)}", ephemeral=True)
    
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
    
    @app_commands.command(name="streaks_history", description="View your recent streak history (last 30 days)")
    async def streaks_history(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        history = self.db.get_streak_history(user_id, guild_id, limit=30)
        
        if not history:
            await interaction.followup.send("You haven't logged any streaks yet! Post some code to begin!", ephemeral=True)
            return
        
        weeks_data = {}
        for log_date, day_number in history:
            try:
                date_obj = datetime.strptime(log_date, "%Y-%m-%d")
                week_start = date_obj - timedelta(days=date_obj.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                
                if week_key not in weeks_data:
                    weeks_data[week_key] = []
                weeks_data[week_key].append((log_date, day_number))
            except (ValueError, AttributeError) as e:
                logger.error(f'Error processing history date {log_date}: {e}')
                continue
        
        embed = discord.Embed(
            title=f"📅 {interaction.user.name}'s Streak History",
            description=f"Last 30 days of your coding journey",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        for week_key in sorted(weeks_data.keys(), reverse=True)[:5]:
            week_data = weeks_data[week_key]
            week_start = datetime.strptime(week_key, "%Y-%m-%d")
            week_str = week_start.strftime("%b %d")
            
            days_counted = len(week_data)
            max_day = max(day_num for _, day_num in week_data)
            
            embed.add_field(
                name=f"Week of {week_str}",
                value=f"📆 {days_counted} days logged\n🔥 Up to Day {max_day}",
                inline=False
            )
        
        embed.set_footer(text=f"Total: {len(history)} days logged")
        await interaction.followup.send(embed=embed)
        logger.info(f'{interaction.user} viewed streak history')
    
    @app_commands.command(name="streak_calendar", description="View your streak calendar (Duolingo-style)")
    async def streak_calendar(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        history = self.db.get_streak_history(user_id, guild_id, limit=30)
        today = datetime.utcnow().date()
        
        embed = discord.Embed(
            title=f"📅 {interaction.user.name}'s Streak Calendar",
            description="Your coding activity over the last 30 days",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        logged_dates = {datetime.strptime(log_date, "%Y-%m-%d").date() for log_date, _ in history}
        
        calendar_lines = []
        for i in range(0, 30, 7):
            week_line = ""
            for j in range(7):
                day_offset = i + j
                if day_offset >= 30:
                    break
                
                date = today - timedelta(days=30 - day_offset - 1)
                if date in logged_dates:
                    week_line += "✅"
                elif date > today:
                    week_line += "⬜"
                else:
                    week_line += "⚫"
                
                if j < 6:
                    week_line += " "
            calendar_lines.append(week_line)
        
        calendar_text = "\n".join(calendar_lines)
        embed.add_field(name="Calendar (Last 30 Days)", value=f"```\n{calendar_text}\n```", inline=False)
        embed.add_field(name="Legend", value="✅ Logged | ⚫ Missed | ⬜ Future", inline=False)
        
        if history:
            current_streak, longest_streak, last_log_date, last_day_number = self.db.get_streak(user_id, guild_id) or (0, 0, None, 0)
            embed.add_field(name="🔥 Current Streak", value=f"{current_streak} days", inline=True)
            embed.add_field(name="💎 Best Streak", value=f"{longest_streak} days", inline=True)
        
        await interaction.followup.send(embed=embed)
        logger.info(f'{interaction.user} viewed streak calendar')
    
    @app_commands.command(name="use_freeze", description="Use a streak freeze to protect your streak (like Duolingo)")
    async def use_freeze(self, interaction: discord.Interaction):
        freeze_count = self.db.get_streak_freeze(interaction.user.id, interaction.guild_id)
        
        if freeze_count <= 0:
            embed = discord.Embed(
                title="❄️ No Streak Freezes Available",
                description="You don't have any streak freezes left!",
                color=discord.Color.red()
            )
            embed.add_field(
                name="How to get freezes",
                value="• Earn 1 freeze for every 7-day streak milestone\n• Freezes are automatically used if you miss a day\n• Keep coding to earn more!",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        streak_data = self.db.get_streak(user_id, guild_id)
        
        if streak_data:
            current_streak, longest_streak, last_log_date, last_day_number = streak_data
            days_since = self.calculate_days_since_last_log(last_log_date)
            
            if days_since < 3:
                embed = discord.Embed(
                    title="❄️ Streak Freeze Active",
                    description="Your streak is safe! No freeze needed right now.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Current Streak", value=f"{current_streak} days", inline=True)
                embed.add_field(name="Freezes Available", value=f"{freeze_count}", inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        if self.db.use_streak_freeze(user_id, guild_id):
            embed = discord.Embed(
                title="❄️ Streak Freeze Used!",
                description="Your streak has been protected for one day.",
                color=discord.Color.cyan()
            )
            embed.add_field(name="Freezes Remaining", value=str(freeze_count - 1), inline=True)
            embed.add_field(name="Current Streak", value=f"{current_streak} days", inline=True)
            embed.set_footer(text="Remember to code tomorrow to keep your streak going!")
            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} used a streak freeze')
        else:
            await interaction.response.send_message("❌ Failed to use freeze.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Streaks(bot))
