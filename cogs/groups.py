import discord

from discord.ext import commands

class Groups(commands.Cog):
    """Commands for forming and using mention groups."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def groups(self, ctx, name=None):
        """Provide group name to mention the group."""

        if name is not None:
            ctx.send('Mentioning is a work in progress')

    @groups.command()
    async def list(self, ctx):
        """"Gives a list of groups."""
        return

    @groups.command()
    async def join(self, ctx):
        """"Join a group."""
        return

    @groups.command()
    async def leave(self, ctx):
        """"Leave a group you're in."""
        return

def setup(bot):
    bot.add_cog(Groups(bot))
