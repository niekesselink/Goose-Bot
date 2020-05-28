import discord
import os

from datetime import datetime
from discord.ext import commands
from utils import data, language

class Events(commands.Cog):
    """General event handler for the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that happens once the bot has started."""

        # Let's sync all the guilds we're in to the database and set default language to English.
        for guild in self.bot.guilds:
            storage = await self.bot.redis.get_storage(guild)
            await storage.set('language', 'english')

        # But is running.
        print('Bot has started.')
        self.bot.uptime = datetime.utcnow()

        # Now change the bot's status. An empty one is boring...
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )
            
    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        """Event that happens once the bot leaves a guild."""

        # We're leaving, destroy guild data...
        redis = self.bot.redis.instance

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event that happens once an user joins the guild the bot is in."""
        return

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        """Event that happens once an user leaves the guild the bot is in."""
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Press F to pay respect.
        if message.content.strip() == 'F':
            await message.add_reaction('🇫')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Event that happens once a command runs into an error."""

        # Don't give an error if the command is non existing.
        if isinstance(error, commands.errors.CommandNotFound):
            return

        # Don't give an error either when the command check failed.
        if isinstance(error, commands.errors.CheckFailure):
            return

        # Cooldown on hidden commands are probably an easter egg, it should stay silent.
        if isinstance(error, commands.errors.CommandOnCooldown) and ctx.command.hidden:
            return

        # If the argument is missing, then let's say that...
        if isinstance(error, commands.errors.MissingRequiredArgument):
            message = await language.get(ctx, 'event.missingrequiredargument')
            return await ctx.send(message.format(ctx.message.author.mention))

        # Notice if private message is not allowed for the command.
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(await language.get(ctx, 'event.noprivatemessage'))

        # We've hit an error. Inform that the owner is on it...
        message = await language.get(ctx, 'event.error')
        await ctx.send(message.format(ctx.message.author.mention))

        # Create a special error embed for this error and send it to the bot owner.
        owner = self.bot.get_user(462311999980961793)
        await owner.send(embed=discord.Embed(
            title=f'Error using {ctx.message.content}',
            description=f'`{str(error)}`',
            colour=0xFF7E62,
        ))
        
def setup(bot):
    bot.add_cog(Events(bot))
