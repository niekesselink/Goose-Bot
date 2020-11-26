import discord

from discord.ext import commands
from utils import language

class Polls(commands.Cog):
    """Commands for creating polls."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Define memory variables...
        if 'polls' not in self.bot.memory:
            self.bot.memory['polls'] = {}
            self.bot.memory['polls']['pending'] = []

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Ignore the poll command, it's triggered first before this event so we have to do this.
        # Also ignore message by the bot, we don't want a loop, and ignore if private message.
        prefix = self.bot.config.prefix
        if message.content.lower() == f'{prefix}poll' or message.author.bot or message.guild is False:
            return

        # Declare some variables.
        key = f'{message.guild.id}_{message.channel.id}_{message.author.id}'
        is_poll_channel = False

        # Check if the user used the !poll command before.
        if key not in self.bot.memory['polls']['pending']:

            # Is the polls channel set in the memory? If not, get it from the database.
            if message.guild.id not in self.bot.memory['polls']:
                channel_id = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {message.guild.id} AND key = 'polls.channel'")
                self.bot.memory['polls'][message.guild.id] = int(channel_id[0]['value']) if channel_id else 0

            # Check if the message is posted in the polls channel, if not, return.
            if self.bot.memory['polls'][message.guild.id] != message.channel.id:
                return

            # It's the poll channel, set the boolean.
            is_poll_channel = True

        # It's a poll, if we got through by using !poll command then let's first remove the key.
        else:
            self.bot.memory['polls']['pending'].remove(key)

        # Put content of the message in a variable and declare an integer to track how many reactions we did.
        content = message.content
        reactions = 0

        # Time to react! There are two types of A, check if either of them is present and react with the regional one.
        if '🅰️' in message.content or '🇦' in content: 
            await message.add_reaction('🇦')
            reactions += 1

        # Same goes for the B, also two types of them.
        if '🅱️' in message.content or '🇧' in content: 
            await message.add_reaction('🇧')
            reactions += 1

        # Declare the rest of the options.
        options = [
            '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', '🇺', '🇻', '🇼', '🇽', '🇾', '🇿',
            '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
        ]

        # Now let's loop through all the options to check if they are present, if so, react with it.
        for option in options:
            if option in content:
                await message.add_reaction(option)
                reactions += 1

                # Discord only allows 20 reactions to a single post, so when we hit that mark make a new post for continuation.
                if reactions % 20 == 0:
                    message = await message.channel.send(await language.get(self, None, 'polls.continuation', message.guild.id))

        # Now if it's in the poll channel, let's make sure we have at least two options, if not inform and remove it...
        if is_poll_channel and reactions < 2:
            msg = await language.get(self, None, 'polls.not_a_poll', message.guild.id)
            await message.channel.send(msg.format(message.author.mention), delete_after=10)
            await message.delete()

    @commands.command()
    @commands.guild_only()
    async def poll(self, ctx):
        """Start a poll in any channel if allowed."""

        # Create an unique key and set it in the memory.
        key = f'{ctx.guild.id}_{ctx.channel.id}_{ctx.author.id}'
        self.bot.memory['polls']['pending'].append(key)

        # Send the message that removes itself after 10 seconds to confirm the action, and the delete one of the user.
        await ctx.send(await language.get(self, ctx, 'polls.next_post'), delete_after=10)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Polls(bot))
