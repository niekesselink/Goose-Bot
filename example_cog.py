from discord.ext import commands
from utils import language

class Example(commands.Cog):
    """Example cog."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        """Pong."""
        await ctx.send(await language.get(self, ctx, 'example.pong'))

async def setup(bot):
    await bot.add_cog(Example(bot))
