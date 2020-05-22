import discord
import os

from datetime import datetime
from discord.ext import commands, tasks

class Events(commands.Cog):
    """General event handler for the bot."""

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
    async def on_guild_join(self, guild):

        # Reset out status so it's shown everywhere...
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        # Don't give an error if the command is non existing.
        if isinstance(error, commands.errors.CommandNotFound):
            return

        # Cooldown on hidden commands are probably an easter egg, it should stay silent.
        if isinstance(error, commands.errors.CommandOnCooldown) and ctx.command.hidden:
            return

        # If the argument is missing, then let's say that...
        if isinstance(error, commands.errors.MissingRequiredArgument):
            return await ctx.send(f'**Honk!** You\'re using this command incorrect {ctx.message.author.mention}, an argument is missing.')

        # Notice if private message is not allowed for the command.
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send('**Honk!** This command cannot be used in private message.')

        # We've hit an error. Inform that the owner is on it...
        await ctx.author.send(f'**Honk!** An error has occured. The owner has been notified and this will be fixed soon, thanks for being a crash-dummy {ctx.message.author.mention}!')

        # Create an embed for this error and send it to the bot owner.
        owner = self.bot.get_user(462311999980961793)
        await owner.send(embed=discord.Embed(
            title='Error by {ctx.message.author.mention} using {ctx.message.content}...',
            description=f'`{str(error)}`',
            colour=0xFF7E62,
        ))
        
def setup(bot):
    bot.add_cog(Events(bot))
