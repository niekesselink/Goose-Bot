import asyncio
import discord
import importlib
import os
import subprocess

from discord.ext import commands, tasks
from utils import embed, json

class Debug(commands.Cog):
    """Debug commands mainly for development/update purposes."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(hidden=True)
    async def debug(self, ctx):
        return

    @debug.command()
    async def honk(self, ctx):
        """Latency test command."""

        # Send the first message.
        honk = await ctx.send('HONK!')

        # Now let's get the difference from when we created the message and when it was created on server.
        difference = honk.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)

        # Update previous message with the difference.
        await honk.edit(content=f'**HONK HONK!** `{miliseconds}ms`')

    @debug.command()
    async def load(self, ctx, name):
        """Load a cog."""

        self.bot.load_extension(f'cogs.{name}')
        await ctx.send(f'**Honk!** Cog {name} has been loaded!')

    @debug.command()
    async def unload(self, ctx, name):
        """Unload a specific cog."""

        self.bot.unload_extension(f'cogs.{name}')
        await ctx.send(f'**Honk!** Cog {name} has been unloaded!')

    @debug.command()
    async def reload(self, ctx, name):
        """Reloads a specific cog."""

        # Just reload one if not 'all'...
        if name != 'all':
            self.bot.reload_extension(f'cogs.{name}')
            return await ctx.send(f'**Honk!** Cog {name} has been reloaded!')

        # Reload all possible cogs which have been loaded...
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                cog = file[:-3]
                try:
                    self.bot.reload_extension(f'cogs.{cog}')
                    await ctx.send(f'**Honk!** Cog {cog} has been reloaded!')
                except:
                    pass

    @debug.command()
    async def importutil(self, ctx, name):
        """Imports an util."""

        util = importlib.import_module(f'utils.{name}')
        importlib.reload(util)
        await ctx.send(f'**Honk!** Util {name} has been (re)imported!')

    @debug.command()
    async def pull(self, ctx):
        """Pulls the most recent version from the repository."""

        # Execture "git pull" command in shell...
        async with ctx.typing():
            stdout, stderr = await self.run_process('git pull')

        # Inform the report.
        await ctx.send(embed=embed.create(
            title='**Honk.** Git pulling...',
            description=f'```diff\n{stdout}\n{stderr}\n```'
        ))

    # Function for running progams on the VPS.
    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        # Return the output.
        return [output.decode() for output in result]
        
def setup(bot):
    bot.add_cog(Debug(bot))
