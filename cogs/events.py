import discord
import os

from datetime import datetime
from discord.ext import commands, tasks

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        # Create a variable for uptime of the bot.
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = datetime.utcnow()

        # Log that we have started and are running.
        self.bot.log(f'Bot has started.', 'Goose-Bot')

        # Now change the bot's status. An empty one is boring...
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):

        # Don't give an error if the command is non existing.
        if type(exception) == discord.ext.commands.errors.CommandNotFound:
            return

        # Cooldown on hidden commands are probably an easter egg, it should stay silent.
        if type(exception) == discord.ext.commands.errors.CommandOnCooldown and ctx.command.hidden:
            return

        # Send the error...
        await ctx.send(embed=discord.Embed(
            title='Oeps. A honking error...',
            description=f'`{str(exception)}`',
            colour=0xED5A40,
        ))
        
def setup(bot):
    bot.add_cog(Events(bot))
