from discord.ext import commands
from utils import language

class AutoDelete(commands.Cog):
    """Autodelete functionality and its commands."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that happens once the bot has started."""

        # Define memory variables.
        if 'autodelete' not in self.bot.memory:
            self.bot.memory['autodelete'] = {}

            # Store values in memory.
            for values in await self.bot.db.fetch("SELECT guild_id, channel_id, delay FROM autodelete"):
                if values['guild_id'] in [guild.id for guild in self.bot.guilds]:

                    # First add guild if not present yet...
                    if values['guild_id'] not in self.bot.memory['autodelete']:
                        self.bot.memory['autodelete'][values['guild_id']] = {}

                    # Now add the config.
                    self.bot.memory['autodelete'][values['guild_id']].update({ values['channel_id']: values['delay'] })

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def autodelete(self, ctx, delay):
        """Add or remove a channel from the autodelete."""

        # In case the keyword is none, then remove the channel from autodelete.
        if delay == 'none':
            if ctx.guild.id in self.bot.memory['autodelete']:
                self.bot.memory['autodelete'][ctx.guild.id].pop(ctx.channel.id)
                await self.bot.db.execute("DELETE FROM autodelete WHERE guild_id = $1 AND channel_id = $2", ctx.guild.id, ctx.channel.id)

            # Inform deletion.
            return await ctx.send(await language.get(self, ctx, 'autodelete.disabled'))

        # Try to convert the input to seconds...
        value = 0
        try:
            seconds_per_unit = { 's': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800 }
            value = int(delay[:-1]) * seconds_per_unit[delay[-1]]
        except:
            return await ctx.send(await language.get(self, ctx, 'autodelete.incorrect'))

        # If it's 0, then it still incorrect regardless of the catch. Abort.
        if value == 0:
            return await ctx.send(await language.get(self, ctx, 'autodelete.incorrect'))

        # Make sure the guild is in memory.
        if ctx.guild.id not in self.bot.memory['autodelete']:
            self.bot.memory['autodelete'][ctx.guild.id] = {}

        # Insert into the memory, as well as the database.
        self.bot.memory['autodelete'][ctx.guild.id].update({ ctx.channel.id: value })
        await self.bot.db.execute("INSERT INTO autodelete (guild_id, channel_id, delay) VALUES ($1, $2, $3) "
                                  "ON CONFLICT (guild_id, channel_id) DO UPDATE SET delay = $3", ctx.guild.id, ctx.channel.id, value)

        # Now, finally, inform success.
        await ctx.send(await language.get(self, ctx, 'autodelete.enabled'))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Ignore non-guild.
        if message.guild is None:
            return

        # Now, if the channel is in autodelete, then apply the delete command with set interval.
        if message.guild.id in self.bot.memory['autodelete'] and message.channel.id in self.bot.memory['autodelete'][message.guild.id]:
            await message.delete(delay=self.bot.memory['autodelete'][message.guild.id][message.channel.id])

def setup(bot):
    bot.add_cog(AutoDelete(bot))
