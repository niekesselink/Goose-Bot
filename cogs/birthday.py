import asyncio
import datetime
import json

from dateutil import parser
from discord.ext import commands, tasks
from utils import language

class Birthday(commands.Cog):
    """Feature to put a person who has his/her birthday on the spotlight."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    def cog_load(self):
        """Event that happens once this cog gets loaded."""
        self.check_birthday.start()

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        self.check_birthday.cancel()

    @commands.hybrid_group()
    @commands.guild_only()
    async def birthday(self, ctx: commands.Context):
        """Commands for setting and changing your birthday."""
        return

    @birthday.command()
    @commands.guild_only()
    async def set(self, ctx: commands.Context, *, date: str):
        """Set your birthday date, the format day/month is used."""

        # Parse the given date and get guild timezone, return error if something is not working.
        try:
            date = parser.parse(date)
        except:
            return await ctx.send(await language.get(self, ctx, 'birthday.incorrect'))

        # Get guild timezone and ensure we have something...
        timezone = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = 'timezone'", ctx.guild.id)
        if timezone[0]['value'] == '':
            timezone = 'CET'
        else:
            timezone = timezone[0]['value']

        # Now add it to the database.
        await self.bot.db.execute("INSERT INTO birthdays (guild_id, member_id, birthday, timezone) VALUES ($1, $2, $3, $4) "
                                  "ON CONFLICT (guild_id, member_id) DO UPDATE SET birthday = $3", ctx.guild.id, ctx.author.id, date, timezone)

        # Inform the user we've set the birthday.
        message = await language.get(self, ctx, 'birthday.success')
        date_formatted = date.strftime(await language.get(self, ctx, 'birthday.format')).lower()
        await ctx.send(message.format(date_formatted, timezone))

    async def has_birthday(ctx: commands.Context):
        """Function to check if user has a birthday set."""
        birthday = await ctx.bot.db.fetch("SELECT birthday FROM birthdays WHERE guild_id = $1 AND member_id = $2", ctx.guild.id, ctx.author.id)
        if not birthday:
            await ctx.send(await language.get(ctx, ctx, 'birthday.not_set'))
            return False
        return True

    @birthday.command(aliases=['delete', 'remove'])
    @commands.guild_only()
    @commands.check(has_birthday)
    async def clear(self, ctx: commands.Context):
        """Remove your set birthday and don't get announced anymore when it's your day."""

        # Remove the birthday entry of the user and inform.
        await self.bot.db.execute("DELETE FROM birthdays WHERE guild_id = $1 AND member_id = $2", ctx.guild.id, ctx.author.id)
        await ctx.send(await language.get(self, ctx, 'birthday.cleared'))

    @birthday.command()
    @commands.guild_only()
    @commands.check(has_birthday)
    async def timezone(self, ctx: commands.Context, *, timezone: str):
        """Change the timezone of your current location."""

        # Get the Json array of possible timezones.
        timezones = {}
        with open('assets/json/timezones.json', encoding='utf8') as data:
            timezones = json.load(data)

        # Now let's check if the given timezone is present, return error if none.
        matching_timezones = [string for string in timezones if timezone.lower() in string.lower()]
        if not matching_timezones:
            return await ctx.send(await language.get(self, ctx, 'birthday.timezone_unknown'))

        # Now let's save it.
        await self.bot.db.execute("UPDATE birthdays SET timezone = $1 WHERE guild_id = $2 AND member_id = $3", matching_timezones[0], ctx.guild.id, ctx.author.id)

        # Inform.
        message = await language.get(self, ctx, 'birthday.timezone_set')
        await ctx.send(message.format(matching_timezones[0]))

    @commands.hybrid_command()
    @commands.guild_only()
    async def birthdays(self, ctx: commands.Context):
        """Shows the first eight upcoming birthdays."""

        # Let's get them from the database.
        birthdays = await self.bot.db.fetch("SELECT member_id, case WHEN bday < current_date THEN bday + interval '1 year' ELSE bday END, text "
                                            "FROM birthdays, to_char(birthday, 'Mon-DD') as text, "
                                            "make_date(extract(year from current_date)::int, extract(month from birthday)::int, extract(day from birthday)::int) as bday "
                                            "WHERE guild_id = $1 ORDER BY bday LIMIT 8", ctx.guild.id)

        # Time to format all the results...
        lines = []
        for birthday in birthdays:

            # Ensure we got the member...
            member = ctx.guild.get_member(birthday['member_id'])
            if member is None:
                continue

            # Add to the array.
            lines.append(f"● `{birthday['text']}` **{member.name}**#{member.discriminator}")

        # Now, we'll send it.
        await ctx.send(await language.get(self, ctx, 'birthday.upcoming') + '\n'.join(lines))

    async def member_info_field(self, ctx: commands.Context, member):
        """Function to add a field to member info command."""

        # Get birthday, return if not set.
        result = await self.bot.db.fetch("SELECT birthday FROM birthdays WHERE guild_id = $1 AND member_id = $2", ctx.guild.id, member.id)
        if not result:
            return None
        
        # Format the birthday and create the field.
        format = (await language.get(self, ctx, 'birthday.format')).replace('%Y', '')
        return { 'name': await language.get(self, ctx, 'birthday'), 'value': result[0]['birthday'].strftime(format), 'inline': False }

    @tasks.loop(minutes=15.0)
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
            channel_id = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = 'birthday.channel'", guild.id)
            role_id = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = 'birthday.role'", guild.id)

            # Now try to get the channel.
            if channel_id[0]['value'] != '':
                channel = guild.get_channel(int(channel_id[0]['value']))
                
                # But before sending, ensure it's there.
                if channel is not None:
                    message = await language.get(self, None, 'birthday.wish', guild.id)
                    await channel.send(message.format(member.mention))

            # Add the role if we can do it, or else make it blank.
            if role_id[0]['value'] != '':
                role_id = int(role_id[0]['value'])
                try:
                    await member.add_roles(guild.get_role(role_id))
                except:
                    pass
            else:
                role_id = ''
            
            # We have triggered this person's birthday...
            await self.bot.db.execute("UPDATE birthdays SET triggered = TRUE, given_role = $1 WHERE guild_id = $2 AND member_id = $3", str(role_id), guild.id, member.id)

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
            await self.bot.db.execute("UPDATE birthdays SET triggered = FALSE, given_role = '' WHERE guild_id = $1 AND member_id = $2", guild.id, member.id)

    @check_birthday.before_loop
    async def before_check_birthday(self):
        """Event that happens before the check_birthday task loop starts."""

        # Get the current time.
        now = datetime.datetime.now()
        target = (now.minute // 15 + 1) * 15
        target = now + datetime.timedelta(minutes=target - now.minute)
        target = target.replace(second=0, microsecond=0)

        # Get the difference in seconds and wait that amount of seconds...
        difference = (target - now).total_seconds()
        await asyncio.sleep(difference)

async def setup(bot):
    await bot.add_cog(Birthday(bot))
