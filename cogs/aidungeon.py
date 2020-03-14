import discord
import re

from discord.ext import commands
from utils import aid2
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

class AIDungeon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = data.getjson('config.json')
        aid2.init_session(self.config)

    @commands.command(brief='Information on how to play AIDungeon with this bot')
    async def how(self, ctx):
        # Just send a message
        await ctx.send(f'Honk honk. To play AIDungeon, just @ me and say "new story", stop a story by saying "end story".\n'
                       f'No need to @ mention me during creation but you have to do that afterwards, oke? Honk honk.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages sent by the bot
        if message.author == self.bot.user:
            return

        # Create an user slang used to keep track of stories...
        userSlang = f'{message.guild.id}/{message.channel.id}/{message.author.id}'

        # Are we in story creation mode?
        if userSlang in STORIES and STORIES[userSlang]['status'] != STATUS_STORY:
            await self.new_story(userSlang, message)

        # We listen here to mentions, not to commands, so check if we are mentioned...
        if self.bot.user in message.mentions:
            message.content = re.sub(r'<@[^>]+>', '', message.content).strip()

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
                    result = aid2.continue_story(story['id'], message.content)
                    if result is not None:
                        await message.channel.send(f'Honk honk. {message.author.mention}. ```{result}```')
                    else:
                        await message.channel.send(f'Honk! Error in your story {message.author.mention}, I give up. Bye, honk.')
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
                story_id, result = aid2.init_story(story['mode'], story['character'], story['name'])

                if result is not None:
                    story['id'] = story_id
                    story['status'] = STATUS_STORY
                    await message.channel.send(f'Honk honk. {message.author.mention}. ```{result}```')
                else:
                    await message.channel.send(f'Honk! Error in your story {message.author.mention}, I give up. Bye, honk.')
                    del STORIES[userSlang]

def setup(bot):
    bot.add_cog(AIDungeon(bot))