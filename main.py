import discord
import os

from discord.ext import commands
from utils import data

# Starting
print('Starting...')

# Get the json config
config = data.getjson('config.json')

# Declare the bot
bot = commands.Bot(
    command_prefix=config.prefix,
    description=config.description
)

# Load all the commands in the cogs folder
for file in os.listdir('cogs'):
    if file.endswith('.py'):
        name = file[:-3]
        bot.load_extension(f'cogs.{name}')

# Run the bot, log it in
bot.run(config.token)

