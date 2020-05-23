import discord
import os

from discord.ext import commands
from utils import json

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):

        # Starting...
        self.log('Initialising bot', 'Goose-Bot')
        self.config = json.get('config.json')

        # Declare a memory array for all cogs data for now.
        self.memory = {}

        # Call the initialize of the bot itself...
        super().__init__(
            command_prefix=self.config.prefix,
            *args,
            **kwargs
        )

    # Function that returns the token from the config to run the bot.
    def get_token(self):
        return self.config.token

    # Function to log information into the console.
    def log(self, value, name):
        print(f'[{name}]', value)

def main():

    # Declare the bot class.
    bot = Bot()

    # Add each cog there is in the cogs directory...
    for file in os.listdir('cogs'):
        if file.endswith('.py'):
            name = file[:-3]
            bot.load_extension(f'cogs.{name}')

    # Now let's start the bot. :-)
    bot.run(bot.get_token())

if __name__ == "__main__":
    main()
