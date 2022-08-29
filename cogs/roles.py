import asyncpg
import discord

from discord.ext import commands
from utils import language

class Roles(commands.Cog):
    """Feature to put a person who has his/her birthday on the spotlight."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    async def cog_load(self):
        """Event that happens once this cog gets loaded."""

        # Create memory.
        if 'roles.triggers' not in self.bot.memory:
            self.bot.memory['roles.triggers'] = []

            # Store values.
            guilds = [guild async for guild in self.bot.fetch_guilds()]
            for guild in await self.bot.db.fetch("SELECT guild_id, channel_id, message_id FROM roles_reaction"):
                if guild['guild_id'] in [guild.id for guild in guilds]:
                    self.bot.memory['roles.triggers'].append(f"{guild['guild_id']}_{guild['channel_id']}_{guild['message_id']}")

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def roles(self, ctx: commands.Context):
        """Commands for adding role reactions."""
        return

    @roles.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def reaction(self, ctx: commands.Context, *, data: str):
        """Add a role trigger on a specific reaction."""

        # Split the data in an array and get the type of action as well as message_id.
        data = data.split(' ')
        action = data[0].lower()
        message_id = int(data[1])

        # Now let's remove the message that initiated the command...
        if ctx.prefix is self.bot.config.prefix:
            await ctx.message.delete(delay=10)

        # Get the message we need to add the reaction to, inform when not found.
        # We will throw the normal error in case of another error... makes sense?
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            if ctx.prefix is self.bot.config.prefix:
                return await ctx.send(await language.get(self, ctx, 'roles.message_not_found'), delete_after=10)
            else:
                return await ctx.send(await language.get(self, ctx, 'roles.message_not_found'))

        # Now, if the action is adding a reaction, then do the following code.
        if action == 'add':

            # Define variables.
            role = None
            reaction = data[3]

            # Get the role by ID, but only if it's an id, otherwise look it up in case of a name match.
            if data[2].isdigit():
                role = ctx.guild.get_role(int(data[2]))
            else:
                role = discord.utils.get(ctx.guild.roles, name=data[2])

            # Abort if nothing found...
            if role is None:
                return await ctx.send(await language.get(self, ctx, 'roles.role_not_found'), delete_after=10)

            # Store this in the database, but make sure to catch duplicates...
            # If any other exception we will throw it so it can be solved by the developer.
            try:
                await self.bot.db.execute("INSERT INTO roles_reaction (guild_id, channel_id, message_id, role_id, reaction) VALUES ($1, $2, $3, $4, $5)",
                                          ctx.guild.id, message.channel.id, message_id, role.id, reaction)
            except asyncpg.exceptions.UniqueViolationError:
                if ctx.prefix is self.bot.config.prefix:
                    return await ctx.send(await language.get(self, ctx, 'roles.already_exist'), delete_after=10)
                else:
                    return await ctx.send(await language.get(self, ctx, 'roles.already_exist'))

            # Also add the trigger to the memory list in case it's not there yet..
            key = f'{ctx.guild.id}_{message.channel.id}_{message.id}'
            if key not in self.bot.memory['roles.triggers']:
                self.bot.memory['roles.triggers'].append(key)

            # Now let's add the reaction to the post and inform the success.
            await message.add_reaction(reaction)
            if ctx.prefix is self.bot.config.prefix:
                await ctx.send(await language.get(self, ctx, 'roles.added'), delete_after=10)
            else:
                await ctx.send(await language.get(self, ctx, 'roles.added'))

        # If the action is remove, then do the following...
        if action == 'remove':

            # Split rest of data.
            reaction = data[1]

            # Now let's remove the trigger...
            await self.bot.db.execute("DELETE FROM roles_reaction WHERE guild_id = $1 AND channel_id = $2 AND message_id = $3 AND reaction = $4",
                                      ctx.guild.id, message.channel.id, message_id, reaction)

            # Now let's remove the reaction to the post, also the trigger if no reactions are left.
            await message.clear_reaction(reaction)

            # Inform success..
            if ctx.prefix is self.bot.config.prefix:
                await ctx.send(await language.get(self, ctx, 'roles.deleted'), delete_after=10)
            else:
                await ctx.send(await language.get(self, ctx, 'roles.deleted'))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Event that happens when a reaction is added. Has to be raw due to client cache."""
        await self.handle_reaction_event(payload, 'add')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Event that happens when a reaction is removed. Has to be raw due to client cache."""
        await self.handle_reaction_event(payload, 'remove')

    async def handle_reaction_event(self, payload, action):
        """Uniform function to handle the reaction add/remove event."""

        # Ignore bot and check if the message where the reaction was done is a trigger.
        if (payload.member and payload.member.bot) or payload.guild_id is None or f'{payload.guild_id}_{payload.channel_id}_{payload.message_id}' not in self.bot.memory['roles.triggers']:
            return

        # Now try and get a role that goes with the reaction from the database...
        role_id = await self.bot.db.fetch("SELECT role_id FROM roles_reaction WHERE guild_id = $1 AND channel_id = $2 AND message_id = $3 AND reaction = $4",
                                          payload.guild_id, payload.channel_id, payload.message_id, str(payload.emoji))

        # Get some more data if there is a role_id...
        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(int(role_id[0]['role_id']))

            # Now do the proper action.
            if action == 'add':
                await payload.member.add_roles(role)
            elif action == 'remove':
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Even that happens when a message gets deleted."""

        # Guild only...
        if payload.guild_id is None:
            return

        # Check if the message where the reaction was done is a trigger, and if so, delete it.
        if f'{payload.guild_id}_{payload.channel_id}_{payload.message_id}' in self.bot.memory['roles.triggers']:
            await self.bot.db.fetch("DELETE FROM roles_reaction WHERE guild_id = $1 AND channel_id = $2 AND message_id = $3", payload.guild_id, payload.channel_id, payload.message_id)
            self.bot.memory['roles.triggers'].remove(f'{payload.guild_id}_{payload.channel_id}_{payload.message_id}')

async def setup(bot):
    await bot.add_cog(Roles(bot))
