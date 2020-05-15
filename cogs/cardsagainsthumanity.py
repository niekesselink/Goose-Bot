import discord
import os
import random

from discord.ext import commands, tasks

STATUS_SETUP = 'setup'
STATUS_PICKING = 'picking'
STATUS_VOTING = 'voting'

class Cards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Create bot memory if not present
        if 'cah_games' not in self.bot.memory and 'cah_players' not in self.bot.memory:
            self.bot.memory['cah_games'] = {}
            self.bot.memory['cah_players'] = {}

    @commands.command()
    @commands.guild_only()
    async def cards(self, ctx):
        """ Use this command to start a new Card Against Humanity game """

        # Are not already playing or setting up a game?
        if ctx.guild.id in self.bot.memory['cah_games']:
            await ctx.send(f'Honk, there is already a game ongoing on this server.')
            return

        # Get the cards.
        blacks = []
        whites = []
        for file in os.listdir('assets/cah'):
            reader = open(f'assets/cah/{file}', 'r')
            if file.endswith('b.txt'):
                blacks += reader.readlines()
            if file.endswith('w.txt'):
                whites += reader.readlines()

        # Define game...
        self.bot.memory['cah_games'][ctx.guild.id] = {
            'blacks': blacks,
            'blacks_current': None,
            'players': [],
            'player_czar': None,
            'player_iteration': 0,
            'status': STATUS_SETUP,
            'whites': whites,
            'whites_discarded': [],
            'whites_played': {},
        }
        
        # Start by asking for players to join, and define it of course...
        await ctx.send('**HONK!** Starting a Cards Against Humanity game! Typ *join cards* to join!\n'
                       'Type in *rules cards* if you want to know the rules of the game.')

        # Now let's add the player who requested the game to the game...
        await self.new_player(ctx.author, ctx.guild.id, no_inform=True)

        # Start instructions go to direct message of the player.
        await ctx.author.send(f'Honk, {ctx.message.author.mention}, type **start cards** when everyone is in or **end cards** to end it.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        # Private message?
        if not message.guild:
            
            # Are we in a game?
            if self.bot.memory['cah_players'][message.author.id] is None:
                return;

            # Is the game in the picking round? If so, we're are probably picking a white card!
            if self.bot.memory['cah_games'][self.bot.memory['cah_players'][message.author.id]['guild_id']]['status'] is STATUS_PICKING:
                await self.play_card(message)
                return

            # In other cases, just return since code below expects a guild.
            return;

        # Do we have a game?
        if message.guild.id not in self.bot.memory['cah_games']:
            return;

        # The rules of the game should always be able to view...
        if message.content.lower() is 'rules cards':
            await message.channel.send(f'Honk, here are the rules for Cards Against Humanity...\nhttp://s3.amazonaws.com/cah/CAH_Rules.pdf')
            return

        # Ending a game? Then just end it.
        if message.content.lower() is 'end cards':
            await self.end_game(message)
            return

        # Are we setting up the game?
        if self.bot.memory['cah_games'][message.guild.id]['status'] is STATUS_SETUP:

            # Joining a game? Then let's add the player!
            if message.content.lower() is 'join cards' and message.author.id not in self.bot.memory['cah_games'][message.guild.id]['players']:
                await self.new_player(message)
                return

            # Starting a game? If so, do it!
            if message.content.lower() is 'start cards':
                await self.start_game(message)
                return

    # Function for adding a new player to the game.
    async def new_player(self, message, no_inform=None):

        # Only one game at a time is allowed.
        if self.bot.memory['cah_players'][message.author.id] is not None:
            await message.author.send('Honk honk! You are already in a Cards Against Humanity game, it\'s not possible to be in two at the same time.')
            return;

        # Define the player...
        player = {
            'blacks': [],
            'guild_id': message.guild.id,
            'whites': []
        }
        
        # Let's get some cards for the player
        for i in range(self.bot.config.cards.cardsinhand):
            player['whites'].append(self.get_card(message.guild.id))

        # Add the player to players and to the game.
        self.bot.memory['cah_players'][message.author.id] = player
        self.bot.memory['cah_games'][message.guild.id]['players'].append(message.author.id)

        # Now inform the players and the other poeple relevant if necessary...
        if no_inform is not True:
            await message.channel.send(f'Honk, {message.author.mention} joined Cards Against Humanity!')
            await message.author.send('Honk honk! You have joined a Cards Against Humanity game.\n'
                              'Wait for the game to start and you will get your cards...')

    # Function for getting a new unique card in a game.
    def get_card(self, guild_id):

        # Do we still have cards? If not shuffle...
        if len(self.bot.memory['cah_games'][guild_id]['whites']) == 0:
            self.bot.memory['cah_games'][guild_id]['whites'] = self.bot.memory['cah_games'][guild_id]['discarded_whites']
            random.shuffle(self.bot.memory['cah_games'][guild_id]['whites'])

        # Get a card, remove from deck, and give it...
        card = random.choice(self.bot.memory['cah_games'][guild_id]['whites'])
        self.bot.memory['cah_games'][guild_id]['whites'].remove(card)
        return card
    
    # Function for when we are picking a white card.
    async def play_card(self, message):

        # Make sure we haven't played already...
        if self.bot.memory['cah_games'][self.bot.memory['cah_players'][message.author.id]['guild_id']]['whites_played'][message.author.id] is not None:
            await message.author.send(f'Honk, you have already played!')
            return

        # Get list of players cards and split from the comma in the message in case of two cards played..
        whitecards = self.bot.memory['cah_players'][message.author.id]['whites']
        played = message.content.split(',')

        # Validate for a proper int. Inform user if something is wrong in their input.
        for play in played:
            try:
                int(play)
            except:
                await message.author.send(f'Honk, that not a valid input! Try again.')

        # Declare the final value for the (combined) white card.
        white_value = None

        # Now let's combine the played whites into one text and remove them from the hand back to the game.
        for play in played:
            self.bot.memory['cah_games'][self.bot.memory['cah_players'][message.author.id]['guild_id']]['whites_discarded'].append(self.bot.memory['cah_players'][message.author.id]['whites'][play -1])
            white_value += self.bot.memory['cah_players'][message.author.id]['whites'][play -1] + ', '
            del self.bot.memory['cah_players'][message.author.id]['whites'][play -1]

        # Now for the final card for voting...
        whiteplayed = {
            "white": white_value[:-2]
        }

        # Add to the game's stock pile.
        self.bot.memory['cah_games'][self.bot.memory['cah_players'][message.author.id]['guild_id']]['whites_played'][message.author.id] = whiteplayed

        # Done, inform!
        await message.author.send(f'Honk, got it! Go back to the channel where I\'ll post the results once every has send them in!')

        # Get the player some new cards for the next round...
        for i in range(self.bot.config.cards.cardsinhand - len(self.bot.memory['cah_players'][message.author.id]['whites'])):
            self.bot.memory['cah_players'][message.author.id]['whites'].append(self.get_card(self.bot.memory['cah_players'][message.author.id]['guild_id']))
    
    # Function for starting a game.
    async def start_game(self, message):

        # Only the person who initialised the game can start it...
        if message.author.id is not self.bot.memory['cah_games'][message.guild.id]['players'][0]:
            return;

        # First things first, do we enough players?
        #if len(self.bot.memory['cah_games'][message.guild.id]['players']) <= self.bot.config.cards.minimumplayers:
        #    await message.channel.send(f'Honk, need at least {self.bot.config.cards.minimumplayers} players to start...')
        #    return

        # Ok�, now start, change status and a random iteration number...
        self.bot.memory['cah_games'][message.guild.id]['status'] = STATUS_PICKING
        self.bot.memory['cah_games'][message.guild.id]['player_iteration'] = random.randint(0, len(self.bot.memory['cah_games'][message.guild.id]['players']) - 1)

        # Inform and begin first round.
        await message.channel.send('**HONK!** Starting the Cards Against Humanity game!')
        await self.new_round(message)

    # Function that throws a black card into the mixer, also known as starting a round.
    async def new_round(self, message):

        # Do we still have black cards left? If not, end the game.
        if not self.bot.memory['cah_games'][message.guild.id]['blacks']:
            await message.channel.send('Honk, no black cards left!')
            await self.end_game(message)
            return

        # First let's make a copy of the list of all the players involved.
        players = self.bot.memory['cah_games'][message.guild.id]['players']
        
        # Reset player iteration if max number has been reached.
        if len(players) == self.bot.memory['cah_games'][message.guild.id]['player_iteration']:
            self.bot.memory['cah_games'][message.guild.id]['player_iteration'] = 0

        # Now let's pick the czar...
        czar = players[self.bot.memory['cah_games'][message.guild.id]['player_iteration']]
        self.bot.memory['cah_games'][message.guild.id]['player_iteration'] += 1
        self.bot.memory['cah_games'][message.guild.id]['player_czar'] = czar

        # Now remove the decider from the list and get an user object 
        #players.remove(czar)
        czar = self.bot.get_user(czar)

        # Let's get a black card.
        card = random.choice(self.bot.memory['cah_games'][message.guild.id]['blacks'])
        self.bot.memory['cah_games'][message.guild.id]['blacks_current'] = card
        self.bot.memory['cah_games'][message.guild.id]['blacks'].remove(card)

        # Now let's us throw the card into the chat.
        await message.channel.send(f'Honk honk! This is the new Black Card and **{czar.mention}** is the Card Czar!\n'
                                   'All other players, check your direct messages because I am honking you...\n',
                                   embed=discord.Embed(
                                       title=f'{card}',
                                       colour=0x000000
                                   ))

        # Loop through the players picking a white...
        for player in players:

            # Get the objects required.
            user = self.bot.get_user(player)
            cards = self.bot.memory['cah_games'][message.guild.id]['players'][player]['whites']

            # Send the message with white cards and the instructions..
            await user.send('Honk honk! You have the following White Cards, which one will you fill in?\n'
                            'Just say number of the card you want to play here privately, you have 2 minutes...\n\n' +
                            '\n'.join([f'{i + 1}) {cards[i]}' for i in range(len(cards))]))

    # Function to go to the second stage of the round, the voting.
    def mid_round(self):
        return

    def end_round(self):
        return

    # Function that ends a game properly.
    async def end_game(self, message):

        # Only the person who started the game can end it...
        if message.author.id is not self.bot.memory['cah_games'][message.guild.id]['players'][0]:
            return;

        # A simple message for now, improve later.
        await message.channel.send('Honk, ending the Cards Against Humanity game. Sad times.')

        # Remove the players...
        for player in self.bot.memory['cah_games'][message.guild.id]['players']:
            del self.bot.memory['cah_players'][player]

        # Now remove the game.
        del(self.bot.memory['cah_games'][message.guild.id])
        
def setup(bot):
    bot.add_cog(Cards(bot))