import discord
import os
import subprocess

from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """ Shows information about the Goose bot"""

        # Just send a message
        await ctx.send('Honk honk. *Niek Esselink* made me. \n\n**Source:** https://github.com/niekesselink/goose-bot'
                       + '\n**Version:** ' + subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
                       + ' **Date:** ' + subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8"))

    @commands.command()
    async def honk(self, ctx):
        """ Honk! This is a response test """

        honk = await ctx.send('HONK!')
        difference = honk.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)
        await honk.edit(content=f'HONK HONK! `{miliseconds}ms`')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx, cog=None):
        """ Load a specific cog """

        self.bot.load(cog)
        await ctx.send(f"Honk honk, {cog} has been loaded!")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx, cog=None):
        """ Unload a specific cog """

        self.bot.unload(cog)
        await ctx.send(f"Honk honk, {cog} has been unloaded!")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx, cog):
        """ Reloads a specific cog """

        self.bot.reload(cog)
        await ctx.send(f"Honk honk, {cog} has been reloaded!")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def pull(self, ctx):
        """ Pulls the most recent version from the repository """

        response = os.popen("git pull").read()
        await ctx.send(embed=discord.Embed(
            title="Git pull...",
            description=f"```diff\n{response}\n```",
            colour=0x009688,
        ))

def setup(bot):
    bot.add_cog(General(bot))
