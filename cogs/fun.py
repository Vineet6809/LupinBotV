import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import random
import logging
from cache import cache

logger = logging.getLogger('LupinBot.fun')

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = None
    
    async def cog_load(self):
        """Initialize HTTP session when cog loads."""
        self.session = aiohttp.ClientSession()
    
    async def cog_unload(self):
        """Close HTTP session when cog unloads."""
        if self.session:
            await self.session.close()
    
    async def fetch_json(self, url: str, cache_key: str = None):
        """Fetch JSON from URL with caching."""
        # Try cache first if a cache key is provided
        if cache_key:
            cached = await cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit for {cache_key}")
                return cached
        
        # Fetch from API
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache the result
                    if cache_key:
                        await cache.set(cache_key, data, ttl=600)  # 10 minutes
                    return data
                else:
                    logger.warning(f"API returned status {response.status} for {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @app_commands.command(name="meme", description="Get a random programming meme")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        data = await self.fetch_json(
            'https://meme-api.com/gimme/ProgrammerHumor',
            cache_key=f"meme_{interaction.user.id}"  # Cache per user
        )
        
        if data:
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
    
    @app_commands.command(name="quote", description="Get an inspiring quote")
    async def quote(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        data = await self.fetch_json(
            'https://api.quotable.io/random?tags=technology,inspirational',
            cache_key=f"quote_{interaction.user.id}"
        )
        
        if data:
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
    
    @app_commands.command(name="joke", description="Get a programming joke")
    async def joke(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        data = await self.fetch_json(
            'https://v2.jokeapi.dev/joke/Programming?blacklistFlags=nsfw,religious,political,racist,sexist,explicit',
            cache_key=f"joke_{interaction.user.id}"
        )
        
        if data:
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

async def setup(bot):
    await bot.add_cog(Fun(bot))
