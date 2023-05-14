import textwrap

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
        result = await self.bot.db.fetch("SELECT g.id, g.name, string_agg('<@' || gm.member_id::TEXT || '>,', ' ') AS members, g.last_called "
                                         "FROM groups AS g LEFT OUTER JOIN group_members AS gm ON gm.group_id = g.id "
                                         "WHERE g.guild_id = $1 AND LOWER(g.name) = LOWER($2) "
                                         "GROUP BY g.id", message.guild.id, group)

        # Did we got a result event?
        if not result:
            msg = await language.get(self, None, 'groups.non_existent', message.guild.id)
            return await message.channel.send(language.fill(msg, message=message))

        # Does the group has members? If not cancel.
        if not result[0]['members']:
            msg = await language.get(self, None, 'groups.no_members', message.guild.id)
            return await message.channel.send(language.fill(msg, message=message))

        # Update last call.
        group_id = int(result[0]['id'])
        await self.bot.db.execute("UPDATE groups SET last_called = NOW() WHERE id = $1", group_id)

        # Split results to keep Discord message character limit in mind.
        wrapper = textwrap.TextWrapper(width=1900)
        lines = wrapper.wrap(text=result[0]['members'])

        # Now publish it, first post get's the group name.
        for index, line in enumerate(lines):
            if index == 0:
                await message.channel.send(f"**@{result[0]['name']}!** {line[:-1]}")
            else:
                await message.channel.send(line[:-1])

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
            Event that happens once a member leaves the guild the bot is in.
            We're doing this here to clean-up old members from groups. It's not possible (yet) through foreign keys.
        """

        # Remove member from all groups in the database for the guild he/she left.
        await self.bot.db.execute("DELETE FROM group_members AS gm USING groups AS g "
                                  "WHERE g.id = gm.group_id AND gm.member_id = $1 AND g.guild_id = $2", member.id, member.guild.id)

    @commands.hybrid_group(aliases=['group'])
    @commands.guild_only()
    async def groups(self, ctx: commands.Context):
        """Commands for groups on the server, purposed to ping those interested in an event."""
        return

    @groups.command()
    @commands.guild_only()
    async def list(self, ctx: commands.Context):
        """"Gives a list of groups."""

        # Open database and get the results.
        groups = await self.bot.db.fetch("SELECT g.name, g.description, "
                                         "(SELECT COUNT(*) FROM group_members AS gm WHERE gm.group_id = g.id) AS membercount "
                                         "FROM groups AS g WHERE g.guild_id = $1 "
                                         "ORDER BY membercount DESC", ctx.guild.id)

        # Are there even any groups?
        if not groups:
            return await ctx.send(await language.get(self, ctx, 'groups.no_groups'))

        # Fill in the groups in the fields list.
        fields = []
        for data in groups:
            memberLang = "groups.list.member" if data["membercount"] == 1 else "groups.list.members"
            fields.append({'name': ''.join([f'{chr(173)}\n', data['name']]) + f' `{str(data["membercount"])} {await language.get(self, ctx, memberLang)}`',
                           'value': data['description'],
                           'inline': False})

        # Send the embed...
        await ctx.send(embed=embed.create(
            self,
            title='',
            description=await language.get(self, ctx, 'groups.list.description'),
            colour=0x303136,
            fields=fields
        ))

    @groups.command()
    @commands.guild_only()
    async def join(self, ctx: commands.Context, group: str):
        """"Join an existing group."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups WHERE guild_id = $1 AND LOWER(name) = LOWER($2)", ctx.guild.id, group)

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Check if the user is not a member already.
        group_id = int(result[0]['id'])
        member_check = await self.bot.db.fetch("SELECT group_id FROM group_members WHERE group_id = $1 AND member_id = $2", group_id, ctx.author.id)
        if member_check:
            return await ctx.send(await language.get(self, ctx, 'groups.already_a_member'))

        # Join the group.
        await self.bot.db.execute("INSERT INTO group_members (group_id, member_id) VALUES ($1, $2)", group_id, ctx.author.id)

        # And now inform.
        message = await language.get(self, ctx, 'groups.joined')
        await ctx.send(message.format(result[0]['name']))

    @groups.command()
    @commands.guild_only()
    async def leave(self, ctx: commands.Context, group: str):
        """"Leave a group you're currently in."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups WHERE guild_id = $1 AND LOWER(name) = LOWER($2)", ctx.guild.id, group)

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Check if the user is a member .
        group_id = int(result[0]['id'])
        member_check = await self.bot.db.fetch("SELECT group_id FROM group_members WHERE group_id = $1 AND member_id = $2", group_id, ctx.author.id)
        if not member_check:
            return await ctx.send(await language.get(self, ctx, 'groups.not_a_member'))

        # Leave the group.
        await self.bot.db.execute("DELETE FROM group_members WHERE group_id = $1 AND member_id = $2", group_id, ctx.author.id)

        # And now inform.
        message = await language.get(self, ctx, 'groups.left')
        await ctx.send(message.format(result[0]['name']))

    @groups.command()
    @commands.guild_only()
    #@commands.has_permissions(administrator=True)
    async def create(self, ctx: commands.Context, *, data: str):
        """Create a new public group for people to join."""

        # Get the correct data from the message.
        data = data.split(' ', 1)
        group_name = data[0]
        group_description = data[1]

        # Check if there's a group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups WHERE guild_id = $1 AND LOWER(name) = LOWER($2)", ctx.guild.id, group_name)

        # If there is, tell so and stop creating.
        if result:
            return await ctx.send(await language.get(self, ctx, 'groups.already_exist'))

        # Do we have all data, so even description?
        if not group_name or not group_description:
            ctx.send(await language.get(self, ctx, 'event.missing_argument'))

        # Now create the group.
        await self.bot.db.execute("INSERT INTO groups (guild_id, name, description) VALUES ($1, $2, $3)", ctx.guild.id, group_name, group_description)

        # And inform.
        message = await language.get(self, ctx, 'groups.created')
        await ctx.send(message.format(group_name))

    @groups.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx: commands.Context, group: str):
        """Delete an existing group."""

        # Get the group matching the name.
        result = await self.bot.db.fetch("SELECT id, name FROM groups WHERE guild_id = $1 AND LOWER(name) = LOWER($2)", ctx.guild.id, group)

        # Tell the user if the group does not exist.
        if not result:
            return await ctx.send(await language.get(self, ctx, 'groups.non_existent'))

        # Now delete the group.
        group_id = int(result[0]['id'])
        await self.bot.db.execute("DELETE FROM groups WHERE id = $1", group_id)

        # And inform.
        message = await language.get(self, ctx, 'groups.deleted')
        await ctx.send(message.format(result[0]['name']))

    async def member_info_field(self, ctx, member):
        """Function to add a field to member info command."""

        # Get list of groups the member is part of.
        result = await self.bot.db.fetch("SELECT string_agg(g.name::TEXT, ', ') AS groups FROM group_members AS gm "
                                         "LEFT OUTER JOIN groups AS g ON g.id = gm.group_id "
                                         "WHERE g.guild_id = $1 AND gm.member_id = $2", ctx.guild.id, member.id)

        # Return the field now if there is something.
        return { 'name': await language.get(self, ctx, 'groups'), 'value': result[0]['groups'], 'inline': False } if result[0]['groups'] else None

async def setup(bot):
    await bot.add_cog(Groups(bot))
