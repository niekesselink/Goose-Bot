import discord
import os
import psutil
import subprocess

from discord.ext import commands, tasks

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def info(self, ctx):
        """ Shows information about the Goose bot"""

        # Get some data...
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgMembers = round(len(self.bot.users) / len(self.bot.guilds))

        # Make an embed
        embed = discord.Embed(
            title='Goose',
            description=self.bot.config.description,
            colour=self.bot.get_colour(),
        )

        # Fill more info...
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.add_field(name='Creator', value='<@462311999980961793>', inline=False)
        embed.add_field(name='Servers active', value=f'{len(ctx.bot.guilds)} (avg: {avgMembers} users/server)', inline=False)
        embed.add_field(name='Last update', value=f'{subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8")}', inline=False)
        embed.add_field(name='RAM usage', value=f'{ramUsage:.2f} MB', inline=False)

        # Send the embed...
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx):
        """ Check out the bot's source code """

        # Just send a message with the GitHub page...
        await ctx.send(f'**HONK!** I am powered by this source code...\nhttps://github.com/niekesselink/Goose-Bot')

    @commands.command()
    async def invite(self, ctx):
        """ Get a link to invite the bot to your own server """

        # Just send a message with the invite link...
        await ctx.send(f'**HONK!** Use this URL to invite me!\n<{discord.utils.oauth_url(self.bot.user.id)}>')

def setup(bot):
    bot.add_cog(Info(bot))