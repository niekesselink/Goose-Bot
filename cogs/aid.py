import discord
import requests

from discord.ext import commands
from utils import data

STORIES = {}

MODES = {
    'fantasy': ['noble', 'knight', 'squire', 'ranger', 'peasant', 'rogue'],
    'mystery': ['patient', 'detective', 'spy'],
    'apocalyptic': ['soldier', 'scavenger', 'survivor', 'courier'],
    'zombies': ['soldier', 'survivor', 'scientist']
}

STATUS_ASKED = 'asked'
STATUS_MODE = 'mode'
STATUS_CHARACTER = 'character'
STATUS_NAME = 'name'
STATUS_STORY = 'story'

MAX_RERUN = 5
TOKEN = None
URL = 'https://api.aidungeon.io'

class AIDungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = data.getjson('config.json')
        self.get_token()

    def get_token(self):
        global TOKEN

        # Declare data.
        data = {}
        data['email'] = self.config.aid.email
        data['password'] = self.config.aid.password

        # Make the request for a token.
        r = requests.post(f'{URL}/users', data)
        
        # Did it fail?
        if not r.ok:
            print('/users', r.status_code, r.reason)
            return None

        # Save, or die.
        try:
            TOKEN = r.json()['accessToken']
        except (ValueError, KeyError):
            print(f'{URL}/users: invalid response: {r.content}')

    @commands.command()
    async def how(self, ctx):
        """ Information on how to play AIDungeon with this bot """

        # Just send a message
        await ctx.send(f'Honk honk. To play AIDungeon, just @ me and say "new story", stop a story by saying "end story".\n'
                       f'No need to @ mention me during creation but you have to do that afterwards, oke? Honk honk.')

    # Listener for messages.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # Ignore private.
        if not message.guild:
            return;

        # Create an user slang used to keep track of stories...
        userSlang = f'{message.guild.id}/{message.channel.id}/{message.author.id}'

        # Are we in story creation mode?
        if userSlang in STORIES and STORIES[userSlang]['status'] != STATUS_STORY:
            await self.new_story(userSlang, message)

        # We listen here to mentions, not to commands, so check if we are mentioned...
        if self.bot.user in message.mentions:

            # Regardless of being in a story or not, do we want a new one?
            if message.content.lower().startswith('new story'):
                await self.new_story(userSlang, message)
                return

            # Are we in a story? If yes, declare it.
            if userSlang in STORIES:
                story = STORIES[userSlang]

                # Do we want to stop it?
                if message.content.lower().startswith('end story'):
                    await message.channel.send(f'Honk! Oké {message.author.mention}, ending your story, hope it was very honkable.')
                    del STORIES[userSlang]
                    return

                # And now we continue it if not running into an error...
                async with message.channel.typing():
                    data = {
                        'text': message.content
                    }

                    r = None
                    times = 0
                    story_id = story['id']

                    while (r is None or r.status_code >= 500) and times < MAX_RERUN:
                        r = requests.post(f'{URL}/sessions/{story_id}/inputs', data, headers={'X-Access-Token': TOKEN})
                        times += 1

                    if not r.ok:
                        await message.channel.send(f'Honk! Error in your continuing story {message.author.mention}, request error, I give up. Bye, honk.')
                        del STORIES[userSlang]
                    else:
                        try:
                            r = r.json()
                            result = r[-1]['value']
                            await message.channel.send(f'Honk honk. {message.author.mention}. ```{result}```')
                        except (ValueError, KeyError, IndexError):
                            await message.channel.send(f'Honk! Error in continuing your story {message.author.mention}, value error, I give up. Bye, honk.')
                            del STORIES[userSlang]

    # Function that creates a story, it's a little bit complicated this one.
    async def new_story(self, userSlang, message):

        # Creating a new one? Declare it.
        if userSlang not in STORIES:
            STORIES[userSlang] = {
                'id': None,
                'status': STATUS_ASKED
            }

        # And now define it.
        story = STORIES[userSlang]

        # We asked for a new story, so first question, which mode?
        if story['status'] == STATUS_ASKED:
            modes_names = list(MODES.keys())
            await message.channel.send(f'Honk! So you want a story {message.author.mention}?\n'
                                       f'**Pick a setting...**\n' +
                                       '\n'.join([f'{i+1}) {modes_names[i]}' for i in range(len(modes_names))]))

            # We have just asked the mode now, onto to the next phase...
            story['status'] = STATUS_MODE

        # We asked the mode, we got a response now.
        elif story['status'] == STATUS_MODE:
            mode = message.content.lower().strip()

            # Let's test if it's really an integer, that is what we expect.
            try:
                mode_i = int(mode) - 1
                modes_names = list(MODES.keys())
                if 0 <= mode_i < len(modes_names):
                    mode = modes_names[mode_i]
            except ValueError:
                await message.channel.send(f'Honk! That\'s not a valid answer! I asked you something honk honk?!')
                pass

            # Is the integer a valid mode and not something way overshot?
            if mode not in MODES:
                await message.channel.send(f'Honk! That was not one of the options... honk!')
            else:

                # Save the mode.
                story['mode'] = mode
                
                # Now ask the type of character.
                characters = MODES[mode]
                await message.channel.send(f'Honk! What are you {message.author.mention}?\n'
                                           f'**Select a character...**\n' +
                                           '\n'.join([f'{i + 1}) {characters[i]}' for i in range(len(characters))]))

                # And onto the next phase...
                story['status'] = STATUS_CHARACTER

        # Now we have asked the character, and we've got a response!
        elif story['status'] == STATUS_CHARACTER:
            character = message.content.lower().strip()

            # Once again, is it an integer?
            try:
                char_i = int(character) - 1
                characters = MODES[story['mode']]
                if 0 <= char_i < len(characters):
                    character = characters[char_i]
            except ValueError:
                await message.channel.send(f'Honk! That\'s not a valid answer! I asked you something honk honk?!')
                pass

            # Was it valid?
            if character not in MODES[story['mode']]:
                await message.channel.send(f'Honk! That was not one of the options... honk!')
            else:

                # Save it.
                story['character'] = character

                # And now all we need is a name for the character...
                await message.channel.send(f'Honk! And you are named {message.author.mention}?\n'
                                           f'**Enter your character name...**')

                # Nexxxttttt! (Yes, you know in what way to read that properly...)
                story['status'] = STATUS_NAME

        # And we got a response... you know the story.
        elif story['status'] == STATUS_NAME:

            # Save the name.
            story['name'] = message.content.strip()

            # Let's start...
            await message.channel.send(f'Honk! So {message.author.mention}, you\'re a *{story["character"]}* in a *{story["mode"]}* setting going by the name *{story["name"]}*. \n'
                                       f'**I\'m starting your honking story now...**')

            # We are typing...
            async with message.channel.typing():
                # Create the story!
                data = {
                    'storyMode': story['mode'],
                    'characterType': story['character'],
                    'name': story['name'],
                    'customPrompt': None,
                    'promptId': None
                }

                r = None
                times = 0

                while (r is None or r.status_code >= 500) and times < MAX_RERUN:
                    r = requests.post(f'{URL}/sessions', data, headers={'X-Access-Token': TOKEN})
                    times += 1

                if not r.ok:
                    await message.channel.send(f'Honk! Error in starting your story {message.author.mention}, request error, I give up. Bye, honk.')
                    del STORIES[userSlang]
                else:
                    try:
                        r = r.json()
                        story['id'] = r['id']
                        story['status'] = STATUS_STORY

                        result = r['story'][0]['value']
                        await message.channel.send(f'Honk honk. {message.author.mention}. ```{result}```')
                    except (ValueError, KeyError, IndexError):
                        await message.channel.send(f'Honk! Error in starting your story {message.author.mention}, value error, I give up. Bye, honk.')
                        del STORIES[userSlang]

def setup(bot):
    bot.add_cog(AIDungeon(bot))
