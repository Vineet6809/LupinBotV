import discord
from discord.ext import commands
from discord import app_commands
from database import Database
import logging
import re
from datetime import datetime

logger = logging.getLogger('LupinBot.utilities')


class Utilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    def get_all_commands_by_category(self):
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
            "backfill_history": "Streak Tracking",
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

    @app_commands.command(name="stats", description="Show server statistics")
    async def stats(self, interaction: discord.Interaction):
        guild = interaction.guild

        total_members = guild.member_count
        online_members = sum(1 for member in guild.members
                             if member.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)

        embed = discord.Embed(title=f"📊 {guild.name} Statistics",
                              color=discord.Color.blue())

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👥 Total Members",
                        value=str(total_members),
                        inline=True)
        embed.add_field(name="🟢 Online",
                        value=str(online_members),
                        inline=True)
        embed.add_field(name="📝 Text Channels",
                        value=str(text_channels),
                        inline=True)
        embed.add_field(name="🔊 Voice Channels",
                        value=str(voice_channels),
                        inline=True)
        embed.add_field(name="🎭 Roles", value=str(roles), inline=True)
        embed.add_field(
            name="👑 Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True)

        embed.set_footer(text=f"Server ID: {guild.id}")

        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} requested server stats')
    
    @app_commands.command(name="serverstats", description="Show server coding statistics")
    async def serverstats(self, interaction: discord.Interaction):
        """Show server-wide coding statistics."""
        await interaction.response.defer()
        
        # Get server stats from database
        total_users, active_today, total_days, avg_streak = self.db.get_server_stats(interaction.guild_id)
        
        embed = discord.Embed(
            title=f"📊 {interaction.guild.name} Coding Statistics",
            description="Community coding progress overview",
            color=discord.Color.blue()
        )
        
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
        embed.add_field(name="👥 Total Coders", value=str(total_users), inline=True)
        embed.add_field(name="🔥 Active Today", value=str(active_today), inline=True)
        embed.add_field(name="📈 Total Days Coded", value=str(total_days), inline=True)
        embed.add_field(name="📊 Average Streak", value=f"{avg_streak} days", inline=True)
        
        # Get activity percentage
        if total_users > 0:
            activity_pct = round((active_today / total_users) * 100, 1)
            embed.add_field(name="💪 Activity Rate", value=f"{activity_pct}%", inline=True)
        
        embed.set_footer(text="Keep coding to climb the stats! 🚀")
        
        await interaction.followup.send(embed=embed)
        logger.info(f'{interaction.user} requested server stats')

    @app_commands.command(name="help",
                          description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🦊 LupinBot - Complete Command Guide",
            description="Your **AI-powered coding streak companion**! 🚀\n\nTrack your coding streaks with smart detection, motivational features, and fun challenges designed specifically for developers.",
            color=discord.Color.blue()
        )
        
        # Add thumbnail
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        
        # Dynamically collect all commands
        commands_by_category = self.get_all_commands_by_category()
        
        # Emoji mapping for categories
        category_emojis = {
            "Streak Tracking": "🔥",
            "Fun & Motivation": "🎮",
            "Server Statistics": "📊",
            "Moderation": "🔨",
            "Server Configuration": "⚙️",
            "Challenges": "💻"
        }
        
        # Build fields dynamically from registered commands
        for category, commands in commands_by_category.items():
            if commands:
                emoji = category_emojis.get(category, "📌")
                value_parts = []
                
                # Special formatting for Streak Tracking
                if category == "Streak Tracking":
                    value_parts.append("**🎯 How it works**: Just share code daily! No need for #DAY-n.\n")
                
                for cmd_name, cmd_description in commands:
                    value_parts.append(f"`/{cmd_name}` - {cmd_description}")
                
                if value_parts:
                    embed.add_field(
                        name=f"{emoji} {category}",
                        value="\n".join(value_parts),
                        inline=False
                    )
        
        # AI FEATURES SECTION
        embed.add_field(
            name="🤖 **AI-Powered Features**",
            value=(
                "✨ **Smart Detection**: Automatically detects code in messages\n"
                "📁 **File Analysis**: Supports 20+ programming languages\n"
                "🖼️ **Image Recognition**: Reads code from screenshots\n"
                "🔍 **Pattern Matching**: Understands #DAY-1, day 2, etc.\n"
                "⚡ **Instant Processing**: Real-time streak updates"
            ),
            inline=False
        )
        
        # ACHIEVEMENTS SECTION
        embed.add_field(
            name="🏆 **Achievement Badges**",
            value=(
                "🔰 **Beginner** - 1-6 days\n"
                "🌟 **Rising Star** - 7-29 days\n"
                "⭐ **Champion** - 30-99 days\n"
                "💎 **Master** - 100-364 days\n"
                "🏆 **Legend** - 365+ days"
            ),
            inline=True
        )
        
        # PROTECTION SECTION
        embed.add_field(
            name="🛡️ **Streak Protection**",
            value=(
                "❄️ **Grace Period**: 2-day buffer\n"
                "🧊 **Freeze System**: Protect your streak\n"
                "🔄 **Restore**: Recover lost streaks\n"
                "📅 **Calendar View**: Visual progress tracking"
            ),
            inline=True
        )
        
        # TIPS SECTION
        embed.add_field(
            name="💡 **Pro Tips**",
            value=(
                "• **No #DAY needed**: Just share any code!\n"
                "• **File uploads**: `.py`, `.js`, `.java`, `.cpp`, etc.\n"
                "• **Screenshots**: I can read code in images\n"
                "• **Flexible**: Works with any coding activity\n"
                "• **Consistent**: Aim for daily coding habits! 🎯"
            ),
            inline=False
        )
        
        # QUICK START SECTION
        embed.add_field(
            name="🚀 **Quick Start**",
            value=(
                "1️⃣ Share code in #daily-code\n"
                "2️⃣ Upload files or screenshots\n"
                "3️⃣ Use `/mystats` to check progress\n"
                "4️⃣ Build your streak daily! 🔥"
            ),
            inline=False
        )
        
        embed.set_footer(
            text="Ready to start your coding journey? Share some code now! 💻 | Tag @Lupin for introduction"
        )
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} requested help')

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="The poll question",
                           options="Poll options separated by commas (max 10)")
    async def poll(self, interaction: discord.Interaction, question: str,
                   options: str):
        option_list = [opt.strip() for opt in options.split(',')]

        if len(option_list) < 2:
            await interaction.response.send_message(
                "❌ You need at least 2 options for a poll!", ephemeral=True)
            return

        if len(option_list) > 10:
            await interaction.response.send_message(
                "❌ Maximum 10 options allowed!", ephemeral=True)
            return

        embed = discord.Embed(title="📊 Poll",
                              description=question,
                              color=discord.Color.blue())

        emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]

        for idx, option in enumerate(option_list):
            embed.add_field(name=f"{emojis[idx]} Option {idx + 1}",
                            value=option,
                            inline=False)

        embed.set_footer(text=f"Poll created by {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

        message = await interaction.original_response()
        for idx in range(len(option_list)):
            await message.add_reaction(emojis[idx])

        logger.info(f'{interaction.user} created a poll: {question}')

    @app_commands.command(
        name="setreminder",
        description="Set the daily reminder time (Admin only)")
    @app_commands.describe(time="Time in HH:MM AM/PM format (e.g., 06:30 PM)")
    async def setreminder(self, interaction: discord.Interaction, time: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True)
            return

        # Regex for HH:MM AM/PM format
        if not re.match(r'^(0[1-9]|1[0-2]):([0-5]\d) (AM|PM)$', time, re.IGNORECASE):
            await interaction.response.send_message(
                "❌ Invalid time format. Please use HH:MM AM/PM (e.g., 06:30 PM).",
                ephemeral=True)
            return

        try:
            # Convert to 24-hour format for storage
            time_obj = datetime.strptime(time, '%I:%M %p')
            time_24h = time_obj.strftime('%H:%M')

            self.db.set_server_setting(interaction.guild_id, 'reminder_time', time_24h)

            embed = discord.Embed(
                title="⏰ Reminder Time Updated",
                description=f"Daily streak reminder set to **{time}**",
                color=discord.Color.green())

            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} set reminder time to {time}')
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time input. Please check the format.",
                ephemeral=True)

    @app_commands.command(
        name="setchallengechannel",
        description="Set the channel for daily challenges (Admin only)")
    @app_commands.describe(channel="The channel to post daily challenges")
    async def setchallengechannel(self, interaction: discord.Interaction,
                                  channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True)
            return

        self.db.set_server_setting(interaction.guild_id,
                                   'challenge_channel_id', channel.id)

        embed = discord.Embed(
            title="✅ Challenge Channel Set",
            description=f"Daily challenges will be posted in {channel.mention}",
            color=discord.Color.green())

        await interaction.response.send_message(embed=embed)
        logger.info(
            f'{interaction.user} set challenge channel to {channel.name}')

    @app_commands.command(
        name="setreminderchannel",
        description="Set the channel for daily reminders (Admin only)")
    @app_codes.describe(channel="The channel to post daily reminders")
    async def setreminderchannel(self, interaction: discord.Interaction,
                                 channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True)
            return

        self.db.set_server_setting(interaction.guild_id, 'reminder_channel_id',
                                   channel.id)

        embed = discord.Embed(
            title="✅ Reminder Channel Set",
            description=f"Daily reminders will be posted in {channel.mention}",
            color=discord.Color.green())

        await interaction.response.send_message(embed=embed)
        logger.info(
            f'{interaction.user} set reminder channel to {channel.name}')
    
    @app_commands.command(name="sync_commands", description="Sync bot commands with Discord (Admin only)")
    async def sync_commands(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True)
            return
        
        try:
            synced = await interaction.client.tree.sync()
            embed = discord.Embed(
                title="✅ Commands Synced",
                description=f"Successfully synced {len(synced)} slash commands with Discord",
                color=discord.Color.green())
            
            # List all synced commands
            command_list = "\n".join([f"`/{cmd.name}` - {cmd.description}" for cmd in synced[:10]])
            if len(synced) > 10:
                command_list += f"\n*...and {len(synced) - 10} more commands*"
            
            embed.add_field(name="Synced Commands", value=command_list, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f'{interaction.user} manually synced commands')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')
            await interaction.response.send_message(
                f"❌ Failed to sync commands: {str(e)}",
                ephemeral=True)


async def setup(bot):
    await bot.add_cog(Utilities(bot))