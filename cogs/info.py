import discord
import os
import psutil
import subprocess

from discord.ext import commands
from utils import embed, language

class Info(commands.Cog):
    """Information commands about the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Get reference to the current running process.
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def info(self, ctx):
        """Shows information about the Goose bot."""

        # Get some data...
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgMembers = round(len(self.bot.users) / len(self.bot.guilds))

        # Define embed fields data.
        fields = {
            'Creator': '<@462311999980961793>',
            'Servers active': f'{len(ctx.bot.guilds)} (avg: {avgMembers} users/server)',
            'Last update': f'{subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8")}',
            'RAM usage': f'{ramUsage:.2f} MB'
        }

        # Create and send the embed.
        await ctx.send(embed=embed.create(
            title=await language.get(ctx, 'info.title'),
            description=await language.get(ctx, 'info.description'),
            thumbnail=ctx.bot.user.avatar_url,
            fields=fields
        ))

    @commands.command()
    async def official(self, ctx):
        """Get an invite to the official server of Goose bot."""
        await ctx.send(await language.get(ctx, 'info.official') + '\nhttps://discord.gg/yVSDgUc')

    @commands.command()
    async def invite(self, ctx):
        """Get a link to invite the bot to your own server."""
        await ctx.send(await language.get(ctx, 'info.invite') + f'\n<{discord.utils.oauth_url(self.bot.user.id)}>')

    @commands.command()
    async def source(self, ctx):
        """Check out the bot's source code."""
        await ctx.send(await language.get(ctx, 'info.source') + '\nhttps://github.com/niekesselink/Goose-Bot')

def setup(bot):
    bot.add_cog(Info(bot))
