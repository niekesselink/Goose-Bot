import os
import json
import traceback

class Languages:
    """Class for loading the languages."""

    # Language array.
    array = {}

    # Now let's fill them.
    for file in os.listdir('assets/languages'):
        with open(f'assets/languages/{file}') as content:
            array[file[:-5]] = json.load(content)

async def get(self, guild_id, key):
    """Returns a line in a specific language as set by the guild."""

    # No guild? Then English...
    if guild_id is None:
        return Languages.array['english'][key]

    # Is the guild in the memory?
    if guild_id not in self.bot.memory:
        self.bot.memory[guild_id] = {}

    # Now set the language in memory if it's not there.
    if 'language' not in self.bot.memory[guild_id]:

        # Get the data from the database.
        language = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {guild_id} AND key = 'language'")

        # Default if not exist.
        if not language:
            language = 'english'
        else:
            language = language[0]['value']

        # Set the memory.
        self.bot.memory[guild_id]['language'] = language
    
        # Get proper language string for the guild...
    return Languages.array[self.bot.memory[guild_id]['language']][key]
