import discord

from discord.ext import commands

class Socials(commands.Cog):
    """Tracking of social media."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

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
