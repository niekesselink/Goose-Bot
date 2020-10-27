import asyncio
import discord
import importlib
import os
import subprocess

from discord.ext import commands
from utils import embed, language, migrate

class Debug(commands.Cog):
    """Debug commands mainly for development/update purposes."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    async def cog_check(self, ctx):
        """Validation check before every command within this class will be executed."""
        return await self.bot.is_owner(ctx.author)

    @commands.group(hidden=True)
    async def debug(self, ctx):
        """Declaration of the debug category."""
        return

    @debug.command()
    async def load(self, ctx, name):
        """Load a cog."""

        self.bot.load_extension(f'cogs.{name}')
        print(f'Cog {name} has been loaded!')
        message = await language.get(self, ctx, 'debug.cog_load')
        await ctx.send(content=message.format(name))

    @debug.command()
    async def unload(self, ctx, name):
        """Unload a specific cog."""

        self.bot.unload_extension(f'cogs.{name}')
        print(f'Cog {name} has been unloaded!')
        message = await language.get(self, ctx, 'debug.cog_unload')
        await ctx.send(content=message.format(name))

    @debug.command()
    async def reload(self, ctx, name):
        """Reloads a specific cog."""

        # Just reload one if not 'all'...
        if name != 'all':
            self.bot.reload_extension(f'cogs.{name}')
            print(f'Cog {name} has been reloaded!')
            message = await language.get(self, ctx, 'debug.cog_reload')
            return await ctx.send(content=message.format(name))

        # Reload all possible cogs which have been loaded...
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                cog = file[:-3]
                try:
                    self.bot.reload_extension(f'cogs.{cog}')
                    print(f'Cog {cog} has been reloaded!')
                    message = await language.get(self, ctx, 'debug.cog_reload')
                    await ctx.send(content=message.format(cog))
                except:
                    pass

    @debug.command()
    async def reloadutil(self, ctx, name):
        """(Re)Load an util."""

        # Import it...
        util = importlib.import_module(f'utils.{name}')
        importlib.reload(util)

        # Inform...
        print(f'Util {name} has been (re)loaded!')
        message = await language.get(self, ctx, 'debug.reload_util')
        await ctx.send(content=message.format(name))

    @debug.command()
    async def migrate(self, ctx):
        """Migrate the database to ensure it's up to date."""

        # Migration code.
        await migrate.go(self.bot)
        await ctx.send(await language.get(self, ctx, 'debug.migrate'))

    @debug.command()
    async def pull(self, ctx):
        """Pulls the most recent version from the repository."""

        # Start typing indicator.
        await ctx.channel.trigger_typing()

        # Execture "git pull" command in shell...
        stdout, stderr = await self.run_process('git pull')

        # Inform the report.
        await ctx.send(embed=embed.create(
            title=await language.get(self, ctx, 'debug.git_pull'),
            description=f'```diff\n{stdout}\n{stderr}\n```'
        ))

    @debug.command()
    async def updateapp(self, ctx, name):
        """Pulls the most recent version from the repository."""

        # Start typing indicator.
        await ctx.channel.trigger_typing()

        # Execture "git pull" command in shell...
        stdout, stderr = await self.run_process(f'apt-get --only-upgrade install {name}')

        # Inform the report.
        await ctx.send(embed=embed.create(
            title=await language.get(self, ctx, 'debug.update_app'),
            description=f'```diff\n{stdout}\n{stderr}\n```'
        ))

    async def run_process(self, command):
        """Function for running progams on the VPS."""

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
