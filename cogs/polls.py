import emoji

from discord.ext import commands
from utils import language

class Polls(commands.Cog):
    """Commands for creating polls."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Event that happens once the bot has started."""

        # Define memory variables.
        if 'polls' not in self.bot.memory:
            self.bot.memory['polls'] = {}
            self.bot.memory['polls.pending'] = []

            # Store values in memory.
            for guild in await self.bot.db.fetch("SELECT guild_id, value FROM guild_settings WHERE key = 'polls.channel' AND value != ''"):
                if guild['guild_id'] in [guild.id for guild in self.bot.guilds]:
                    self.bot.memory['polls'][guild['guild_id']] = guild['value']

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Ignore non-guild.
        if message.guild is None:
            return

        # Ignore the poll command, it's triggered first before this event so we have to do this.
        # Also ignore message by the bot, we don't want a loop, and ignore if private message.
        prefix = self.bot.config.prefix
        if message.content.lower() == f'{prefix}poll' or message.author.bot or message.guild is None:
            return

        # Declare some variables.
        key = f'{message.guild.id}_{message.channel.id}_{message.author.id}'
        isPollChannel = False

        # Check if the user used the !poll command before.
        if key not in self.bot.memory['polls.pending']:

            # Check if the message is posted in the polls channel, if not, return.
            if message.guild.id not in self.bot.memory['polls'] or int(self.bot.memory['polls'][message.guild.id]) != message.channel.id:
                return

            # It's the poll channel, set the boolean.
            isPollChannel = True

        # It's a poll, if we got through by using !poll command then let's first remove the key.
        else:
            self.bot.memory['polls.pending'].remove(key)

        # Get all the emoji's in the message and declare an integer to track how many reactions we did.
        emojis = ''.join(c for c in message.content if c in emoji.UNICODE_EMOJI['en'])
        reactions = 0

        # Now let's loop through all the options to check if they are present, if so, react with it.
        for em in emojis:
            await message.add_reaction(em)
            reactions += 1

            # Discord only allows 20 reactions to a single post, so when we hit that mark make a new post for continuation.
            if reactions % 20 == 0:
                message = await message.channel.send(await language.get(self, None, 'polls.continuation', message.guild.id))

        # Now if it's in the poll channel, let's make sure we have at least an option, if not inform and remove it...
        if isPollChannel and reactions < 1:
            msg = await language.get(self, None, 'polls.not_a_poll', message.guild.id)
            await message.channel.send(msg.format(message.author.mention), delete_after=10)
            await message.delete()

    @commands.command()
    @commands.guild_only()
    async def poll(self, ctx):
        """Start a poll in any channel if allowed."""

        # Create an unique key and set it in the memory.
        key = f'{ctx.guild.id}_{ctx.channel.id}_{ctx.author.id}'
        self.bot.memory['polls.pending'].append(key)

        # Send the message that removes itself after 10 seconds to confirm the action, and the delete one of the user.
        if ctx.prefix is self.bot.config.prefix:
            await ctx.send(await language.get(self, ctx, 'polls.next_post'), delete_after=10)
            await ctx.message.delete()
        else:
            await ctx.send(await language.get(self, ctx, 'polls.next_post'))

def setup(bot):
    bot.add_cog(Polls(bot))
