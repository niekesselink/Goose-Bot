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

async def get(ctx, line):
    """Returns a line in a specific language as set by the guild."""

    # No guild? Then English...
    if ctx is None or ctx.guild is None:
        return Languages.array['english'][line]

    # Get proper language string for the guild...
    return Languages.array['english'][line]
