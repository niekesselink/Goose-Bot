import asyncio
import asyncpg
import discord
import json
import os

from collections import namedtuple
from discord.ext import commands

class Bot(commands.Bot):
    """Main class of the bot."""

    def __init__(self, *args, **kwargs):
        """Initial function that runs when the class has been created."""

        # Declare memory and load config.
        self.memory = {}
        with open('config.json', encoding='utf8') as data:
            self.config = json.load(data, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        # Call the initialize of the bot itself.
        super().__init__(
            command_prefix=self.config.prefix,
            *args,
            **kwargs
        )

        # Configure database.
        self.db = asyncio.get_event_loop().run_until_complete(
            asyncpg.create_pool(self.config.postgre)
        )

# Define the bot.
bot = Bot()

# Add each cog there is in the cogs directory...
for file in os.listdir('cogs'):
    if file.endswith('.py'):
        name = file[:-3]
        bot.load_extension(f'cogs.{name}')

# Now let's start it.
bot.run(bot.config.token)
