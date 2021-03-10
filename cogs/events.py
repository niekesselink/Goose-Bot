import discord

from discord.ext import commands
from utils import language

class Events(commands.Cog):
    """General event handler for the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event that happens once a member joins the guild the bot is in."""
        await self.send_event_message(member, 'welcome')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event that happens once a member leaves the guild the bot is in."""
        await self.send_event_message(member, 'bye')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Event that happens when a member gets updated."""

        # Check if user boosted the server, if so, send a message.
        if before.premium_since is None and after.premium_since is not None:
            await self.send_event_message(after, 'boost')

    async def send_event_message(self, member, event):
        """Function to send the proper welcome or bye message."""

        # Get the channel ID and only continue if it's set.
        channel_id = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = $2", member.guild.id, f'events.{event}_channel')
        if channel_id[0]['value'] != '':
            channel = member.guild.get_channel(int(channel_id[0]['value']))

            # Getting a random message, again, only continue and send it if it is set.
            query = f"SELECT text FROM 'event_{event}s' WHERE guild_id = $1 ORDER BY RANDOM() LIMIT 1"
            message = await self.bot.db.fetch(query, member.guild.id)
            if message:
                await channel.send(language.fill(message[0]['text'], member=member))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Press F to pay respect.
        if message.content.strip() == 'F':
            return await message.add_reaction('🇫')

def setup(bot):
    bot.add_cog(Events(bot))
