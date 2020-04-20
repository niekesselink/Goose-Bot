import discord
import os

from discord.ext import commands
from utils import data

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(hidden=True)
    async def debug(self, ctx):
        return

    @commands.is_owner()
    @debug.command(hidden=True)
    async def loadcog(self, ctx, name):
        """ Load a specific cog """

        self.bot.load_extension(f"cogs.{name}")
        await ctx.send(f'Honk honk, cog {name} has been loaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def unloadcog(self, ctx, name):
        """ Unload a specific cog """

        self.bot.unload_extension(f"cogs.{name}")
        await ctx.send(f'Honk honk, cog {name} has been unloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadcog(self, ctx, name):
        """ Reloads a specific cog """

        self.bot.reload_extension(f"cogs.{name}")
        await ctx.send(f'Honk honk, cog {name} has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadconfig(self, ctx):
        """ Reloads the config.json """

        self.bot.config = data.getjson('config.json')
        await ctx.send(f'Honk honk, config.json has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadutil(self, ctx, name: str):
        """ Reloads an util module. """

        util = importlib.import_module(f"utils.{name}")
        importlib.reload(util)
        await ctx.send(f'Honk honk, util {name} has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def gitpull(self, ctx):
        """ Pulls the most recent version from the repository """

        response = os.popen('git pull').read()
        await ctx.send(embed=discord.Embed(
            title='Honk. Updating...',
            description=f'```diff\n{response}\n```',
            colour=self.bot.config.colour,
        ))
        
def setup(bot):
    bot.add_cog(Debug(bot))
