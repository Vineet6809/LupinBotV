import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('LupinBot.moderation')

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="kick", description="Kick a member from the server (Admin only)")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to kick members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot kick someone with an equal or higher role.", ephemeral=True)
            return
        
        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} kicked {member} for: {reason}')
        except Exception as e:
            logger.error(f'Error kicking member: {e}')
            await interaction.response.send_message(f"❌ Failed to kick {member.mention}.", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server (Admin only)")
    @app_commands.describe(member="The member to ban", reason="Reason for banning")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to ban members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot ban someone with an equal or higher role.", ephemeral=True)
            return
        
        try:
            await member.ban(reason=reason)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned from the server.",
                color=discord.Color.red()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} banned {member} for: {reason}')
        except Exception as e:
            logger.error(f'Error banning member: {e}')
            await interaction.response.send_message(f"❌ Failed to ban {member.mention}.", ephemeral=True)
    
    @app_commands.command(name="mute", description="Timeout a member (Admin only)")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You don't have permission to timeout members.", ephemeral=True)
            return
        
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot timeout someone with an equal or higher role.", ephemeral=True)
            return
        
        try:
            import datetime
            timeout_duration = datetime.timedelta(minutes=duration)
            await member.timeout(timeout_duration, reason=reason)
            
            embed = discord.Embed(
                title="🔇 Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} timed out {member} for {duration} minutes: {reason}')
        except Exception as e:
            logger.error(f'Error timing out member: {e}')
            await interaction.response.send_message(f"❌ Failed to timeout {member.mention}.", ephemeral=True)
    
    @app_commands.command(name="giverole", description="Give a role to a member (Admin only)")
    @app_commands.describe(member="The member to give a role to", role="The role to give")
    async def giverole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to manage roles.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role:
            await interaction.response.send_message("❌ You cannot assign a role equal to or higher than your own.", ephemeral=True)
            return
        
        try:
            await member.add_roles(role)
            
            embed = discord.Embed(
                title="✅ Role Assigned",
                description=f"{role.mention} has been given to {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f'{interaction.user} gave role {role.name} to {member}')
        except Exception as e:
            logger.error(f'Error giving role: {e}')
            await interaction.response.send_message(f"❌ Failed to give role to {member.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
