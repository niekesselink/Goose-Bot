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
            
        # Declare intents.
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True,
            message_content=True,
        )

        # Call the initialize of the bot itself.
        super().__init__(
            command_prefix=self.config.prefix,
            intents=intents,
            *args,
            **kwargs
        )

    async def setup_hook(self) -> None:
        """Setup function that's async."""

        # Configure database.
        self.db = await asyncpg.create_pool(self.config.postgre)

        # Add each cog there is in the cogs directory...
        for file in os.listdir('cogs'):
            if file.endswith('.py'):
                name = file[:-3]
                await self.load_extension(f'cogs.{name}')

async def main():
    """Main method. What else?"""

    # Start database and efine the bot.
    async with Bot() as bot:
        await bot.start(bot.config.token)

# Run the main method.
asyncio.run(main())
