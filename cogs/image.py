import discord
import requests

from discord.ext import commands

class Image(commands.Cog):
    """Random images commands for fun."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cat(self, ctx):
        """Posts a random cat picture."""
        await self.get_image(ctx, 'http://aws.random.cat/meow', 'file')

    @commands.command()
    async def dog(self, ctx):
        """Posts a random dog picture."""
        await self.get_image(ctx, 'http://random.dog/woof.json', 'url')

    @commands.command()
    async def birb(self, ctx):
        """Posts a random birb picture."""
        await self.get_image(ctx, 'https://api.alexflipnote.dev/birb', 'file')

    @commands.command()
    async def duck(self, ctx):
        """Posts a random duck picture."""
        await self.get_image(ctx, 'https://random-d.uk/api/v1/random', 'url') 
        
    async def get_image(self, ctx, link: str, keyword: str):
        """Function that gets an image from a given url and places it in an embed."""

        image = discord.Embed()
        image.set_image(url=requests.get(link).json()[keyword])
        await ctx.send(embed=image)

def setup(bot):
    bot.add_cog(Image(bot))