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

async def get(self, ctx, key, guild_id=None):
    """Returns a line in a specific language as set by the guild."""

    # Get guild_id from ctx if none.
    if guild_id is None and ctx.guild:
        guild_id = ctx.guild.id

    # Still no guild? Then normal English with only username format...
    if guild_id is None:
        replace = { 'user_mention': ctx.message.author.mention }

        # Format and return!
        string = Languages.array['normal-english'][key]
        for index in replace:
            string = string.replace(index, replace[index])
        return string

    # Is the guild in the memory?
    if guild_id not in self.bot.memory:
        self.bot.memory[guild_id] = {}

    # Now set the language in memory if it's not there.
    if 'language' not in self.bot.memory[guild_id]:

        # Get the data from the database and set in memory.
        language = await self.bot.db.fetch("SELECT value FROM guild_settings WHERE guild_id = $1 AND key = 'language'", guild_id)
        self.bot.memory[guild_id]['language'] = language[0]['value']

    # Skip formatting if no ctx.
    if ctx is None:
        return Languages.array[self.bot.memory[guild_id]['language']][key]
    
    # Get proper language string for the guild, but after formatting...
    return fill(Languages.array[self.bot.memory[guild_id]['language']][key], ctx=ctx)

def fill(string, ctx=None, member=None, message=None):
    """Function to fill a string with common used values."""

    # Declare most used values for auto-fill.
    replace = None

    # For ctx.
    if ctx:
        replace = {
            '{guild_name}': ctx.guild.name,
            '{user_mention}': ctx.message.author.mention,
            '{user_id}': f'{ctx.message.author.name}#{ctx.message.author.discriminator}'
        }

    # For member.
    if member:
        replace = {
            '{guild_name}': member.guild.name,
            '{user_mention}': member.mention,
            '{user_id}': f'{member.name}#{member.discriminator}'
        }

    # For message.
    if message:
        replace = {
            '{guild_name}': message.guild.name,
            '{user_mention}': message.author.mention,
            '{user_id}': f'{message.author.name}#{message.author.discriminator}'
        }

    # Now make it happen.
    for key in replace:
        string = string.replace(key, replace[key])

    # Return end result.
    return string
