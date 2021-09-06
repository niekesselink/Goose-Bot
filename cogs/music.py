import asyncio
import discord
import os
import random
import re
import requests
import spotipy
import youtube_dl

from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from utils import language

class Music(commands.Cog):
    """Commands for playing music in a voice channel."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Define memory variable...
        if 'music' not in self.bot.memory:
            self.bot.memory['music'] = {}

    @commands.command()
    @commands.guild_only()
    async def join(self, ctx):
        """Brings the bot to to the channel."""

        # Make sure the person using the command is in a voice channel.
        if ctx.author.voice is None:
            return await ctx.send(await language.get(self, ctx, 'music.user_not_in_channel'))

        # Are we in a voice client? If so, inform properly; we're somewhere else or already in your channel...
        if ctx.voice_client is not None:
            if ctx.author.voice.channel is ctx.voice_client.channel:
                return await ctx.send(await language.get(self, ctx, 'music.already_there'))
            return await ctx.send(await language.get(self, ctx, 'music.already_in_channel'))

        # We're not in a channel but are going to now, also we do it deafened...
        await ctx.author.voice.channel.connect()
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)
        await ctx.send(await language.get(self, ctx, 'music.join'))

        # Create a memory object.
        if ctx.guild.id not in self.bot.memory['music']:
            self.bot.memory['music'][ctx.guild.id] = {
                'playlist': [],
                'playlistMessages': {},
                'playing': False,
                'playingIndex': 0,
                'playingLoop': 'off',
                'volume': 1   
            }

        # Do we have a playlist but not playing? Let's start playing again then...
        if len(self.bot.memory['music'][ctx.guild.id]['playlist']) > 0 and ctx.voice_client.source is None:
            self.play_song(ctx)

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        """Makes the bot leave the channel."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return

        # We're leaving...
        await ctx.voice_client.disconnect()
        await ctx.send(await language.get(self, ctx, 'music.leave'))
        del(self.bot.memory['music'][ctx.guild.id])

    @commands.command(aliases=['queue', 'q'])
    @commands.guild_only()
    async def playlist(self, ctx):
        """Shows the current playlist of the bot."""

        # Are we in a channel?
        if ctx.voice_client is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_in_channel'))

        # If there's nothing in the list then send a plain message.
        if len(self.bot.memory['music'][ctx.guild.id]['playlist']) == 0:
            return await ctx.send(await language.get(self, ctx, 'music.playlist.nothing'))

        # We want to show 3 (4 in code since this one counts current song as well) songs coming up, and 6 songs behind us...
        lower = self.bot.memory['music'][ctx.guild.id]['playingIndex'] - 6
        upper = self.bot.memory['music'][ctx.guild.id]['playingIndex'] + 4
        
        # Validate...
        lower, upper = self.validate_paginging_numbers(ctx.guild.id, lower, upper)

        # Send the message, and save it...
        message = await ctx.send(await self.get_playlist_page(ctx.guild.id, lower, upper))

        # Are we going to page the queue message, as in more than 10?
        if len(self.bot.memory['music'][ctx.guild.id]['playlist']) > 10:

            # Save the message for reference.
            self.bot.memory['music'][ctx.guild.id]['playlistMessages'][message.id] = {
                'lower': lower,
                'upper': upper
            }

            # Add reactions..
            await message.add_reaction('⏫')
            await message.add_reaction('⬆')
            await message.add_reaction('▶️')
            await message.add_reaction('⬇')
            await message.add_reaction('⏬')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Event that happens when emoji reactions are given, in this case to control the playlist view."""

        # Ignore bot and check if guild is in music memory before checking further...
        if user.bot or user.guild.id not in self.bot.memory['music']:
            return

        # Check if the message is a queue message as well, and proper emoji are being used..
        if reaction.message.id not in self.bot.memory['music'][reaction.message.guild.id]['playlistMessages'] and reaction.emoji not in ['⏫', '⬆', '▶️', '⬇', '⏬']:
            return

        # Let's asume it's going a page forward for now...
        lower = self.bot.memory['music'][reaction.message.guild.id]['playlistMessages'][reaction.message.id]['lower'] + 10
        upper = self.bot.memory['music'][reaction.message.guild.id]['playlistMessages'][reaction.message.id]['upper'] + 10

        # Are we going to top? Then do that.
        if reaction.emoji == '⏫':
            lower = 0
            upper = 10

        # Are we going back, then remove 20 since we assumed going forward first...
        if reaction.emoji == '⬆':
            lower = lower - 20
            upper = upper - 20

        # If going to now playing, then well, do that.
        if reaction.emoji == '▶️':
            lower = self.bot.memory['music'][reaction.message.guild.id]['playingIndex'] - 6
            upper = self.bot.memory['music'][reaction.message.guild.id]['playingIndex'] + 4


        # Or... are we going to bottom instead?
        if reaction.emoji == '⏬':
            lower = len(self.bot.memory['music'][reaction.message.guild.id]['playlist']) - 10
            upper = len(self.bot.memory['music'][reaction.message.guild.id]['playlist'])

        # Validate and store the values...
        lower, upper = self.validate_paginging_numbers(reaction.message.guild.id, lower, upper)
        self.bot.memory['music'][reaction.message.guild.id]['playlistMessages'][reaction.message.id]['lower'] = lower
        self.bot.memory['music'][reaction.message.guild.id]['playlistMessages'][reaction.message.id]['upper'] = upper

        # Edit the message and undo reaction...
        await reaction.message.edit(content = await self.get_playlist_page(reaction.message.guild.id, lower, upper))
        await reaction.remove(user)

    async def get_playlist_page(self, guild_id, lower, upper):
        """"Get a page for the queue between a range of indexes."""

        # Declare top part of the message...
        message = await language.get(self, None, 'music.playlist', guild_id)
        message += '```nim\n'

        # Add all the songs we have queued.
        for i in range(lower, upper):

            # The line of the song queued with some cutting and spaces calculations...
            spaces = ' ' * (len(str(upper)) + 1 - len(str(i + 1)))
            title = self.bot.memory['music'][guild_id]['playlist'][i]['title']
            title = (title[:40] + '…') if len(title) > 40 else title
            line = '{0}){1}{2}\n'.format(i + 1, spaces, title)

            # Indicate the song we're playing now.
            if i == self.bot.memory['music'][guild_id]['playingIndex']:
                line = '     ⬐ {0}\n{1}     ⬑ {0}\n'.format(await language.get(self, None, 'music.playlist.now', guild_id), line)

            # Append...
            message += line

        # Add an end message and send.
        message += '\n{0}```'.format(await language.get(self, None, 'music.playlist.end', guild_id))
        return message

    def validate_paginging_numbers(self, guild_id, lower, upper):
        """"Function to make sure that page numbering will go correctly..."""

        # Upper should always be 10, but not exceed max amount of numbers in queue.
        upper = 10 if 10 > upper else upper
        upper = len(self.bot.memory['music'][guild_id]['playlist']) if upper >= len(self.bot.memory['music'][guild_id]['playlist']) else upper

        # Lower should be always be 10 lower than upper, bot not eceed 0.
        lower = lower if upper - lower == 10 else upper - 10
        lower = 0 if 0 > lower else lower

        # Return the values...
        return lower, upper

    @commands.command()
    @commands.guild_only()
    async def volume(self, ctx, level: int):
        """Changes the volume of the music."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, True):
            return

        # Now let's change the volume and inform...
        ctx.voice_client.source.volume = level / 100
        self.bot.memory['music'][ctx.guild.id]['volume'] = level / 100
        await ctx.send((await language.get(self, ctx, 'music.volume')).format(level))

    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx):
        """Skips the current playing song."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, True):
            return

        # Let's skip the song...
        ctx.voice_client.stop()
        await ctx.send(await language.get(self, ctx, 'music.skip'))

    @commands.command(aliases=['remove'])
    @commands.guild_only()
    async def delete(self, ctx, position):
        """Removes a song from the playlist at the given position."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, True):
            return

        # Declare drop variable, for in case we need to adjust the current playing index.
        indexPoints = position.split('-')
        playingDrop = 0

        # Validate input.
        if not indexPoints[0].isdigit() or (len(indexPoints) > 1 and not indexPoints[1].isdigit()):
            return await ctx.send(await language.get(self, ctx, 'core.incorrect_usage'))

        # Can't remove current playing, use skip instead.
        nowPlayingVisual = self.bot.memory['music'][ctx.guild.id]['playingIndex'] + 1
        if int(indexPoints[0]) == nowPlayingVisual or (len(indexPoints) > 1 and int(indexPoints[0]) >= nowPlayingVisual and int(indexPoints[1]) <= nowPlayingVisual):
            return await ctx.send(await language.get(self, ctx, 'music.removed_no_current'))

        # Check if range is given, if so get a loop going corresponding to the range.
        if '-' in position:
            for i in list(range(int(indexPoints[0]) - 1, int(indexPoints[1]))):

                # Let's remove the item, we keep removing the first index here as the playlist will automatically drop their items down...
                # Afterwards, let's increase the drop rate what might be needed in case of 
                del(self.bot.memory['music'][ctx.guild.id]['playlist'][int(indexPoints[0]) - 1])
                playingDrop += 1

            # Inform we removed the range...
            message = await language.get(self, ctx, 'music.removed_range')
            await ctx.send(message.format(position))

        # Otherwise just remove one song, but get the name for the information beforehand...
        else:
            title = self.bot.memory['music'][ctx.guild.id]['playlist'][int(indexPoints[0]) - 1]['title']
            del(self.bot.memory['music'][ctx.guild.id]['playlist'][int(indexPoints[0]) - 1])
            playingDrop += 1

            # Inform.
            message = await language.get(self, ctx, 'music.removed')
            await ctx.send(message.format(title))

        # Adjust playing index accordingly.
        if int(indexPoints[0]) < self.bot.memory['music'][ctx.guild.id]['playingIndex']:
            self.bot.memory['music'][ctx.guild.id]['playingIndex'] = self.bot.memory['music'][ctx.guild.id]['playingIndex'] - playingDrop

    @commands.command()
    @commands.guild_only()
    async def clear(self, ctx):
        """Clears the current playlist."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return
            
        # Clear the playlist.
        self.bot.memory['music'][ctx.guild.id]['playlist'] = []
        self.bot.memory['music'][ctx.guild.id]['playingIndex'] = 0

        # Stop playing and inform.
        ctx.voice_client.stop()
        self.bot.memory['music'][ctx.guild.id]['playing'] = False
        await ctx.send(await language.get(self, ctx, 'music.cleared'))

    @commands.command()
    @commands.guild_only()
    async def loop(self, ctx, trigger):
        """Loop the song, playlist or turn it off again."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return
            
        # Stop looping in case that keyword is given.
        if trigger == 'off' or trigger == 'stop':
            self.bot.memory['music'][ctx.guild.id]['playingLoop'] = 'off'
            await ctx.send(await language.get(self, ctx, 'music.loop.off'))

        # Start looping the current track.
        elif trigger == 'track' or trigger == 'song':
            self.bot.memory['music'][ctx.guild.id]['playingLoop'] = 'track'
            await ctx.send(await language.get(self, ctx, 'music.loop.track'))

            # Now let's see if we need to start playing directly, as in, nothing is playing...
            if not self.bot.memory['music'][ctx.guild.id]['playing']:
                self.bot.memory['music'][ctx.guild.id]['playing'] = True
                self.bot.memory['music'][ctx.guild.id]['playingIndex'] = self.bot.memory['music'][ctx.guild.id]['playingIndex'] - 1
                self.play_song(ctx, self.bot.memory['music'][ctx.guild.id]['playingIndex'])

        # Start looping the whole queue.
        elif trigger == 'queue' or trigger == 'playlist':
            self.bot.memory['music'][ctx.guild.id]['playingLoop'] = 'queue'
            await ctx.send(await language.get(self, ctx, 'music.loop.queue'))

            # Now let's see if we need to start playing directly, as in, nothing is playing...
            if not self.bot.memory['music'][ctx.guild.id]['playing']:
                self.bot.memory['music'][ctx.guild.id]['playing'] = True
                self.play_song(ctx)

        # Unknown trigger...
        else: 
            await ctx.send(await language.get(self, ctx, 'core.trigger_unknown'))
                
    @commands.command()
    @commands.guild_only()
    async def shuffle(self, ctx):
        """Shuffles the playlist."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return

        # Let's get current entry object first, and remove it.
        entry = self.bot.memory['music'][ctx.guild.id]['playlist'][self.bot.memory['music'][ctx.guild.id]['playingIndex']]
        self.bot.memory['music'][ctx.guild.id]['playlist'].remove(entry)

        # Everyday I'm shuffeling...
        random.shuffle(self.bot.memory['music'][ctx.guild.id]['playlist'])

        # Now set the entry back at first spot, and update playing index.
        self.bot.memory['music'][ctx.guild.id]['playlist'].insert(0, entry)
        self.bot.memory['music'][ctx.guild.id]['playingIndex'] = 0

        # And finally, inform..
        await ctx.send(await language.get(self, ctx, 'music.shuffle'))

    @commands.command(aliases=['p'])
    @commands.guild_only()
    async def play(self, ctx, *, query: str):
        """Play a song or playlist by providing the name/artist or through an URL."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return
        
        # Start typing incidicator and declare variables.
        await ctx.channel.trigger_typing()
        added_playlist = False
        entry = None

        # Extract the right data in case it's a Spotify link, we want to make it a search string.
        if 'spotify.com' in query and ('playlist' in query or 'track' in query):

            # First, let's set up a connection to Spotify to do so through Spotipy and get information about the track from the URL.
            credentials = SpotifyClientCredentials(client_id=self.bot.config.spotify_client_id, client_secret=self.bot.config.spotify_client_secret)
            spotify = spotipy.Spotify(client_credentials_manager=credentials)

            # If it's a playlist, then use the Spotify API to get the playlist and queue it.
            if 'playlist' in query:

                # Now, let's get all the results from Spotify properly into an array...
                playlist = []
                result = spotify.playlist_items(query)
                while result:
                    playlist.extend(result['items'])
                    result = spotify.next(result)

                # Now let's add them to the local playlist...
                for track in playlist:
                    self.bot.memory['music'][ctx.guild.id]['playlist'].append(self.parse_spotify_track(track['track']))
                
                # Inform we're done adding a playlist.
                message = await language.get(self, ctx, 'music.queued_playlist')
                await ctx.send(message.format(len(playlist)))
                added_playlist = True

            # Get the track if it's a track and queue it.
            elif 'track' in query:
                entry = self.parse_spotify_track(spotify.track(query))
                self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)

        # Check for a YouTube link, if so, handle that...
        elif 'youtube.com' in query or 'youtu.be' in query:

            # Check for a playlist first, if so, cancel, not supported (yet)...
            if 'playlist?list=' in query:
                return await ctx.send(await language.get(self, ctx, 'music.not_supported'))

            # Else it's just a song from YouTube, let's add that to the queue.
            else:
                entry = self.get_from_youtube(query)
                self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
            
        # If the query is still a hyperlink after previous catches, then cancel it, not supported.
        elif query.startswith('http://') or query.startswith('https://'):
            return await ctx.send(await language.get(self, ctx, 'music.not_supported'))

        # Else it's just a name of a song, let's search for it on YouTube and add it..
        else:
            entry = self.get_from_youtube(f'ytsearch:{query}')
            self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
             
        # Inform we've queued the song instead, ignore if it's a playlist.
        if not added_playlist:
            message = await language.get(self, ctx, 'music.queued')
            await ctx.send(message.format(
                entry['title']
            ))

        # Now let's see if we need to start playing directly, as in, nothing is playing...
        if not self.bot.memory['music'][ctx.guild.id]['playing']:
            self.bot.memory['music'][ctx.guild.id]['playing'] = True
            self.play_song(ctx, self.bot.memory['music'][ctx.guild.id]['playingIndex'])

    def play_song(self, ctx, index=None):
        """Function to actually play a song."""

        # Remove previous downloaded file.
        song_there = os.path.isfile(f'{ctx.guild.id}.mp3')
        try:
            if song_there:
                os.remove(f'{ctx.guild.id}.mp3')
        except:
            pass

        # Do we still have a queue or are we still in a channel? If one check fails then end.
        if ctx.guild.id not in self.bot.memory['music'] or ctx.voice_client is None or not self.bot.memory['music'][ctx.guild.id]['playing']:
            return

        # We need to fill the index if none is given, or maybe even stop in that case...
        if index is None:

            # Are we looping the track? Then we stick to the current playing index...
            if self.bot.memory['music'][ctx.guild.id]['playingLoop'] == 'track':
                index = self.bot.memory['music'][ctx.guild.id]['playingIndex']

            else:
                # We're going for the next in queue, so increment the playing index.
                index = self.bot.memory['music'][ctx.guild.id]['playingIndex'] + 1
                self.bot.memory['music'][ctx.guild.id]['playingIndex'] = index

                # Are we at the end of the queue?
                if len(self.bot.memory['music'][ctx.guild.id]['playlist']) <= index:

                    # End playing if we're not looping the queue.
                    if self.bot.memory['music'][ctx.guild.id]['playingLoop'] != 'queue':
                        self.bot.memory['music'][ctx.guild.id]['playing'] = False
                        return

                    # List is done, but we are looping. So, resetting the playing index.
                    self.bot.memory['music'][ctx.guild.id]['playingIndex'] = 0                
                    index = 0

        # Let's get the entry of next song.
        entry = self.bot.memory['music'][ctx.guild.id]['playlist'][index]

        # If the query is still a YouTube search, then let's do that first...
        if 'ytsearch:' in entry['query']:
            entry = self.get_from_youtube(entry['query'])

        # Declare the options for youtube-dl.
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': f'{ctx.guild.id}.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        # Declare the youtube-dl downloader and download the song.
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([entry['query']])

        # Now let's actually start playing..
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{ctx.guild.id}.mp3'), self.bot.memory['music'][ctx.guild.id]['volume'])
        ctx.voice_client.play(source, after=lambda e: self.play_song(ctx))

    def get_from_youtube(self, query):
        """Gets a track from YouTube, either by URL or search."""
            
        # Declare variables used in the function.
        meta = None
        ydl_opts = {
            'noplaylist': True,
            'quiet': True,
            'skip_download': True
        }

        # Download the metadata of the video.
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                meta = ydl.extract_info(query, download=False)

            # Sometimes an error occurs here for unknown reasons due to youtube-dl.
            # If it occurs, we will try to do the fixes below...
            except:

                # Append lyrics as first resort in case it's not done.
                if query.startswith('ytsearch:') and not query.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{query} lyrics', download=False)

                # Probably blocked or something, let's get the song title and do a search instead with lyrics on the end.
                elif 'youtube.com' in query or 'youtu.be' in query:
                    result = requests.get(query)
                    query = re.search('<\W*title\W*(.*)</title', result.text, re.IGNORECASE).group(1)[:-10]
                    meta = ydl.extract_info(f'ytsearch:{query} lyrics', download=False)

                # Now we really don't know...
                else:
                    raise

            # Fix for search, sometimes we won't get any results without lyrics being appened...
            # so we have to do a check here as well and run the extraction again but with lyrics appended this time.
            if 'duration' not in meta:
                if len(meta['entries']) < 1 and query.startswith('ytsearch:') and not query.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{query} lyrics', download=False)

                meta = meta['entries'][0]

        # Let's return the entry.
        return {
            'query': meta['webpage_url'],
            'title': meta['title'],
            'duration': meta['duration']
        }

    def parse_spotify_track(self, track):
        """Parse a track from Spotify to something useful for the bot."""

        # Get a proper query variable going.
        query = f"ytsearch:{track['name']} - {track['artists'][0]['name']}"
        if len(track['artists']) > 1:
            for i in range(1, len(track['artists'])):
                query += f", {track['artists'][i]['name']}"

        # Let's return the entry.
        return {
            'query': query,
            'title': f"{track['name']} - {track['artists'][0]['name']}",
            'duration': track['duration_ms']
        }

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # Only continue the code if there's only one user left which is the bot.
        if before.channel is None or len(before.channel.members) != 1 or before.channel.members[0].id != self.bot.user.id:
            return

        # Grace period of 10 seconds..
        await asyncio.sleep(10)

        # Cancel in case someone joined.
        if len(before.channel.members) != 1:
            return

        # So, it's the bot, and we're alone. Let's leave.
        voice_client = discord.utils.get(self.bot.voice_clients, guild=before.channel.guild)
        await voice_client.disconnect()

        # Clean up since we're done...
        del(self.bot.memory['music'][before.channel.guild.id])

    async def allowed_to_run_command_check(self, ctx, need_source):
        """Function to check if we are playing something, used for various commands above."""

        # Are we in a voice channel voice channel?
        if ctx.voice_client is None:
            await ctx.send(await language.get(self, ctx, 'music.not_in_channel'))
            return False
 
        # Make sure the person using the command is in a voice channel.
        if ctx.author.voice is None:
            await ctx.send(await language.get(self, ctx, 'music.user_not_in_channel'))
            return False
            
        # And also, in the same channel?
        if ctx.author.voice.channel is not ctx.voice_client.channel:
            await ctx.send(await language.get(self, ctx, 'music.not_in_same_channel'))
            return False

        # Ensure we have a source...
        if need_source and ctx.voice_client.source is None:
            await ctx.send(await language.get(self, ctx, 'music.not_playing'))
            return False

        # All is good...
        return True

def setup(bot):
    bot.add_cog(Music(bot))
