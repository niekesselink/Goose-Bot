import discord
import os

from datetime import datetime
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.log(ctx.message.clean_content, ctx.author.name)

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = datetime.utcnow()

        self.bot.log(f'Ready: {self.bot.user} | Guilds: {len(self.bot.guilds)}', 'Goose-Bot')

        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, exception):
        if type(exception) == discord.ext.commands.errors.CommandNotFound:
            return

        await ctx.send(embed=discord.Embed(
            title='Oeps. A honking error...',
            description=f'`{str(exception)}`',
            colour=0xFF0000,
        ))
        
def setup(bot):
    bot.add_cog(Events(bot))
