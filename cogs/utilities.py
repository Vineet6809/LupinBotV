import discord
from discord.ext import commands
from discord import app_commands
from database import Database
import logging

logger = logging.getLogger('LupinBot.utilities')

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    @app_commands.command(name="stats", description="Show server statistics")
    async def stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Statistics",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👥 Total Members", value=str(total_members), inline=True)
        embed.add_field(name="🟢 Online", value=str(online_members), inline=True)
        embed.add_field(name="📝 Text Channels", value=str(text_channels), inline=True)
        embed.add_field(name="🔊 Voice Channels", value=str(voice_channels), inline=True)
        embed.add_field(name="🎭 Roles", value=str(roles), inline=True)
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} requested server stats')
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="The poll question", options="Poll options separated by commas (max 10)")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ You need at least 2 options for a poll!", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ Maximum 10 options allowed!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue()
        )
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for idx, option in enumerate(option_list):
            embed.add_field(name=f"{emojis[idx]} Option {idx + 1}", value=option, inline=False)
        
        embed.set_footer(text=f"Poll created by {interaction.user.name}")
        
        await interaction.response.send_message(embed=embed)
        
        message = await interaction.original_response()
        for idx in range(len(option_list)):
            await message.add_reaction(emojis[idx])
        
        logger.info(f'{interaction.user} created a poll: {question}')
    
    @app_commands.command(name="setreminder", description="Set the daily reminder time (Admin only)")
    @app_commands.describe(time="Time in HH:MM format (24-hour, UTC)")
    async def setreminder(self, interaction: discord.Interaction, time: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        import re
        if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time):
            await interaction.response.send_message("❌ Invalid time format. Use HH:MM (24-hour format).", ephemeral=True)
            return
        
        self.db.set_server_setting(interaction.guild_id, 'reminder_time', time)
        
        embed = discord.Embed(
            title="⏰ Reminder Time Updated",
            description=f"Daily streak reminder set to **{time} UTC**",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} set reminder time to {time} UTC')
    
    @app_commands.command(name="setchallengechannel", description="Set the channel for daily challenges (Admin only)")
    @app_commands.describe(channel="The channel to post daily challenges")
    async def setchallengechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        self.db.set_server_setting(interaction.guild_id, 'challenge_channel_id', channel.id)
        
        embed = discord.Embed(
            title="✅ Challenge Channel Set",
            description=f"Daily challenges will be posted in {channel.mention}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} set challenge channel to {channel.name}')
    
    @app_commands.command(name="setreminderchannel", description="Set the channel for daily reminders (Admin only)")
    @app_commands.describe(channel="The channel to post daily reminders")
    async def setreminderchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        self.db.set_server_setting(interaction.guild_id, 'reminder_channel_id', channel.id)
        
        embed = discord.Embed(
            title="✅ Reminder Channel Set",
            description=f"Daily reminders will be posted in {channel.mention}",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)
        logger.info(f'{interaction.user} set reminder channel to {channel.name}')

async def setup(bot):
    await bot.add_cog(Utilities(bot))
