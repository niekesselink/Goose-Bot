import discord
import os

from datetime import datetime
from discord.ext import commands
from utils import language

class Events(commands.Cog):
    """General event handler for the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that happens once the bot has started."""

        # But is running.
        print('Bot has started.')
        self.bot.uptime = datetime.utcnow()

        # Now change the bot's status. An empty one is boring...
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )
            
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Event that happens once the bot enters a guild."""

        # Add the guild and the members of said guild to the database.
        await self.bot.db.execute(f"INSERT INTO guilds (id) VALUES ({guild.id})")
        for member in guild.members:
            await self.bot.db.execute(f"INSERT INTO guild_members (guild_id ,id) VALUES ({guild.id}, {member.id})")

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        """Event that happens once the bot leaves a guild."""

        # Remove the guild from the database.
        await self.bot.db.execute(f"DELETE FROM guilds WHERE id = {guild.id}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event that happens once a member joins the guild the bot is in."""

        # Add the member to the database.
        await self.bot.db.execute(f"INSERT INTO guild_members (guild_id, id) VALUES ({member.guild.id}, {member.id}) ON CONFLICT (guild_id, id) DO NOTHING")

        # Get a welcome channel if it's set.
        raw_welcome_channel = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {member.guild.id} AND key = 'welcome.channel'")

        # If channel is set, get the channel and continue.
        if raw_welcome_channel:
            welcome_channel = member.guild.get_channel(int(raw_welcome_channel[0]['value']))

            # Getting a random welcome message, get the channel, format it, and send it.
            welcome_messages = await self.bot.db.fetch(f"SELECT text FROM welcomes WHERE guild_id = {member.guild.id} ORDER BY RANDOM() LIMIT 1")
            await welcome_channel.send(language.format(welcome_messages[0]['text']).format(member.mention))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event that happens once a member leaves the guild the bot is in."""

        # Remove member from the database.
        await self.bot.db.execute(f"DELETE FROM guild_members WHERE guild_id = {member.guild.id} AND id = {member.id}")

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
            return await ctx.send(await language.get(self, ctx, 'event.missing_argument'))

        # Notice if private message is not allowed for the command.
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(await language.get(self, ctx, 'event.no_private_message'))

        # We've hit an error. Inform that the owner is on it...
        await ctx.send(await language.get(self, ctx, 'event.error'))

        # Create a special error embed for this error and send it to the bot owner.
        owner = self.bot.get_user(462311999980961793)
        await owner.send(embed=discord.Embed(
            title=f'Error using {ctx.message.content}',
            description=f'`{str(error)}`',
            colour=0xFF7E62,
        ))
        
def setup(bot):
    bot.add_cog(Events(bot))
