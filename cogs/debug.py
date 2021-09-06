import asyncio
import importlib
import json
import os
import psutil
import subprocess

from collections import namedtuple
from discord.ext import commands
from urllib.request import urlopen
from utils import embed, language, migrate

class Debug(commands.Cog):
    """Debug commands mainly for development/update purposes."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Get reference to the current running process.
        self.process = psutil.Process(os.getpid())

    async def cog_check(self, ctx):
        """Validation check before every command within this class will be executed."""
        return await self.bot.is_owner(ctx.author)

    @commands.group(hidden=True)
    async def debug(self, ctx):
        """Declaration of the debug category."""
        return

    @debug.command()
    async def ram(self, ctx):
        """Shows RAM usage of the bot."""
        
        # Get RAM info and return it in a simple message.
        ramUsage = self.process.memory_full_info().rss / 1024**2
        await ctx.send(f'{ramUsage:.2f} MB')

    @debug.command()
    async def ping(self, ctx):
        """Pong."""

        # Send the first message.
        msg = await ctx.send('...')

        # Now let's get the difference from when we created the message and when it was created on server.
        difference = msg.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)

        # Update previous message 
        await msg.edit(f'Pong! {miliseconds}')

    @debug.command()
    async def load(self, ctx, name):
        """Load a cog."""

        self.bot.load_extension(f'cogs.{name}')
        print(f'Cogs.{name} has been loaded!')
        message = await language.get(self, ctx, 'debug.cog_load')
        await ctx.send(content=message.format(name))

    @debug.command()
    async def unload(self, ctx, name):
        """Unload a specific cog."""

        self.bot.unload_extension(f'cogs.{name}')
        print(f'Cogs.{name} has been unloaded!')
        message = await language.get(self, ctx, 'debug.cog_unload')
        await ctx.send(content=message.format(name))

    @debug.command()
    async def reload(self, ctx, name):
        """Reloads a specific cog."""

        # Just reload one if not 'all'...
        if name != 'all':
            self.bot.reload_extension(f'cogs.{name}')
            print(f'Cogs.{name} has been reloaded!')
            message = await language.get(self, ctx, 'debug.cog_reload')
            return await ctx.send(content=message.format(name))

        # Reload all possible cogs which have been loaded...
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                self.bot.reload_extension(f'cogs.{file[:-3]}')
                print(f'Cogs.{file[:-3]} has been reloaded!')
                message = await language.get(self, ctx, 'debug.cog_reload')
                await ctx.send(content=message.format(file[:-3]))

    @debug.command()
    async def reloadslash(self, ctx):
        """Reloads the slash commands."""
        await ctx.channel.trigger_typing()
        await self.bot.register_application_commands()
        await ctx.send(await language.get(self, ctx, 'debug.reload_slash'))

    @debug.command()
    async def reloadconfig(self, ctx):
        """Reloads the config.json file."""

        # Let's do the reload...
        with open('config.json', encoding='utf8') as data:
            self.bot.config = json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        # Inform.
        await ctx.send(await language.get(self, ctx, 'debug.reload_config'))

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
    async def avatar(self, ctx, url):
        """Update profile image of the bot."""

        await self.bot.user.edit(avatar=urlopen(url).read())
        await ctx.send(await language.get(self, ctx, 'debug.avatar'))

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
            self,
            title=await language.get(self, ctx, 'debug.git_pull'),
            description=f'```diff\n{stdout}\n{stderr}\n```'
        ))

    @debug.command()
    async def update(self, ctx, name):
        """Updates a pip package."""

        # Start typing indicator.
        await ctx.channel.trigger_typing()

        # Execture command in shell...
        stdout, stderr = await self.run_process(f'pip3 install --upgrade {name}')

        # Inform the report.
        await ctx.send(embed=embed.create(
            self,
            title=await language.get(self, ctx, 'debug.update'),
            description=f'```diff\n{stdout}\n{stderr}\n```'
        ))

    @debug.command()
    async def eval(self, ctx, *args):
        """Execute Python code. Could be dangerous."""

        eval_string = " ".join(args)
        eval_result = eval(eval_string)
        await ctx.send(f"```py\n{eval_result}\n```")

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
