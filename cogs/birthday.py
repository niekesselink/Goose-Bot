import asyncpg
import datetime
import discord
import json

from dateutil import parser
from discord.ext import commands, tasks
from utils import language

class Birthday(commands.Cog):
    """Feature to put a person who has his/her birthday on the spotlight."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot
        self.check_birthday.start()

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        self.check_birthday.cancel()

    @commands.command()
    async def birthday(self, ctx, *, birthday: str=None):
        """Set your birthday date, the format day/month is used."""

        # Check for value, if none then tell how to use this command.
        if birthday is None:
            return await ctx.send(await language.get(self, ctx, 'birthday.how_to'))

        # Parse the given date and get guild timezone, return error if something is not working.
        try:
            date = parser.parse(birthday)
        except:
            return await ctx.send(await language.get(self, ctx, 'birthday.incorrect'))

        # Get guild timezone and ensure we have something...
        timezone = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {ctx.guild.id} AND key = 'timezone'")
        if not timezone:
            timezone = 'CEST'
        else:
            timezone = timezone[0]['value']

        # Now add it to the database.
        await self.bot.db.execute(f"INSERT INTO birthdays (guild_id, member_id, birthday, timezone) VALUES ({ctx.guild.id}, {ctx.author.id}, '{date}', '{timezone}') "
                                  f"ON CONFLICT (guild_id, member_id) DO UPDATE SET birthday = '{date}', timezone = '{timezone}'")

        # Inform the user we've set the birthday.
        message = await language.get(self, ctx, 'birthday.succes')
        date_formatted = date.strftime(await language.get(self, ctx, 'birthday.format')).lower()
        await ctx.send(message.format(date_formatted, timezone))

    @commands.command()
    async def timezone(self, ctx, *, timezone: str=None):
        """Change the timezone of your current location."""

        # Check for input, if none explain the possible timezones.
        if timezone is None:
            return await ctx.send(await language.get(self, ctx, 'birthday.timezone'))

        # Check if user has set a birthday.
        birthday = await self.bot.db.fetch(f"SELECT birthday FROM birthdays WHERE guild_id = {ctx.guild.id} AND member_id = {ctx.author.id}")
        if not birthday:
            return await ctx.send(await language.get(self, ctx, 'birthday.not_set'))

        # Get the Json array of possible timezones.
        # Declare memory and load config.
        timezones = {}
        with open('assets/json/timezones.json', encoding='utf8') as data:
            timezones = json.load(data)

        # Now let's check if the given timezone is present, return error if none.
        matching_timezones = [string for string in timezones if timezone.lower() in string.lower()]
        if not matching_timezones:
            return await ctx.send(await language.get(self, ctx, 'birthday.timezone_unknown'))

        # Now let's save it.
        await self.bot.db.execute(f"UPDATE birthdays SET timezone = '{matching_timezones[0]}' WHERE guild_id = {ctx.guild.id} AND member_id = {ctx.author.id}")

        # Inform.
        message = await language.get(self, ctx, 'birthday.timezone_set')
        await ctx.send(message.format(matching_timezones[0]))

    @tasks.loop(minutes=10.0)
    async def check_birthday(self):
        """
            Function that loops to search the database for birthdays to give or remove.
            Note that this function is not guild specific; it's used globally for all the servers.
        """

        # Get people who are having their birthday right now and don't have to role already.
        birthdays = await self.bot.db.fetch("SELECT guild_id, member_id FROM birthdays "
                                            "WHERE to_char(birthday, 'MM-DD') = to_char(date(timezone(timezone, NOW())), 'MM-DD') AND triggered = FALSE "
                                            "GROUP BY guild_id, member_id")

        # Loop through every birthday there is now.
        for birthday in birthdays:
            
            # Ensure we got a guild...
            guild = self.bot.get_guild(birthday['guild_id'])
            if guild is None:
                continue

            # Ensure we got the member as well.
            member = guild.get_member(birthday['member_id'])
            if member is None:
                continue

            # Get some values required.
            channel_id = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {guild.id} AND key = 'birthday.channel'")
            role_id = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {guild.id} AND key = 'birthday.role'")

            # Now try to get the channel.
            if channel_id:
                channel = guild.get_channel(int(channel_id[0]['value']))
                
                # But before sending, ensure it's there.
                if channel is not None:
                    message = await language.get(self, None, 'birthday.wish', guild.id)
                    await channel.send(message.format(member.mention))

            # Add the role if we can do it, or else make it blank.
            if role_id:
                role_id = int(role_id[0]['value'])
                try:
                    await member.add_roles(guild.get_role(role_id))
                except:
                    pass
            else:
                role_id = ''
            
            # We have triggered this person's birthday...
            await self.bot.db.execute(f"UPDATE birthdays SET triggered = TRUE, given_role = '{role_id}' WHERE guild_id = {guild.id} AND member_id = {member.id}")

        # Now also look for people who had their birthday yesterday.
        old_birthdays = await self.bot.db.fetch("SELECT guild_id, member_id, given_role FROM birthdays "
                                                "WHERE to_char(birthday, 'MM-DD') != to_char(date(timezone(timezone, NOW())), 'MM-DD') AND triggered = TRUE "
                                                "GROUP BY guild_id, member_id, given_role")

        # Loop through every old birthday.
        for old_birthday in old_birthdays:
            
            # Ensure we got a guild...
            guild = self.bot.get_guild(old_birthday['guild_id'])
            if guild is None:
                continue

            # Ensure we got the member as well.
            member = guild.get_member(old_birthday['member_id'])
            if member is None:
                continue

            # If we had the birthday role, then remove it.
            if old_birthday['given_role'] and member:
                try:
                    await member.remove_roles(guild.get_role(int(old_birthday['given_role'])))
                except:
                    pass

            # No role given, simple update.
            await self.bot.db.execute(f"UPDATE birthdays SET triggered = FALSE, given_role = '' WHERE guild_id = {guild.id} AND member_id = {member.id}")

def setup(bot):
    bot.add_cog(Birthday(bot))
