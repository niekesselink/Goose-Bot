import asyncpg
import discord

from discord.ext import commands, tasks
from utils import language

class Roles(commands.Cog):
    """Feature to put a person who has his/her birthday on the spotlight."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Create memory and run a task to fill it...
        self.bot.memory['roles.triggers'] = []
        self.bot.loop.create_task(self.populate_memory())

    async def populate_memory(self):
        """Task to populate the memory for the trigger reactions to get roles."""

        # For performance, we want to load the known trigger messages into memory...
        triggers = await self.bot.db.fetch("SELECT guild_id, channel_id, message_id FROM roles_reaction")
        for trigger in triggers:
            self.bot.memory['roles.triggers'].append(f"{trigger['guild_id']}_{trigger['channel_id']}_{trigger['message_id']}")

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        self.bot.memory['roles.triggers'] = []

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def roles(self, ctx):
        """Commands for adding role reactions."""
        return

    @roles.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *, data: str):
        """Add a role trigger on a specific reaction."""

        # Get the correct data from the message.
        data = data.split(' ')
        message_id = int(data[0])
        role_id = int(data[1])
        reaction = data[2]

        # Now let's remove the message that initiated the command to clean-up...
        await ctx.message.delete(delay=10)

        # Get the message we need to add the reaction to, inform when not found.
        # We will throw the normal error in case of another error... makes sense?
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(await language.get(self, ctx, 'roles.message_not_found'), delete_after=10)
        except:
            throw

        # Do the same for the role.
        role = ctx.guild.get_role(role_id)
        if role is None:
            return await ctx.send(await language.get(self, ctx, 'roles.role_not_found'), delete_after=10)

        # Store this in the database, but make sure to catch duplicates...
        # If any other exception we will throw it so it can be solved by the developer.
        try:
            await self.bot.db.execute(f"INSERT INTO roles_reaction (guild_id, channel_id, message_id, role_id, reaction) VALUES ({ctx.guild.id}, {message.channel.id}, {message_id}, {role_id}, '{reaction}')")
        except asyncpg.exceptions.UniqueViolationError:
            return await ctx.send(await language.get(self, ctx, 'roles.already_exist'), delete_after=10)
        except:
            throw

        # Also add the trigger to the memory list in case it's not there yet..
        key = f'{ctx.guild.id}_{message.channel.id}_{message.id}'
        if key not in self.bot.memory['roles.triggers']:
            self.bot.memory['roles.triggers'].append(key)

        # Now let's add the reaction to the post and inform the success.
        await message.add_reaction(reaction)
        await ctx.send(await language.get(self, ctx, 'roles.added'), delete_after=10)

    @roles.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, *, data: str):
        """Remove a role reaction."""

        # Get the correct data from the message.
        data = data.split(' ')
        message_id = int(data[0])
        reaction = data[1]

        # Now let's remove the message that initiated the command to clean-up...
        await ctx.message.delete(delay=10)

        # Get the message we need to remove the reaction from, inform when not found.
        # We will throw the normal error in case of another error... makes sense?
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(await language.get(self, ctx, 'roles.message_not_found'), delete_after=10)
        except:
            throw

        # Now let's remove the trigger...
        await self.bot.db.execute(f"DELETE FROM roles_reaction WHERE guild_id = {ctx.guild.id} AND channel_id = {message.channel.id} AND message_id = {message_id} AND reaction = '{reaction}'")
        self.bot.memory['roles.triggers'].remove(f'{ctx.guild.id}_{message.channel.id}_{message.id}')

        # Now let's remove the reaction to the post and inform the success.
        await message.clear_reaction(reaction)
        await ctx.send(await language.get(self, ctx, 'roles.deleted'), delete_after=10)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Event that happens when a reaction is added. Has to be raw due to client cache."""

        # Ignore bots, and check if the message where the reaction was added is a trigger.
        if payload.member.bot or f'{payload.guild_id}_{payload.channel_id}_{payload.message_id}' not in self.bot.memory['roles.triggers']:
            return

        # Now try and get a role that goes with the reaction from the database...
        role_id = await self.bot.db.fetch(f"SELECT role_id FROM roles_reaction WHERE guild_id = {payload.guild_id} AND channel_id = {payload.channel_id} AND message_id = {payload.message_id} AND reaction = '{str(payload.emoji)}'")

        # Add the role to the user who reacted if there is a match.
        if role_id:
            try:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(int(role_id[0]['role_id']))
                await payload.member.add_roles(role)
            except:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Event that happens when a reaction is removed. Has to be raw due to client cache."""

        # Check if the message where the reaction was removed is a trigger.
        if f'{payload.guild_id}_{payload.channel_id}_{payload.message_id}' not in self.bot.memory['roles.triggers']:
            return

        # Now try and get a role that goes with the reaction from the database...
        role_id = await self.bot.db.fetch(f"SELECT role_id FROM roles_reaction WHERE guild_id = {payload.guild_id} AND channel_id = {payload.channel_id} AND message_id = {payload.message_id} AND reaction = '{str(payload.emoji)}'")

        # Remove the role if match...
        if role_id:
            try:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(int(role_id[0]['role_id']))
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)
            except:
                pass

def setup(bot):
    bot.add_cog(Roles(bot))
