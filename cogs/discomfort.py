import discord

from discord.ext import commands
from utils import language

class Discomfort(commands.Cog):
    """Program for meeting people out of your comfort zone."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.group()
    async def discomfort(self, ctx):
        """Find and meet strangers through the Discomfort program."""
        return    
    
    @discomfort.command()
    async def about(self, ctx):
        """Shows more information about the Discomfort program."""
        await ctx.send(await language.get(self, ctx.guild.id, 'discomfort.about'))

    @discomfort.command()
    async def join(self, ctx):
        """Joins the Discomfort program."""
        await ctx.send(await language.get(self, ctx.guild.id, 'discomfort.join'))

def setup(bot):
    bot.add_cog(Discomfort(bot))
