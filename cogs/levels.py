import asyncio
import math
import random
import re

from cachetools import TTLCache
from discord.ext import commands
from utils import embed, language

class Levels(commands.Cog):
    """Leveling functionality for users on a Discord server."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    async def cog_load(self):
        """Event that happens once this cog gets loaded."""

        # Create memory.
        if 'levels' not in self.bot.memory:
            self.bot.memory['levels'] = {}
            self.bot.memory['levels.lock'] = TTLCache(maxsize=math.inf, ttl=60)

            # Store values in memory.
            guilds = [guild async for guild in self.bot.fetch_guilds()]
            for guild in await self.bot.db.fetch("SELECT guild_id FROM guild_settings WHERE key = 'levels.enabled' AND value = 'True'"):
                if guild['guild_id'] in [guild.id for guild in guilds]:
                    await self.add_guild(guild['guild_id'])

    async def add_guild(self, guild_id):
        """Setup a guild in the level memory."""

        # Get the settings and banned lists from the database.
        config = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key LIKE 'levels.%' ORDER BY key ASC", guild_id)

        # Add the memory object.
        if guild_id not in self.bot.memory['levels']:
            self.bot.memory['levels'][guild_id] = {
                'bannedChannels': [],
                'bannedMembers': [],
                'xpRange': config[1]['value'],
                'xpRate': int(config[2]['value'])
            }

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Ignore bot, guild only, and guild needs to have levels activated.
        if message.author.bot or message.guild is None or message.guild.id not in self.bot.memory['levels']:
            return

        # If member is banned or the channel the message is in is, then ignore it.
        if message.author.id in self.bot.memory['levels'][message.guild.id]['bannedMembers'] or message.channel.id in self.bot.memory['levels'][message.guild.id]['bannedChannels']:
            return

        # Ignore if user is on lock.
        if f'{message.guild.id}_{message.author.id}' in self.bot.memory['levels.lock']:
            return

        # Add user to the lock array.
        self.bot.memory['levels.lock'][f'{message.guild.id}_{message.author.id}'] = True

        # Let's give the user random XP that falls within the XP range.
        range = self.bot.memory['levels'][message.guild.id]['xpRange'].split('-')
        earned_xp = random.randint(int(range[0]), int(range[1])) * self.bot.memory['levels'][message.guild.id]['xpRate']

        # Push the XP to the database, returning total XP value and current level.
        result = await self.bot.db.fetch("INSERT INTO levels AS l (guild_id, member_id, xp) VALUES ($1, $2, $3) "
                                         "ON CONFLICT (guild_id, member_id) DO UPDATE SET xp = l.xp + $3 RETURNING xp, level", message.guild.id, message.author.id, earned_xp)

        # Calculate the XP required for the next level a la MEE6 style.
        next_level = result[0]['level'] + 1
        treshold = self.get_xp_treshold(next_level)

        # Let's check if we just passed that treshold with the newly given xp.
        if result[0]['xp'] >= treshold and result[0]['xp'] - earned_xp < treshold:
            
            # Inform the level up first to be quickly as possible.
            msg = await language.get(self, None, 'levels.levelup', message.guild.id)
            await message.channel.send(msg.format(message.author.mention, next_level))

            # Let's update it in the database...
            await self.bot.db.execute("UPDATE levels SET level = $1 WHERE guild_id = $2 AND member_id = $3", next_level, message.guild.id, message.author.id)

            # Let's check if that means we're getting a new rank...
            role_id = await self.bot.db.fetch("SELECT role_id FROM levels_ranks WHERE guild_id = $1 AND level = $2", message.guild.id, next_level)
            if role_id:

                # We do, award it.
                role = message.guild.get_role(role_id[0]['role_id'])
                await message.author.add_roles(role)

                # Now inform about it.
                msg = await language.get(self, None, 'levels.newrole', message.guild.id)
                await message.channel.send(msg.format(role.name))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event that happens once some joins join the guild."""

        # Check if the user has XP and levels stored in the database.
        result = await self.bot.db.fetch("SELECT level FROM levels WHERE guild_id = $1 AND member_id = $2", member.guild.id, member.id)
        if result:

            # The person has a level! Probably rejoined, let's get the ranks that goes with the level.
            achieved_ranks = []
            ranks = await self.bot.db.fetch("SELECT role_id FROM levels_ranks WHERE guild_id = $1 AND level <= $2", member.guild.id, result[0]['level'])
            for rank in ranks:
                achieved_ranks.append(member.guild.get_role(rank['role_id']))

            # Let's add the ranks...
            await member.add_roles(*achieved_ranks)

    @commands.hybrid_command()
    @commands.guild_only()
    async def rank(self, ctx: commands.Context, username: str=None):
        """Get information about your current level."""

        # Command only works when levels are activated.
        if ctx.guild.id not in self.bot.memory['levels']:
            return

        # Get the user if given, else resort to self.
        user = ctx.author
        if username is not None:
            user_id = re.findall("\d+", username)
            user = ctx.guild.get_member(int(user_id[0]) if len(user_id) > 0 else username)
            user = user if user is not None else ctx.author

        # Get user info from the database.
        result = await self.bot.db.fetch("WITH summary AS (SELECT member_id, xp, level, ROW_NUMBER() OVER(ORDER BY xp DESC) AS rank FROM levels WHERE guild_id = $1) "
                                         "SELECT xp, level, rank FROM summary WHERE member_id = $2", ctx.guild.id, user.id)

        # If no user found then that person is likely not ranked.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'levels.norank'))

        # Author field.
        author = {
            'name': f'{user.name}#{user.discriminator}',
            'icon': user.avatar.url
        }
        
        # Create and send the embed.
        message = await language.get(self, ctx, 'levels.rank')
        await ctx.send(embed=embed.create(
            self,
            description=message.format(result[0]['rank'], result[0]['level'], result[0]['xp'], int(self.get_xp_treshold(result[0]['level'] + 1))),
            colour=0x303136,
            author=author
        ))

    @commands.hybrid_command()
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
        """Get's the top 10 people of the server."""
        
        # Get the top ten members.
        result = await self.bot.db.fetch("SELECT member_id, xp, level FROM levels WHERE guild_id = $1 "
                                         "ORDER BY xp DESC LIMIT 10", ctx.guild.id)

        # Generate a proper list now...
        message = ''
        for i, member in enumerate(result):
            user = ctx.guild.get_member(member['member_id'])

            # Get the correct notation...
            if i + 1 == 1:
                message += f":first_place:) **{user.name}** (Level {member['level']}, {member['xp']} XP)\n"
            elif i + 1 == 2:
                message += f":second_place:) **{user.name}** (Level {member['level']}, {member['xp']} XP)\n"
            elif i + 1 == 3:
                message += f":third_place:) **{user.name}** (Level {member['level']}, {member['xp']} XP)\n"
            else:
                message += f"{i + 1}) **{user.name}** (Level {member['level']}, {member['xp']} XP)\n"

        # Create and send the embed.
        await ctx.send(embed=embed.create(
            self,
            title='Leaderboard',
            description=message,
            colour=0x303136
        ))

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def levels(self, ctx: commands.Context):
        """Admin commands for levels."""
        return

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def setxp(self, ctx: commands.Context, *, data: str):
        """Give an user a specific amount of XP."""

        # Command only works when levels are activated.
        if ctx.guild.id not in self.bot.memory['levels']:
            return

        # Split the data and find an user.
        data = data.split(' ', 1)
        user = ctx.guild.get_member(int(re.findall("\d+", data[0])[0]))

        # Make sure there is an user, XP is given, and that it is an int...
        if user is None or (len(data) > 1 and not data[1].isdigit()):
            return await ctx.send(await language.get(self, ctx, 'core.incorrect_usage'))

        # Set XP to the user.
        await self.bot.db.execute("INSERT INTO levels (guild_id, member_id, xp) VALUES ($1, $2, $3) "
                                  "ON CONFLICT (guild_id, member_id) DO UPDATE SET xp = $3", ctx.guild.id, user.id, int(data[1]))

        # Now let's re-level and inform we're done!
        await self.re_level(ctx.guild, user, int(data[1]))
        await ctx.send('👌')

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def addxp(self, ctx: commands.Context, *, data: str):
        """Give an user a specific amount of XP."""

        # Command only works when levels are activated.
        if ctx.guild.id not in self.bot.memory['levels']:
            return

        # Split the data and find an user.
        data = data.split(' ', 1)
        user = ctx.guild.get_member(int(re.findall("\d+", data[0])[0]))

        # Make sure there is an user, XP is given, and that it is an int...
        if user is None or (len(data) > 1 and not data[1].isdigit()):
            return await ctx.send(await language.get(self, ctx, 'core.incorrect_usage'))

        # Add the XP to the user, return new total.
        result = await self.bot.db.fetch("INSERT INTO levels AS l (guild_id, member_id, xp) VALUES ($1, $2, $3) "
                                         "ON CONFLICT (guild_id, member_id) DO UPDATE SET xp = l.xp + $3 RETURNING xp", ctx.guild.id, user.id, int(data[1]))

        # Now let's re-level and inform we're done!
        await self.re_level(ctx.guild, user, result[0]['xp'])
        await ctx.send('👌')

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def removexp(self, ctx: commands.Context, *, data: str):
        """Remove XP from an user, use 'all' to remove all the earned XP."""

        # Command only works when levels are activated.
        if ctx.guild.id not in self.bot.memory['levels']:
            return

        # Split the data and find an user.
        data = data.split(' ', 1)
        user = ctx.guild.get_member(int(re.findall("\d+", data[0])[0]))

        # Make sure there is an user, XP is given, and that it is an int...
        if user is None or (len(data) > 1 and not data[1].isdigit()):
            return await ctx.send(await language.get(self, ctx, 'core.incorrect_usage'))

        # Remove the XP from the user, return new total.
        result = await self.bot.db.fetch("INSERT INTO levels AS l (guild_id, member_id, xp) VALUES ($1, $2, $3) "
                                         "ON CONFLICT (guild_id, member_id) DO UPDATE SET xp = l.xp - $3 RETURNING xp", ctx.guild.id, user.id, int(data[1]))

        # Now let's re-level and inform we're done!
        await self.re_level(ctx.guild, user, result[0]['xp'])
        await ctx.send('👌')

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx: commands.Context):
        """Enables the leveling system."""

        # Enable it...
        await self.bot.db.execute("UPDATE guild_settings SET value = 'True' WHERE key = 'levels.enabled' AND guild_id = $1", ctx.guild.id)
        self.bot.memory[ctx.guild.id]['levels.enabled'] = 'True'
        await self.add_guild(ctx.guild.id)

        # Inform...
        await ctx.send('👌')

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx: commands.Context):
        """Disables the leveling system."""

        # Disable it...
        await self.bot.db.execute("UPDATE guild_settings SET value = 'False' WHERE key = 'levels.enabled' AND guild_id = $1", ctx.guild.id)
        self.bot.memory[ctx.guild.id]['levels.enabled'] = 'False'
        del(self.bot.memory['levels'][ctx.guild.id])

        # Inform...
        await ctx.send('👌')

    @levels.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def recalculate(self, ctx: commands.Context):
        """Recalculates the level of everyone. It's dangerous, and might take long."""

        # Inform the progress is starting.
        await ctx.send(f'Starting to re-calculate level standings...')

        # Let's loop through all the members to re-level.
        for member in ctx.guild.members:
            result = await self.bot.db.fetch("SELECT xp FROM levels WHERE guild_id = $1 and member_id = $2", ctx.guild.id, member.id)
            if len(result) > 0:
                await self.re_level(ctx.guild, member, result[0]['xp'])
                await asyncio.sleep(0.5)

        # Done!
        await ctx.send('Done!')

    async def re_level(self, guild, member, xp):
        """Function that re-levels a member to the correct level according to the XP, as well as giving the ranks."""

        # Everyone starts at level 0, let's get looping till we get to right level, then remove one since we didn't match the latest...
        level = 0
        while xp >= self.get_xp_treshold(level):
            level += 1
        level -= 1

        # Save the level to the user in the database.
        await self.bot.db.execute("UPDATE levels SET level = $1 WHERE guild_id = $2 AND member_id = $3", level, guild.id, member.id)

        # For the ranks, define an array of achieved and failed.
        achieved_ranks = []
        failed_ranks = []

        # Now, let's get all the ranks available and start looping through them.
        ranks = await self.bot.db.fetch("SELECT level, role_id FROM levels_ranks WHERE guild_id = $1", guild.id)
        for rank in ranks:

            # Check if the level has been achieved, if so, add it to achieved, otherwise it goes into failed ranks.
            if level >= rank['level']:
                achieved_ranks.append(guild.get_role(rank['role_id']))
            else:
                failed_ranks.append(guild.get_role(rank['role_id']))

        # Let's add and remove the ranks...
        await member.add_roles(*achieved_ranks)
        await member.remove_roles(*failed_ranks)

    def get_xp_treshold(self, next_level):
        """Function that calculates the XP treshold for the next level."""

        # It's stolen from MEE6, but who cares right? Don't ask me the reasoning behind this calculation.
        return 5/6 * next_level * (2 * next_level * next_level + 27 * next_level + 91)

async def setup(bot):
    await bot.add_cog(Levels(bot))
