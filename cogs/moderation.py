import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta, timezone

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
            import datetime as _dt
            timeout_duration = _dt.timedelta(minutes=duration)
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
    
    @app_commands.command(name="clear", description="Clear recent messages in the channel (Admin only)")
    async def clear(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to manage messages.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = interaction.channel
            deleted_count = 0
            fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)

            while True:
                messages = []
                async for message in channel.history(limit=100):
                    messages.append(message)
                
                if not messages:
                    break
                
                # Filter messages newer than 14 days for bulk delete
                recent_msgs = [m for m in messages if m.created_at > fourteen_days_ago]
                old_msgs = [m for m in messages if m.created_at <= fourteen_days_ago]

                if len(recent_msgs) > 1:
                    await channel.delete_messages(recent_msgs)
                    deleted_count += len(recent_msgs)
                elif len(recent_msgs) == 1:
                    await recent_msgs[0].delete()
                    deleted_count += 1

                # Delete old messages individually to avoid bulk delete restriction
                for m in old_msgs:
                    try:
                        await m.delete()
                        deleted_count += 1
                    except Exception:
                        # Stop if we hit rate limits or permissions
                        pass
                
                # If less than 100 were found, we've likely reached the start
                if len(messages) < 100:
                    break
            
            embed = discord.Embed(
                title="🧹 Channel Cleared",
                description=f"Successfully deleted {deleted_count} messages from {channel.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f'{interaction.user} cleared {deleted_count} messages from #{channel.name}')
        except Exception as e:
            logger.error(f'Error clearing channel: {e}')
            await interaction.followup.send(f"❌ Failed to clear messages: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
