import discord
import requests

from discord.ext import commands, tasks
from utils import embed

class Socials(commands.Cog):
    """Tracking of social media."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    def cog_load(self):
        """Event that happens once this cog gets loaded."""
        self.check_socials.start()

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        self.check_socials.cancel()

    @tasks.loop(minutes=3.0)
    async def check_socials(self):
        """Loop to check the social post status and post a new one if there is a new one."""

        # Get all the socials we need to check and loop through them.
        socials = await self.bot.db.fetch("SELECT guild_id, channel_id, social, handle, last, text FROM socials")
        for social in socials:
            
            # Ensure we got a guild...
            guild = self.bot.get_guild(social['guild_id'])
            if guild is None:
                continue

            # Also ensure we got a channel...
            channel = guild.get_channel(social['channel_id'])
            if channel is None:
                continue

            # Now let's go and check the actual social media itself.
            if social['social'] == 'instagram':
                await self.instagram(channel, social)

    async def instagram(self, channel, social):
        """Checks Instagram to see if latest post has been posted."""

        # Declare some variables...
        response = None
        headers = {
            "Host": "www.instagram.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
        }

        # Try and get data from Instagram.
        try:
            response = requests.get(f"https://www.instagram.com/{social['handle']}/feed/?__a=1&__d=dis", headers=headers)
            response = response.json()["graphql"]["user"]
        except:
            return

        # Get latest image posted on Instagram and check if we posted that in Discord, if so, return...
        last_on_instagram = response['edge_owner_to_timeline_media']['edges'][0]['node']
        if last_on_instagram['shortcode'] == social['last']:
            return

        # Update the last field as we're going to post.
        await self.bot.db.execute("UPDATE socials SET last = $1 WHERE guild_id = $2 AND channel_id = $3 AND handle = $4",
                                  last_on_instagram['shortcode'], channel.guild.id, channel.id, social['handle'])

        # Send embed.
        embed = discord.Embed(title='',
                              description=last_on_instagram['edge_media_to_caption']['edges'][0]['node']['text'],
                              color=0x303136)
        embed.set_author(name=f"{response['full_name']} ({social['handle']})",
                         url=f"https://www.instagram.com/{social['handle']}/",
                         icon_url=response["profile_pic_url"])
        embed.set_image(url=last_on_instagram['display_url'])
        await channel.send(f"{social['text']}\nhttps://www.instagram.com/p/{last_on_instagram['shortcode']}/", embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        """Checks if user starts streaming and awards a role if set in a guild."""

        # Get proper variables.
        is_live = any([isinstance(a, discord.Streaming) for a in after.activities])
        was_live = any([isinstance(a, discord.Streaming) for a in before.activities])

        # Skip if still live, or was never live...
        if is_live == was_live:
            return

        # Now get the role ID and only continue if it's set if the user is or was live.
        role_id = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = $2", after.guild.id, 'socials.streamer_role')
        if role_id[0]['value'] != '':

            # Add or remove the role...
            if is_live:
                await after.add_roles(after.guild.get_role(int(role_id[0]['value'])))
            elif was_live:
                await after.remove_roles(after.guild.get_role(int(role_id[0]['value'])))



async def setup(bot):
    await bot.add_cog(Socials(bot))
