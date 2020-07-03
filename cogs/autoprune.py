import asyncpg
import datetime
import discord

from dateutil import parser
from discord.ext import commands, tasks
from utils import data, language

class AutoPrune(commands.Cog):
    """Automatically remove messages from a channel after given time interval."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot
        self.prune_task.start()

    def cog_unload(self):
        """Function that happens the when the cog unloads."""
        self.prune_task.cancel()

    @tasks.loop(minutes=1)
    async def prune_task(self):
        """
            Function that loops to search the database for birthdays to give or remove.
            Note that this function is not guild specific; it's used globally for all the servers.
        """




def setup(bot):
    bot.add_cog(AutoPrune(bot))
