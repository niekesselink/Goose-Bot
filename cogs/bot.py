import discord
import subprocess

from discord.ext import commands

class Bot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Shows information about the bot')
    async def info(self, ctx):
        # Just send a message
        await ctx.send('Honk honk. *Niek Esselink* made this shit. \n\n**Source:** https://github.com/niekesselink/goose-bot'
                       + '\n**Version:** ' + subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
                       + ' **Date:** ' + subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8"))

    @commands.command(brief='Changes the playing status of the bot')
    async def status(self, ctx, text: str):
        # Change the playing status to something that we want
        await self.bot.change_presence(
            activity=discord.Game(type=3, name=text),
            status=discord.Status.online
        )

def setup(bot):
    bot.add_cog(Bot(bot))