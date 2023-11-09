import asyncio
import importlib
import json
import os
import psutil
import subprocess

from collections import namedtuple
from discord.ext import commands
from utils import embed

class Debug(commands.Cog):
    """Debug commands mainly for development/update purposes."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    def cog_load(self):
        """Event that happens once this cog gets loaded; it gets a reference to the bot process..."""
        self.process = psutil.Process(os.getpid())

    async def cog_check(self, ctx):
        """Validation check before every command within this class will be executed."""
        return await self.bot.is_owner(ctx.author)

    @commands.hybrid_group(hidden=True)
    async def debug(self, ctx: commands.Context):
        """Declaration of the debug category."""
        return

    #region Load/reload/unloads

    @debug.command()
    async def load(self, ctx: commands.Context, name: str):
        """Load a cog."""

        # Load the cog and sync new commands to enable slash.
        await self.bot.load_extension(f'cogs.{name}')
        await self.bot.tree.sync()

        # Inform the success...
        await ctx.send(f'Cogs.{name} has been loaded!')

    @debug.command()
    async def unload(self, ctx: commands.Context, name: str):
        """Unload a specific cog."""

        # Unload the cog and resync the slash commands.
        await self.bot.unload_extension(f'cogs.{name}')
        await self.bot.tree.sync()

        # Inform the success...
        await ctx.send('Cogs.{name} has been unloaded!')

    @debug.command()
    async def reload(self, ctx: commands.Context, name: str):
        """Reloads a specific cog."""

        # Just reload one if not 'all', do the same for slash tree...
        if name != 'all':
            await self.bot.reload_extension(f'cogs.{name}')
            await self.bot.tree.sync()

            # Inform the success and end here...
            return await ctx.send(f'Cogs.{name} has been reloaded!')

        # Reload all possible cogs which have been loaded.
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                await self.bot.reload_extension(f'cogs.{file[:-3]}')
                await ctx.send(f'Cogs.{file[:-3]} has been reloaded!')

        # Finally with all reloaded, sync commands to enable or disable new/old slash commands.
        await self.bot.tree.sync()

    @debug.command()
    async def reloadconfig(self, ctx: commands.Context):
        """Reloads the config.json file."""

        # Let's do the reload...
        with open('config.json', encoding='utf8') as data:
            self.bot.config = json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        # Inform completion.
        await ctx.send('Config reloaded!')

    @debug.command()
    async def reloadutil(self, ctx: commands.Context, name: str):
        """(Re)Load an util."""

        # Import it and inform...
        util = importlib.import_module(f'utils.{name}')
        importlib.reload(util)

        # Inform completion.
        await ctx.send(f'Util {name} has been (re)loaded!')

    #endregion

    #region Processes

    @debug.command()
    async def pull(self, ctx: commands.Context):
        """Pulls the most recent version from the repository."""

        # Start typing...
        async with ctx.channel.typing():

            # Execture "git pull" command in shell.
            stdout, stderr = await self.run_process('git pull')

            # Inform the report.
            await ctx.send(embed=embed.create(
                self,
                title='Git Pull',
                description=f'```diff\n{stdout}\n{stderr}\n```',
                colour=0x303136
            ))

    @debug.command()
    async def pip(self, ctx: commands.Context, name: str):
        """Updates a pip package."""

        # Start typing...
        async with ctx.channel.typing():

            # Run the pip command.
            stdout, stderr = await self.run_process(f'pip install --upgrade {name}')

            # Inform the report.
            await ctx.send(embed=embed.create(
                self,
                title='Pip Update',
                description=f'```diff\n{stdout}\n{stderr}\n```',
                colour=0x303136
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

    #endregion

    #region Misc

    @debug.command()
    async def ram(self, ctx: commands.Context):
        """Shows RAM usage of the bot."""
        ramUsage = self.process.memory_full_info().rss / 1024**2
        await ctx.send(f'{ramUsage:.2f} MB')

    @debug.command()
    async def ping(self, ctx: commands.Context):
        """Pong."""

        # Send the first message.
        msg = await ctx.send('...')

        # Now let's get the difference from when we created the message and when it was created on server.
        difference = msg.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)

        # Update previous message 
        await msg.edit(f'Pong! {miliseconds}')

    
    @debug.command()
    async def migrate(self, ctx: commands.Context):
        """Migrate the database to ensure it's up to date."""

        # Start typing...
        async with ctx.channel.typing():

            # Loop through the guilds.
            async for guild in self.bot.fetch_guilds():
                guild = self.bot.get_guild(guild.id)
                
                # Add the guild itself to the database.
                await self.bot.db.execute("INSERT INTO guilds (id) VALUES ($1) ON CONFLICT (id) DO UPDATE SET migrated = NOW()", guild.id)

                # Get config variables and add the default of it to the database if none present.
                with open('assets/json/settings.json') as content:
                    configs = json.load(content)
                    for config in configs:
                        await self.bot.db.execute("INSERT INTO guild_settings (guild_id, key, value) VALUES ($1, $2, $3) ON CONFLICT (guild_id, key) DO NOTHING", guild.id, config, configs[config])

                # Now loop through members and add them to the database.
                for member in guild.members:
                    await self.bot.db.execute("INSERT INTO guild_members (guild_id, id) VALUES ($1, $2) ON CONFLICT (guild_id, id) DO UPDATE SET migrated = NOW()", guild.id, member.id)

                # Inform process...
                await ctx.send(f'Guild ID **{guild.id}** complete.')

            # Inform completion.
            await ctx.send('Migration complete.')

    #endregion

async def setup(bot):
    await bot.add_cog(Debug(bot))
