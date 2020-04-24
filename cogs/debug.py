import discord
import os

from discord.ext import commands, tasks
from utils import data

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(hidden=True)
    async def debug(self, ctx):
        return

    @debug.command(hidden=True)
    async def honk(self, ctx):

        # Send the first message.
        honk = await ctx.send('HONK!')

        # Now let's get the difference from when we created the message and when it was created on server.
        difference = honk.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)

        # Update previous message with the difference.
        await honk.edit(content=f'**HONK HONK!** `{miliseconds}ms`')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def loadcog(self, ctx, name):
        """ Load a specific cog """

        self.bot.load_extension(f"cogs.{name}")
        await ctx.send(f'Honk, cog {name} has been loaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def unloadcog(self, ctx, name):
        """ Unload a specific cog """

        self.bot.unload_extension(f"cogs.{name}")
        await ctx.send(f'Honk, cog {name} has been unloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadcog(self, ctx, name):
        """ Reloads a specific cog """

        # Make it possible to reload all of the cogs that are loaded..
        if name == 'all':
            for file in os.listdir('cogs'):
                if file.endswith('.py'):
                    cog = file[:-3]
                    try:
                        self.bot.reload_extension(f'cogs.{cog}')
                        await ctx.send(f'Honk, cog {cog} has been reloaded!')
                    except:
                        # Probably unloaded for a reason... ignore.
                        pass
        else:
            # Just reload one...
            self.bot.reload_extension(f"cogs.{name}")
            await ctx.send(f'Honk, cog {name} has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadconfig(self, ctx):
        """ Reloads the config.json """

        self.bot.config = data.getjson('config.json')
        await ctx.send(f'Honk, config.json has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def reloadutil(self, ctx, name: str):
        """ Reloads an util module. """

        util = importlib.import_module(f"utils.{name}")
        importlib.reload(util)
        await ctx.send(f'Honk, util {name} has been reloaded!')

    @commands.is_owner()
    @debug.command(hidden=True)
    async def gitpull(self, ctx):
        """ Pulls the most recent version from the repository """

        # Execture "git pull" command in shell...
        response = os.popen('git pull').read()

        # Inform the report.
        await ctx.send(embed=discord.Embed(
            title='Honk. Updating...',
            description=f'```diff\n{response}\n```',
            colour=self.bot.get_colour(),
        ))
        
def setup(bot):
    bot.add_cog(Debug(bot))
