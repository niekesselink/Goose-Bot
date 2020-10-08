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

def setup(bot):
    bot.add_cog(Admin(bot))
