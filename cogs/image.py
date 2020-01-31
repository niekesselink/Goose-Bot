import discord
import requests

from discord.ext import commands

class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function that gets an image from a given url
    async def getimage(self, ctx, link: str, keyword: str):
        image = discord.Embed()
        image.set_image(url=requests.get(link).json()[keyword])
        await ctx.send(embed=image)

    @commands.command(brief='Posts a random cat picture')
    async def cat(self, ctx):
        await self.getimage(ctx, 'http://aws.random.cat/meow', 'file')

    @commands.command(brief='Posts a random dog picture')
    async def dog(self, ctx):
        await self.getimage(ctx, 'http://random.dog/woof.json', 'url')

    @commands.command(brief='Posts a random birb picture')
    async def birb(self, ctx):
        await self.getimage(ctx, 'https://api.alexflipnote.dev/birb', 'file')

    @commands.command(brief='Posts a random duck picture')
    async def duck(self, ctx):
        await self.getimage(ctx, 'https://random-d.uk/api/v1/random', 'url')     

    @commands.command(brief='Posts a random panda picture')
    async def panda(self, ctx):
        await self.getimage(ctx, 'https://some-random-api.ml/img/panda', 'link') 
        
    @commands.command(brief='Posts a random koala picture')
    async def koala(self, ctx):
        await self.getimage(ctx, 'https://some-random-api.ml/img/koala', 'link')     
        
def setup(bot):
    bot.add_cog(Image(bot))