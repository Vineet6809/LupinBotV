import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import Database
import logging
import re
from datetime import datetime, time

logger = logging.getLogger('LupinBot.utilities')

class Utilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.daily_reminder.start()

    def cog_unload(self):
        self.daily_reminder.cancel()

    def get_all_commands_by_category(self):
        # ... (rest of the function is unchanged)
        """Dynamically collect all registered commands and organize by category."""
        commands_by_category = {
            "Streak Tracking": [],
            "Fun & Motivation": [],
            "Server Statistics": [],
            "Moderation": [],
            "Server Configuration": [],
            "Challenges": []
        }
        
        # Define command categorization
        category_mapping = {
            "leaderboard": "Streak Tracking",
            "mystats": "Streak Tracking",
            "streaks_history": "Streak Tracking",
            "streak_calendar": "Streak Tracking",
            "use_freeze": "Streak Tracking",
            "restore": "Streak Tracking",
            "meme": "Fun & Motivation",
            "quote": "Fun & Motivation",
            "joke": "Fun & Motivation",
            "stats": "Server Statistics",
            "serverstats": "Server Statistics",
            "poll": "Server Statistics",
            "kick": "Moderation",
            "ban": "Moderation",
            "mute": "Moderation",
            "clear": "Moderation",
            "giverole": "Moderation",
            "setreminder": "Server Configuration",
            "setreminderchannel": "Server Configuration",
            "setchallengechannel": "Server Configuration",
            "sync_commands": "Server Configuration",
            "challenge": "Challenges"
        }
        
        # Get all registered commands from the bot tree
        for command in self.bot.tree.walk_commands():
            if isinstance(command, app_commands.Command):
                cmd_name = command.name
                cmd_description = command.description
                
                # Determine category
                category = category_mapping.get(cmd_name, "Other")
                
                if category in commands_by_category:
                    commands_by_category[category].append((cmd_name, cmd_description))
        
        return commands_by_category

    @tasks.loop(time=time(hour=0, minute=0)) # Default time, will be configured
    async def daily_reminder(self):
        logger.info("Checking for daily reminders...")
        all_servers = self.db.get_all_server_settings()
        for guild_id, settings in all_servers.items():
            if settings.get('reminder_enabled', False):
                try:
                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue

                    reminder_time_str = settings.get('reminder_time')
                    if not reminder_time_str:
                        continue
                    
                    # Convert 12-hour format to 24-hour for comparison
                    try:
                        reminder_time = datetime.strptime(reminder_time_str, "%I:%M %p").time()
                    except ValueError:
                        try:
                            reminder_time = datetime.strptime(reminder_time_str, "%H:%M").time()
                        except ValueError:
                            logger.warning(f"Invalid time format in DB for guild {guild_id}: {reminder_time_str}")
                            continue
                    
                    # Check if it's time to send the reminder
                    now_utc = datetime.utcnow().time()
                    if now_utc.hour == reminder_time.hour and now_utc.minute == reminder_time.minute:
                        channel_id = settings.get('reminder_channel_id')
                        if not channel_id:
                            logger.warning(f"Reminder channel not set for guild {guild_id}")
                            continue

                        channel = guild.get_channel(channel_id)
                        if not channel:
                            logger.warning(f"Reminder channel not found for guild {guild_id}")
                            continue

                        # Get users who haven't logged today
                        users_to_remind = self.db.get_users_to_remind(guild_id)
                        if not users_to_remind:
                            logger.info(f"No users to remind in {guild.name}")
                            continue

                        mentions = [f'<@{user_id}>' for user_id in users_to_remind]
                        
                        embed = discord.Embed(
                            title="🔥 Daily Streak Reminder!",
                            description=(
                                f"Hey {', '.join(mentions)}! Don't forget to post your coding progress today to keep your streak alive. "
                                f"You can post code snippets, GitHub links, or even screenshots of your work in the #daily-code channel.\n\n"
                                f"**Keep that fire going!** 🔥"
                            ),
                            color=discord.Color.orange()
                        )
                        embed.set_footer(text="Consistency is key to mastery. You can do it!")
                        await channel.send(embed=embed)
                        logger.info(f"Sent reminders to {len(users_to_remind)} users in {guild.name}")

                except Exception as e:
                    logger.error(f"Error sending reminder for guild {guild_id}: {e}")

    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()
        logger.info("Starting daily reminder loop...")

    @app_commands.command(name="setreminder", description="Set the daily reminder time (Admin only, 12-hour or 24-hour format)")
    @app_commands.describe(time="Time in 'HH:MM AM/PM' or 'HH:MM' (24h) format (e.g., '08:30 PM' or '20:30')")
    async def setreminder(self, interaction: discord.Interaction, time: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        time_str_cleaned = time.strip().upper()
        
        # Regex for 12-hour and 24-hour format
        match_12hr = re.match(r'^(1[0-2]|0?[1-9]):([0-5][0-9])\s*(AM|PM)$', time_str_cleaned)
        match_24hr = re.match(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$', time_str_cleaned)
        
        if not match_12hr and not match_24hr:
            await interaction.response.send_message("❌ Invalid time format. Use 'HH:MM AM/PM' or 'HH:MM' (24h).", ephemeral=True)
            return

        # Store the validated time string
        valid_time_str = time_str_cleaned
        if match_12hr:
            # Convert to a standard format if needed, but storing as is is fine
            hour, minute, period = match_12hr.groups()
            valid_time_str = f"{int(hour):02d}:{minute} {period}"
        elif match_24hr:
            hour, minute = match_24hr.groups()
            # Convert to 12-hour format for consistency in display
            d = datetime.strptime(f"{hour}:{minute}", "%H:%M")
            valid_time_str = d.strftime("%I:%M %p")


        self.db.set_server_setting(interaction.guild_id, 'reminder_time', valid_time_str)
        self.db.set_server_setting(interaction.guild_id, 'reminder_enabled', True)

        embed = discord.Embed(
            title="⏰ Reminder Time Updated",
            description=f"The daily streak reminder has been set to **{valid_time_str}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Next Steps", value="Make sure you have set a reminder channel using `/setreminderchannel`.")
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} set reminder time to {valid_time_str}')

async def setup(bot):
    await bot.add_cog(Utilities(bot))
