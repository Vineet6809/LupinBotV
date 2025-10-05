import discord
from discord.ext import commands
from discord import app_commands
import requests
import random
import logging

logger = logging.getLogger('LupinBot.fun')

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="meme", description="Get a random programming meme")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            response = requests.get('https://meme-api.com/gimme/ProgrammerHumor', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                embed = discord.Embed(
                    title=data.get('title', 'Programming Meme'),
                    color=discord.Color.purple()
                )
                embed.set_image(url=data['url'])
                embed.set_footer(text=f"👍 {data.get('ups', 0)} upvotes | r/{data.get('subreddit', 'ProgrammerHumor')}")
                
                await interaction.followup.send(embed=embed)
                logger.info(f'Sent meme to {interaction.user}')
            else:
                await interaction.followup.send("❌ Couldn't fetch a meme right now. Try again later!")
        except Exception as e:
            logger.error(f'Error fetching meme: {e}')
            await interaction.followup.send("❌ An error occurred while fetching the meme.")
    
    @app_commands.command(name="quote", description="Get an inspiring quote")
    async def quote(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            response = requests.get('https://api.quotable.io/random?tags=technology,inspirational', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                embed = discord.Embed(
                    description=f"*\"{data['content']}\"*",
                    color=discord.Color.blue()
                )
                embed.set_author(name=data['author'])
                embed.set_footer(text="💡 Stay motivated!")
                
                await interaction.followup.send(embed=embed)
                logger.info(f'Sent quote to {interaction.user}')
            else:
                await interaction.followup.send("❌ Couldn't fetch a quote right now. Try again later!")
        except Exception as e:
            logger.error(f'Error fetching quote: {e}')
            await interaction.followup.send("❌ An error occurred while fetching the quote.")
    
    @app_commands.command(name="joke", description="Get a programming joke")
    async def joke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            response = requests.get('https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw,religious,political,racist,sexist,explicit', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                embed = discord.Embed(
                    title="😄 Programming Joke",
                    color=discord.Color.green()
                )
                
                if data['type'] == 'single':
                    embed.description = data['joke']
                else:
                    embed.add_field(name="Setup", value=data['setup'], inline=False)
                    embed.add_field(name="Punchline", value=data['delivery'], inline=False)
                
                embed.set_footer(text="Laugh and code on! 😊")
                
                await interaction.followup.send(embed=embed)
                logger.info(f'Sent joke to {interaction.user}')
            else:
                await interaction.followup.send("❌ Couldn't fetch a joke right now. Try again later!")
        except Exception as e:
            logger.error(f'Error fetching joke: {e}')
            await interaction.followup.send("❌ An error occurred while fetching the joke.")

async def setup(bot):
    await bot.add_cog(Fun(bot))
