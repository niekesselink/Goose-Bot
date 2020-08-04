﻿import discord

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

        # Ignore the poll and setpollschannel command, it's triggered first before this event so we have to do this.
        # Also ignore message by the bot, we don't want a loop.
        prefix = self.bot.config.prefix
        if message.content.lower() == f'{prefix}poll' or message.content.lower() == f'{prefix}setpollschannel' or message.author == self.bot.user:
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

        # Integer to track if we have reacted with an option or not.
        reactions = 0

        # Time to react! There are two types of A, check if either of them is present and react with the regional one.
        if '🅰️' in message.content or '🇦' in message.content: 
            await message.add_reaction('🇦')
            reactions += 1

        # Same goes for the B, also two types of them.
        if '🅱️' in message.content or '🇧' in message.content: 
            await message.add_reaction('🇧')
            reactions += 1

        # Now let's loop through all the other options of which there are only one to check if they are present, if so, react with it.
        options = ['🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵', '🇶', '🇷', '🇸', '🇹', '🇺', '🇻', '🇼', '🇽', '🇾', '🇿']
        for option in options:
            if option in message.content:
                await message.add_reaction(option)
                reactions += 1

        # Now if it's in the poll channel, let's make sure we have at least two options, if not inform and remove it...
        if is_poll_channel and reactions < 2:
            msg = await language.get(self, None, 'polls.not_a_poll', message.guild.id)
            await message.channel.send(msg.format(message.author.mention), delete_after=10)
            await message.delete()

    @commands.command()
    async def poll(self, ctx):
        """Start a poll in any channel if allowed."""

        # Create an unique key and set it in the memory.
        key = f'{ctx.guild.id}_{ctx.channel.id}_{ctx.author.id}'
        self.bot.memory['polls']['pending'].append(key)

        # Send the message that removes itself after 10 seconds to confirm the action, and the delete one of the user.
        await ctx.send(await language.get(self, ctx, 'polls.next_post'), delete_after=10)
        await ctx.message.delete()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def setpollschannel(self, ctx):
        """Sets the current channel as the guild's channel for polls."""

        # Put it in the memory.
        self.bot.memory['polls'][ctx.guild.id] = ctx.channel.id

        # Also, put it in the database.
        await self.bot.db.execute(f"INSERT INTO guild_settings (guild_id, key, value) VALUES ({ctx.guild.id}, 'polls.channel', '{ctx.channel.id}') "
                                  f"ON CONFLICT (guild_id, key) DO UPDATE SET value = '{ctx.channel.id}'")

        # Inform and delete message!
        await ctx.send(await language.get(self, ctx, 'polls.set_channel'), delete_after=10)
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(Polls(bot))
