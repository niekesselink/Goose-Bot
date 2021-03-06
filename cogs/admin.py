import discord
import json

from discord.ext import commands
from utils import language

class Admin(commands.Cog):
    """Commands for forming and using mention groups."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def admin(self, ctx):
        """Admin commands for the guild."""
        return

    @admin.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, *, data: str):
        """"Set a config variable for the current guild."""

        # Get the correct data from the message.
        data = data.split(' ', 1)
        config_name = data[0].lower()
        config_value = data[1].lower()

        # Get the Json array of possible settings.
        settings = {}
        with open('assets/json/settings.json', encoding='utf8') as data:
            settings = json.load(data)

        # Make sure the config_name is a valid one.
        matching_settings = [string for string in settings if config_name in string]
        if not matching_settings:
            message = await language.get(self, ctx, 'admin.config_unknown')
            return await ctx.send(message.format(config_name))

        # Language is set in memory, so here's a little hack fix for that.
        if config_name == 'language':

            # Is the guild in the memory? If not set it.
            if ctx.guild.id not in self.bot.memory:
                self.bot.memory[ctx.guild.id] = {}

            # Now set the config in memory.
            self.bot.memory[ctx.guild.id][config_name] = config_value

        # Now add it to the database.
        await self.bot.db.execute(f"INSERT INTO guild_settings (guild_id, key, value) VALUES ({ctx.guild.id}, '{config_name}', '{config_value}') "
                                  f"ON CONFLICT (guild_id, key) DO UPDATE SET value = '{config_value}'")

        # Inform.
        message = await language.get(self, ctx, 'admin.config')
        await ctx.send(message.format(config_name, config_value))

    @admin.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, *, data: str):
        """Change the status of the bot."""

        # For a non-fork, so Goose bot, only the real owner can do this..
        if self.bot.user.id == 672445557293187128 and self.bot.is_owner(ctx.author) is False:
            return ctx.send(await language.get(self, ctx, 'admin.status_not_allowed'))

        # Get the correct data from the message.
        data = data.split(' ', 1)
        activityType = data[0].lower()
        activityText = data[1]

        # Turn the type, which is a string now, into a discord object.
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

        # Check-double-check to ensure the type is not a string...
        if isinstance(activityType, str):
            return ctx.send(await language.get(self, ctx, 'admin.status_incorrect'))

        # Now change the bot's status. An empty one is boring...
        await self.bot.change_presence(
            activity=discord.Activity(type=activityType, name=activityText),
            status=discord.Status.online
        )

        # Add reaction to confirm it's done.
        await ctx.message.add_reaction('👍')

def setup(bot):
    bot.add_cog(Admin(bot))
