import discord

from discord.ext import commands
from utils import embed, language

class Groups(commands.Cog):
    """Commands for forming and using mention groups."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Event that happens when user sends a message in a channel."""

        # Make sure we're going to mention a group by doing the command.
        if not message.content.startswith('@group '):
            return

        # Strip out the group name.
        group = message.content.split(' ')[1]

        # Get the group result
        result = await self.bot.db.fetch("SELECT g.id, g.name, string_agg('<@' || gm.member_id::TEXT || '>', ', ') AS members, g.last_called "
                                         "FROM groups AS g LEFT OUTER JOIN group_members AS gm ON gm.group_id = g.id "
                                         f"WHERE g.guild_id = {message.guild.id} AND LOWER(g.name) = LOWER('{group}') "
                                         "GROUP BY g.id")

        # Did we got a result event?
        if not result:
            return await message.channel.send(await language.get(self, ctx, 'groups.non_existent'))

        # Update last call.
        group_id = int(result[0]['id'])
        await self.bot.db.execute(f"UPDATE groups SET last_called = NOW() WHERE id = {group_id}")

        # Now publish the results.
        await message.channel.send('**@' + result[0]['name'] + '!** ' + result[0]['members'])

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
            Event that happens once a member leaves the guild the bot is in.
            We're doing this here to clean-up old members from groups. It's not possible (yet) through foreign keys.
        """

        # Remove member from all groups in the database.
        await self.bot.db.execute(f"DELETE FROM guild_members WHERE guild_id = {member.guild.id} AND id = {member.id}")

    @commands.group()
    async def group(self, ctx):
        """Declaration of the group category."""
        return

    @group.command()
    async def list(self, ctx):
        """"Gives a list of groups."""

        # Open database and get the results.
        groups = await self.bot.db.fetch("SELECT g.name, g.description, "
                                         "(SELECT COUNT(*) FROM group_members AS gm WHERE gm.group_id = g.id) AS membercount "
                                         f"FROM groups AS g WHERE g.guild_id = {ctx.guild.id} "
                                         "ORDER BY membercount")

        # Are there even any groups?
        if not groups:
            return await ctx.send(await language.get(self, ctx, 'groups.no_groups'))

        # Get the correct language for members string and define a field variable.
        members = await language.get(self, ctx, 'groups.list.members')
        fields = {}

        # Fill in the groups in the fields list.
        for data in groups:
            fields.update({ data['name'] + ' (' + str(data['membercount']) + f' {members})': data['description'] })

        # Send the embed...
        await ctx.send(embed=embed.create(
            title=await language.get(self, ctx, 'groups.list.title'),
            description=await language.get(self, ctx, 'groups.list.description'),
            fields=fields
        ))

    @group.command()
    async def join(self, ctx, group: str):
        """"Join an existing group."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups "
                                         f"WHERE guild_id = {ctx.guild.id} AND LOWER(name) = LOWER('{group}')")

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Check if the user is not a member already.
        group_id = int(result[0]['id'])
        member_check = await self.bot.db.fetch(f"SELECT group_id FROM group_members WHERE group_id = {group_id} AND member_id = {ctx.author.id}")
        if member_check:
            return await ctx.send(await language.get(self, ctx, 'groups.already_a_member'))

        # Join the group.
        await self.bot.db.execute(f"INSERT INTO group_members (group_id, member_id) VALUES ({group_id}, {ctx.author.id})")

        # And now inform.
        message = await language.get(self, ctx, 'groups.joined')
        await ctx.send(message.format(result[0]['name']))

    @group.command()
    async def leave(self, ctx, group: str):
        """"Leave a group you're currently in."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups "
                                         f"WHERE guild_id = {ctx.guild.id} AND LOWER(name) = LOWER('{group}')")

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Check if the user is a member .
        group_id = int(result[0]['id'])
        member_check = await self.bot.db.fetch(f"SELECT group_id FROM group_members WHERE group_id = {group_id} AND member_id = {ctx.author.id}")
        if not member_check:
            return await ctx.send(await language.get(self, ctx, 'groups.not_a_member'))

        # Leave the group.
        await self.bot.db.execute(f"DELETE FROM group_members WHERE group_id = {group_id} AND member_id = {ctx.author.id}")

        # And now inform.
        message = await language.get(self, ctx, 'groups.left')
        await ctx.send(message.format(result[0]['name']))

    @group.command()
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, *, data: str):
        """Create a new public group for people to join."""

        # Get the correct data from the message.
        data = data.split(' ', 1)
        group_name = data[0]
        group_description = data[1].replace("'", "''")

        # Check if there's a group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups "
                                         f"WHERE guild_id = {ctx.guild.id} AND LOWER(name) = LOWER('{group_name}')")

        # If there is, tell so and stop creating.
        if result:
            return await ctx.send(await language.get(self, ctx, 'groups.already_exist'))

        # Now create the group.
        await self.bot.db.execute(f"INSERT INTO groups (guild_id, name, description) VALUES ({ctx.guild.id}, '{group_name}', '{group_description}')")

        # And inform.
        message = await language.get(self, ctx, 'groups.created')
        await ctx.send(message.format(group_name))

    @group.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, group: str):
        """Delete an existing group."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups "
                                         f"WHERE guild_id = {ctx.guild.id} AND LOWER(name) = LOWER('{group}')")

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Now delete the group.
        group_id = int(result[0]['id'])
        await self.bot.db.execute(f"DELETE FROM groups WHERE id = {group_id}")

        # And inform.
        message = await language.get(self, ctx, 'groups.deleted')
        await ctx.send(message.format(result[0]['name']))

def setup(bot):
    bot.add_cog(Groups(bot))
