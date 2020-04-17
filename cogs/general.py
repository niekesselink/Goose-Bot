import discord
import subprocess

from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """ Shows information about the Goose bot"""

        # Just send a message
        await ctx.send('Honk honk, *Niek Esselink* made me. \n\n**Source:** https://github.com/niekesselink/goose-bot'
                       + '\n**Version:** ' + subprocess.check_output(["git", "describe", "--always"]).strip().decode("utf-8")
                       + ' **Date:** ' + subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8"))

    @commands.command()
    async def honk(self, ctx):
        """ Honk! This is a response test """

        honk = await ctx.send('HONK!')
        difference = honk.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)
        await honk.edit(content=f'*HONK HONK!* `{miliseconds}ms`')

def setup(bot):
    bot.add_cog(General(bot))
