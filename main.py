import discord
import os

from discord.ext import commands
from utils import data

class Bot(commands.Bot):
    """Main class of the bot."""

    def __init__(self, *args, **kwargs):
        """Initial function that runs when the class has been created."""

        # Load config and declare memory.
        self.config = data.get_json('config.json')
        self.memory = {}

        # Call the initialize of the bot itself.
        super().__init__(
            command_prefix=self.config.prefix,
            *args,
            **kwargs
        )

        # Configure database.
        self.redis = data.Redis(
            self.config.redis,
            self.loop
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
