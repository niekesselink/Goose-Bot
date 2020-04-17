import discord
import os

from discord.ext import commands
from utils import data

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.log('Initialising bot', 'Goose-Bot')
        self.config = data.getjson('config.json')
        super().__init__(command_prefix=self.config.prefix, description=self.config.description, *args, **kwargs)

    def token(self):
        return self.config.token

    def log(self, value, name=None):
        print(f'[{name}]', value)

def main():
    bot = Bot()

    for file in os.listdir('cogs'):
        if file.endswith('.py'):
            name = file[:-3]
            bot.load_extension(f'cogs.{name}')

    bot.run(bot.token())

if __name__ == "__main__":
    main()
