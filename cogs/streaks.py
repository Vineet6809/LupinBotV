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
        """Enhanced code detection for streak tracking."""
        if not content:
            return False
            
        # Check for code blocks first
        if self.code_pattern.search(content):
            return True
        
        # Check for day patterns (if it mentions a day, it's likely a coding entry)
        day_patterns = [
            r'#\s*day[\s-]*\d+',
            r'day\s*\d+',
            r'#day\d+',
            r'day-\d+',
            r'coding',
            r'programming',
            r'challenge',
            r'leetcode',
            r'hackerrank',
            r'codewars',
            r'project',
            r'algorithm',
            r'data structure',
            r'dsa',
            r'problem\s*\d+',
            r'solution',
            r'debug',
            r'fix',
            r'optimize',
            r'refactor'
        ]
        
        for pattern in day_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # Enhanced code keywords
        code_keywords = [
            'def ', 'class ', 'import ', 'function ', 'const ', 'let ', 'var ',
            'public ', 'private ', 'void ', 'int ', 'string ', 'return ',
            'if ', 'else ', 'for ', 'while ', 'try ', 'catch ', '#include',
            'console.log', 'print(', 'System.out', 'printf', 'cout',
            'function(', '=>', 'async', 'await', 'promise',
            'main(', 'public static void', 'namespace', 'using ',
            'require(', 'module.exports', 'export ', 'import ',
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE',
            'html', 'css', 'javascript', 'python', 'java', 'cpp', 'c++',
            'react', 'vue', 'angular', 'node', 'express', 'django',
            'sql', 'mongodb', 'mysql', 'postgresql',
            'git', 'commit', 'push', 'pull', 'branch',
            'api', 'endpoint', 'request', 'response', 'json',
            'array', 'list', 'dictionary', 'hashmap', 'tree',
            'binary', 'search', 'sort', 'recursion', 'dynamic'
        ]
        
        return any(keyword in content.lower() for keyword in code_keywords)
    
    async def has_media_or_code(self, message) -> bool:
        """Enhanced detection for code content including files and images."""
        # Check text content first
        if self.detect_code(message.content):
            return True
        
        # Check for attachments (code files and images)
        if message.attachments:
            for attachment in message.attachments:
                # Check for code files
                if attachment.filename:
                    code_extensions = [
                        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.php',
                        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
                        '.html', '.css', '.scss', '.sass', '.less', '.xml',
                        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
                        '.sql', '.sh', '.bash', '.ps1', '.bat', '.cmd',
                        '.md', '.txt', '.log', '.conf', '.config'
                    ]
                    
                    if any(attachment.filename.lower().endswith(ext) for ext in code_extensions):
                        logger.info(f'Code file detected: {attachment.filename}')
                        return True
                
                # Check for images that might contain code
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
                        # If Gemini fails, assume it might contain code for safety
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
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.reference:
            return
        
        user_id = message.author.id
        guild_id = message.guild.id
        
        # Enhanced day pattern detection
        day_patterns = [
            r'#\s*day[\s-]*(\d+)',  # #DAY-17, #DAY 17, etc.
            r'day\s*(\d+)',         # day 17
            r'#day(\d+)',          # #day17
            r'day-(\d+)',          # day-17
            r'day\s*(\d+)',        # day 17
            r'coding\s*day\s*(\d+)', # coding day 17
            r'challenge\s*(\d+)',   # challenge 17
            r'problem\s*(\d+)',    # problem 17
            r'leetcode\s*(\d+)',  # leetcode 17
            r'day\s*(\d+)\s*of',   # day 17 of
            r'(\d+)\s*day',        # 17 day
        ]
        
        day_number = None
        for pattern in day_patterns:
            match = re.search(pattern, message.content, re.IGNORECASE)
            if match:
                try:
                    day_number = int(match.group(1))
                    logger.info(f'Day number detected: {day_number} from pattern: {pattern}')
                    break
                except (ValueError, IndexError):
                    continue
        
        # If no day number found, try to extract any number that could be a day
        if not day_number:
            numbers = re.findall(r'\b(\d+)\b', message.content)
            if numbers:
                # Take the largest number as potential day number
                day_number = max(int(n) for n in numbers)
                logger.info(f'Day number inferred from largest number: {day_number}')
        
        # Day number detection is now handled above
        
        has_content = await self.has_media_or_code(message)
        
        # Check if user has already logged today
        if self.db.has_logged_today(user_id, guild_id):
            today_day_number = self.db.get_todays_day_number(user_id, guild_id)
            
            # If user provided a day number, check if it matches what they should be logging
            if day_number:
                streak_data = self.db.get_streak(user_id, guild_id)
                if streak_data:
                    _, _, last_log_date, last_day_number = streak_data
                    days_since = self.calculate_days_since_last_log(last_log_date)
                    expected_day = last_day_number + 1
                    
                    # If the day number matches what they should log, it's a duplicate
                    if day_number == expected_day:
                        await message.add_reaction('✅')
                        embed = discord.Embed(
                            title="✅ Already Completed",
                            description=f"{message.author.mention}, you've already completed #DAY-{today_day_number} today! Come back tomorrow to continue your streak.",
                            color=discord.Color.green()
                        )
                        await message.channel.send(embed=embed)
                        logger.info(f'User {message.author} tried to log again for Day {day_number}')
                        return
                    # If day number doesn't match, continue processing (might be correcting day)
                    else:
                        logger.info(f'User {message.author} provided day {day_number} but already logged day {today_day_number}, processing as correction')
                else:
                    # No streak data, but they logged today - this shouldn't happen normally
                    await message.add_reaction('✅')
                    embed = discord.Embed(
                        title="✅ Already Completed",
                        description=f"{message.author.mention}, you've already completed your streak for today! Come back tomorrow to continue.",
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed)
                    logger.warning(f'User {message.author} tried to log again but no streak data found')
                    return
            else:
                # No day number provided, just content - treat as duplicate
                await message.add_reaction('✅')
                embed = discord.Embed(
                    title="✅ Already Completed",
                    description=f"{message.author.mention}, you've already completed your streak for today! Come back tomorrow to continue.",
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed)
                logger.info(f'User {message.author} tried to log again without day number')
                return
        
        if not day_number and not has_content:
            return
        
        # Get streak data once
        streak_data = self.db.get_streak(user_id, guild_id)
        
        # Validate day number if provided
        if day_number:
            try:
                # Validate day number (prevent abuse)
                if day_number < 1 or day_number > 10000:
                    await message.channel.send("❌ Day number must be between 1 and 10000.")
                    logger.warning(f'User {message.author} attempted invalid day number: {day_number}')
                    return
            except (ValueError, AttributeError) as e:
                logger.error(f'Error parsing day number: {e}')
                await message.channel.send("❌ Invalid day number format.")
                return
        else:
            # No day number provided, infer from streak data
            if streak_data:
                _, _, last_log_date, last_day_number = streak_data
                day_number = last_day_number + 1
            else:
                day_number = 1
        
        # Calculate streak metrics
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
            
            if days_since == 2 and (day_number == expected_day or not day_number):
                if not day_number:
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
            
            elif day_number == expected_day or (not day_number and days_since <= 1):
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
                
                if not day_number:
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
            if day_number == 1 or not day_number:
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
        
        # Validate day number
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
        """Show user's recent streak history."""
        await interaction.response.defer()  # Fix 404 error by deferring
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        # Get history from database
        history = self.db.get_streak_history(user_id, guild_id, limit=30)
        
        if not history:
            await interaction.followup.send("You haven't logged any streaks yet! Post some code to begin!", ephemeral=True)
            return
        
        # Group by week
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
        
        # Show most recent 5 weeks
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
        """Show a calendar view of your coding streak like Duolingo."""
        await interaction.response.defer()
        
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        
        # Get last 30 days
        history = self.db.get_streak_history(user_id, guild_id, limit=30)
        today = datetime.utcnow().date()
        
        embed = discord.Embed(
            title=f"📅 {interaction.user.name}'s Streak Calendar",
            description="Your coding activity over the last 30 days",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Create date set for quick lookup
        logged_dates = {datetime.strptime(log_date, "%Y-%m-%d").date() for log_date, _ in history}
        
        # Build calendar grid
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
        
        # Streak info
        if history:
            current_streak, longest_streak, last_log_date, last_day_number = self.db.get_streak(user_id, guild_id) or (0, 0, None, 0)
            embed.add_field(name="🔥 Current Streak", value=f"{current_streak} days", inline=True)
            embed.add_field(name="💎 Best Streak", value=f"{longest_streak} days", inline=True)
        
        await interaction.followup.send(embed=embed)
        logger.info(f'{interaction.user} viewed streak calendar')
    
    @app_commands.command(name="use_freeze", description="Use a streak freeze to protect your streak (like Duolingo)")
    async def use_freeze(self, interaction: discord.Interaction):
        """Use a streak freeze to prevent losing your streak for missing a day."""
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
        
        # Check if freeze is needed
        user_id = interaction.user.id
        guild_id = interaction.guild_id
        streak_data = self.db.get_streak(user_id, guild_id)
        
        if streak_data:
            current_streak, longest_streak, last_log_date, last_day_number = streak_data
            days_since = self.calculate_days_since_last_log(last_log_date)
            
            # Only allow freeze if they're about to lose streak
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
        
        # Use the freeze
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
