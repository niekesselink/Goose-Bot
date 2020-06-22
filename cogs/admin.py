import discord

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
    async def language(self, ctx, lang):
        """"Set the language used in the guild."""

        # Is the guild in the memory?
        if ctx.guild.id not in self.bot.memory:
            self.bot.memory[ctx.guild.id] = {}

        # Now set in memory.
        self.bot.memory[ctx.guild.id]['language'] = lang

        # Now add it to the database.
        await self.bot.db.execute(f"INSERT INTO guild_settings (guild_id, key, value) VALUES ({ctx.guild.id}, 'language', '{lang}') "
                                  f"ON CONFLICT (guild_id, key) DO UPDATE SET value = '{lang}'")
         # Inform.
        message = await language.get(self, ctx.guild.id, 'admin.language')
        return await ctx.send(message.format(lang))

def setup(bot):
    bot.add_cog(Admin(bot))
