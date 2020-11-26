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

        # Get the right activity type.
        activityType = self.bot.config.activityType.lower()
        if activityType == "playing":
            activityType = discord.ActivityType.playing
        elif activityType == "streaming":
            activityType = discord.ActivityType.streaming
        elif activityType == "listening":
            activityType = discord.ActivityType.listening
        elif activityType == "watching":
            activityType = discord.ActivityType.watching
        elif activityType == "custom":
            activityType = discord.ActivityType.custom
        elif activityType == "competing":
            activityType = discord.ActivityType.competing

        # Check-double-check to ensure the type is not a string, if correct, go and change...
        if isinstance(activityType, str) is False:
            await self.bot.change_presence(
                activity=discord.Activity(type=activityType, name=self.bot.config.activityText),
                status=discord.Status.online
            )

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
            return await ctx.send(await language.get(self, ctx, 'events.missing_argument'))

        # Notice if private message is not allowed for the command.
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(await language.get(self, ctx, 'events.no_private_message'))

        # We've hit an error. Inform that the owner is on it...
        await ctx.send(await language.get(self, ctx, 'events.error'))

        # Create a special error embed for this error and send it to the bot owner.
        owner = self.bot.get_user(462311999980961793)
        await owner.send(embed=discord.Embed(
            title=f'Error using {ctx.message.content}',
            description=f'`{str(error)}`',
            colour=0xFF7E62,
        ))
            
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Event that happens once the bot enters a guild."""

        # Add the guild and the members of said guild to the database.
        await self.bot.db.execute(f"INSERT INTO guilds (id) VALUES ({guild.id})")
        for member in guild.members:
            await self.bot.db.execute(f"INSERT INTO guild_members (guild_id, id) VALUES ({guild.id}, {member.id})")

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

        # Send welcome message in case it's set...
        await self.send_welcome_or_bye_message(self, member, 'welcome')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event that happens once a member leaves the guild the bot is in."""

        # Remove member from the database.
        await self.bot.db.execute(f"DELETE FROM guild_members WHERE guild_id = {member.guild.id} AND id = {member.id}")

        # Send goodbye message in case it's set...
        await self.send_welcome_or_bye_message(self, member, 'bye')

    async def send_welcome_or_bye_message(self, member, event):
        """Function to send the proper welcome or bye message."""

        # Get the channel ID if it's set.
        channel_id = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {member.guild.id} AND key = 'events.{event}_channel'")

        # If channel is set, get the channel and continue.
        if channel_id:
            channel = member.guild.get_channel(int(channel_id[0]['value']))

            # Getting a random message, gformat it, and send it.
            messages = await self.bot.db.fetch(f"SELECT text FROM {event}s WHERE guild_id = {member.guild.id} ORDER BY RANDOM() LIMIT 1")
            await channel.send(language.fill(messages[0]['text'], member=member))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Press F to pay respect.
        if message.content.strip() == 'F':
            await message.add_reaction('🇫')
        
def setup(bot):
    bot.add_cog(Events(bot))
