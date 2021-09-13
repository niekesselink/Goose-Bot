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

        # Check if user started streaming...
        live = False
        if after.activity:
            live = True if after.activity.type == discord.ActivityType.streaming else False

        # Check if user was streaming...
        was_live = False
        if before.activity:
            was_live = True if before.activity.type == discord.ActivityType.streaming else False

        # Now get the role ID and only continue if it's set if the user is or was live.
        if live or was_live:
            role_id = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = $2", after.guild.id, 'socials.streamer_role')
            if role_id[0]['value'] != '':

                # Add or remove the role...
                if live:
                    await after.add_roles(after.guild.get_role(int(role_id[0]['value'])))
                else:
                    await after.remove_roles(after.guild.get_role(int(role_id[0]['value'])))

def setup(bot):
    bot.add_cog(Socials(bot))
