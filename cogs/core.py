import discord
import json

from datetime import datetime
from discord.ext import commands
from utils import language

class Core(commands.Cog):
    """General event handler for the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that happens once the bot has started."""

        # Wait untill ready. Wait what?
        await self.bot.wait_until_ready()

        # But is running.
        print('Bot has started.')
        self.bot.uptime = datetime.utcnow()

        # Remove legacy help command, for now it's broken.
        self.bot.remove_command('help')

        # Sync commands to enable or disable new/old slash commands.
        await self.bot.tree.sync()

        # Set a status if type and content are set.
        if self.bot.config.activityType is not '' and self.bot.config.activityText is not '':
            
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
            return await ctx.send(await language.get(self, ctx, 'core.incorrect_usage'))

        # Notice if private message is not allowed for the command.
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.author.send(await language.get(self, ctx, 'core.no_private_message'))

        # Create an error message with what went wrong...
        error_msg = discord.Embed(
            description=f'**{ctx.message.content}**\n`{str(error)}`',
            colour=0xFF0000
        )

        # If we're in debug, show the error message in the chat where it happened and end here.
        if (self.bot.config.debug == '1'):
            return await ctx.send(embed=error_msg)

        # Not in debug, send full message to the bot owner and just a generic one to the channel.
        owner = self.bot.get_user(462311999980961793)
        await owner.send(embed=error_msg)
        await ctx.send(embed=discord.Embed(
            description=await language.get(self, ctx, 'core.error'),
            colour=0xFF0000
        ))
            
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Event that happens once the bot enters a guild."""

        # Add the guild to the database.
        await self.bot.db.execute("INSERT INTO guilds (id) VALUES ($1)", guild.id)

        # Now add the configs and their default to the database.
        with open('assets/json/settings.json') as content:
            configs = json.load(content)
            for config in configs:
                await self.bot.db.execute("INSERT INTO guild_settings (guild_id, key, value) VALUES ($1, $2, $3)", guild.id, config, configs[config])

        # Finally, add a list of all members to be used further into the bot's features.
        for member in guild.members:
            await self.bot.db.execute("INSERT INTO guild_members (guild_id, id) VALUES ($1, $2)", guild.id, member.id)

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        """Event that happens once the bot leaves a guild."""
        await self.bot.db.execute("DELETE FROM guilds WHERE id = $1", guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event that happens once a member joins the guild the bot is in."""
        await self.bot.db.execute("INSERT INTO guild_members (guild_id, id) VALUES ($1, $2)", member.guild.id, member.id)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload):
        """Event that happens once a member leaves the guild the bot is in."""
        await self.bot.db.execute("DELETE FROM guild_members WHERE guild_id = $1 AND id = $2", payload.guild_id, payload.user.id)

async def setup(bot):
    await bot.add_cog(Core(bot))
