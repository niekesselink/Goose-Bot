from discord.ext import commands
from utils import language

class Counting(commands.Cog):
    """Cog to set a counting channel, and well, count."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    async def cog_load(self):
        """Event that happens once this cog gets loaded."""

        # Define memory variables.
        if 'polls' not in self.bot.memory:
            self.bot.memory['counting'] = {}

            # Store values in memory.
            guilds = [guild async for guild in self.bot.fetch_guilds()]
            for guild in await self.bot.db.fetch("SELECT guild_id, value FROM guild_settings WHERE key = 'counting.channel' AND value != ''"):
                if guild['guild_id'] in [guild.id for guild in guilds]:
                    self.bot.memory['counting'][guild['guild_id']] = guild['value']

    @commands.hybrid_group(hidden=True)
    @commands.has_permissions(administrator=True)
    async def counting(self, ctx):
        """Counting function commands for the guild."""
        return

    @counting.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def start(self, ctx: commands.Context):
        """Start a couting in this channel."""

    @counting.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def stop(self, ctx: commands.Context):
        """Stop the counting in this channel."""

    @counting.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx: commands.Context):
        """Set the count of this channel to a certain value."""

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Ignore non-guild.
        if message.guild is None:
            return

        # Are we in a counting channel?
        if message.guild.id not in self.bot.memory['counting'] or int(self.bot.memory['counting'][message.guild.id]) != message.channel.id:
            return
        
async def setup(bot):
    await bot.add_cog(Counting(bot))
