import discord

from discord.ext import commands
from utils import data

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = data.getjson('config.json')

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Show who says what command
        print(f'{ctx.author} {ctx.message.clean_content}')

    @commands.Cog.listener()
    async def on_ready(self):
        # Notify on prompt
        print('Started!')

        # Change the name and status of the bot
        await self.bot.user.edit(username=self.config.username)
        await self.bot.change_presence(
            activity=discord.Game(type=3, name=self.config.playing),
            status=discord.Status.online
        )

def setup(bot):
    bot.add_cog(Events(bot))
