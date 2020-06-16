import asyncpg
import datetime
import discord

from dateutil import parser
from discord.ext import commands, tasks
from utils import data, language

class Birthday(commands.Cog):
    """Feature to put a person who has his/her birthday on the spotlight."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Define looping task which checkes for birthdays.
        #self.check_birthday.add_exception_type(asyncpg.PostgresConnectionError)
        #self.check_birthday.start()

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        #self.check_birthday.cancel()

    @commands.command()
    async def birthday(self, ctx, input=None):
        """Set your birthday date, the format day/month is used."""

        # Check for value, if none then tell how to use this command.
        if input is None:
            return await ctx.send(await language.get(ctx, 'birthday.howto'))

        # Parse the given date and get guild timezone.
        date = parser.parse(input)
        timezone = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {ctx.guild.id} AND key = 'timezone'")

        # Make sure the timezone is an acutual value.
        if not timezone:
            timezone = 'CEST'
        else:
            timezone = timezone[0]['value']

        # Now add it to the database.
        await self.bot.db.execute(f"INSERT INTO birthdays (guild_id, member_id, birthday, timezone) VALUES ({ctx.guild.id}, {ctx.author.id}, '{date}', '{timezone}') "
                                  f"ON CONFLICT (guild_id, member_id) DO UPDATE SET birthday = '{date}', timezone = '{timezone}'")

        # Inform the user we've set the birthday.
        message = await language.get(ctx, 'birthday.succes')
        date_formatted = date.strftime(await language.get(ctx, 'birthday.format')).lower()
        await ctx.send(message.format(date_formatted, timezone))

    #@commands.command()
    #async def timezone(self, ctx, input=None):
    #    """Change the timezone of your current location."""

    #    # Check for input, if none explain the possible timezones.
    #    if input is None:
    #        return await ctx.send(await language.get(ctx, 'birthday.timezone'))

    #    # Check if user has set a birthday.
    #    birthday = await self.bot.db.fetch(f"SELECT birthday FROM birthdays WHERE guild_id = {ctx.guild.id} AND member_id = {ctx.author.id}")
    #    if not birthday:
    #        return await ctx.send(await language.get(ctx, 'birthday.notset'))

    #@tasks.loop(minutes=20)
    #async def check_birthday(self):
    #    """Function that loops to search the database for birthdays to give or remove."""

    #    # Get people who are having their birthday right now and don't have to role already.
    #    birthdays = f"SELECT member_id FROM birthdays WHERE birthday = date(timezone(timezone, NOW())) AND has_role = false"

    #    # Now loop through them.

    #    # Now also look for people who had their birthday yesterday.

    #    # Remove their birthday role if they still have it.

def setup(bot):
    bot.add_cog(Birthday(bot))
