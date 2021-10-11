import asyncio
import discord
import os
import random
import re
import requests
import spotipy
import yt_dlp

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
        """Brings the bot to your voice channel."""

        # Make sure the user is in a voice channel.
        if ctx.author.voice is None:
            return await ctx.send(await language.get(self, ctx, 'music.user_not_in_channel'))

        # Are we in a voice client? If so, inform properly; we're somewhere else or already in your channel...
        if ctx.voice_client is not None:
            if ctx.author.voice.channel is ctx.voice_client.channel:
                return await ctx.send(await language.get(self, ctx, 'music.already_there'))
            return await ctx.send(await language.get(self, ctx, 'music.already_in_channel'))

        # Let's join the channel...
        await ctx.send(await language.get(self, ctx, 'music.leave')) if ctx.message is None else await ctx.message.add_reaction('👍')
        await self.join_channel(ctx)

    async def join_channel(self, ctx):
        """Function to join a voice channel and create bot memory."""

        # Let's join the channel...
        await ctx.author.voice.channel.connect()
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)

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

    async def is_allowed_to_use(ctx):
        """Function to check if user is in the channel with the bot."""

        # Make sure the user is in a voice channel.
        if ctx.author.voice is None:
            await ctx.send(await language.get(ctx, ctx, 'music.user_not_in_channel'))
            return False

        # Doing play command and not in a channel? Let's join the one of the user then.
        if ctx.command.name == "play" and ctx.voice_client is None:
            await ctx.cog.join_channel(ctx)

        # Are we still not in a voice channel? Then stop.
        if ctx.voice_client is None:
            await ctx.send(await language.get(ctx, ctx, 'music.not_in_channel'))
            return False 
        
        # Final check, are we in the same channel?
        if ctx.author.voice.channel is not ctx.voice_client.channel:
            await ctx.send(await language.get(ctx, ctx, 'music.not_in_same_channel'))
            return False

        # All good...
        return True

    @commands.command()
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def leave(self, ctx):
        """Makes the bot leave the channel."""

        # We're leaving...
        await ctx.send(await language.get(self, ctx, 'music.leave')) if ctx.message is None else await ctx.message.add_reaction('👋')
        await ctx.voice_client.disconnect()
        if ctx.guild.id in self.bot.memory['music']:
            del(self.bot.memory['music'][ctx.guild.id])

    @commands.command()
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def volume(self, ctx, level: int):
        """Changes the volume of the music."""

        # Ensure we have a source...
        if ctx.voice_client.source is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_playing'))

        # Now let's change the volume and inform...
        await ctx.send((await language.get(self, ctx, 'music.volume')).format(level))
        self.bot.memory['music'][ctx.guild.id]['volume'] = level / 100
        ctx.voice_client.source.volume = level / 100

    @commands.command()
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def skip(self, ctx):
        """Skips the current playing song."""

        # Ensure we have a source...
        if ctx.voice_client.source is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_playing'))

        # Let's skip the song...
        await ctx.send(await language.get(self, ctx, 'music.skip'))
        ctx.voice_client.stop()

    @commands.command()
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def clear(self, ctx):
        """Clears the current playlist."""
            
        # Clear the playlist.
        self.bot.memory['music'][ctx.guild.id]['playlist'] = []
        self.bot.memory['music'][ctx.guild.id]['playingIndex'] = 0

        # Stop playing and inform.
        await ctx.send(await language.get(self, ctx, 'music.cleared'))
        self.bot.memory['music'][ctx.guild.id]['playing'] = False
        ctx.voice_client.stop()

    @commands.command(aliases=['remove'])
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def delete(self, ctx, position):
        """Removes a song from the playlist at the given position."""

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

    @commands.command(aliases=['repeat'])
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def loop(self, ctx, trigger):
        """Loop the song, playlist or turn it off again."""
            
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
                index = self.bot.memory['music'][ctx.guild.id]['playingIndex'] = self.bot.memory['music'][ctx.guild.id]['playingIndex'] - 1
                self.start_play(ctx, index)

        # Start looping the whole queue.
        elif trigger == 'queue' or trigger == 'playlist':
            self.bot.memory['music'][ctx.guild.id]['playingLoop'] = 'queue'
            await ctx.send(await language.get(self, ctx, 'music.loop.queue'))

            # Now let's see if we need to start playing directly, as in, nothing is playing...
            if not self.bot.memory['music'][ctx.guild.id]['playing']:
                self.start_play(ctx)

        # Unknown trigger...
        else:
            message = await language.get(self, ctx, 'core.trigger_unknown')
            await ctx.send(message.format('track, queue, off'))
                
    @commands.command()
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def shuffle(self, ctx):
        """Shuffles the playlist."""

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

    @commands.command(aliases=['p'])
    @commands.guild_only()
    @commands.check(is_allowed_to_use)
    async def play(self, ctx, *, query: str):
        """Play a song or playlist by providing the name/artist or through an URL."""

        # If given, cut the audio filter away from the query into it's own.
        audioFilter = None
        if query.endswith(']') and '[' in query:
            audioFilter = re.search(r'\[.*?\]', query)[0][1:-1]
            query = query.replace(f' [{audioFilter}]', '')

        # Start typing incidicator.
        await ctx.channel.trigger_typing()

        # First, let's handle Spotify links.
        if 'spotify.com' in query and ('playlist' in query or 'track' in query):
            spotifyCredentials = SpotifyClientCredentials(client_id=self.bot.config.spotify_client_id, client_secret=self.bot.config.spotify_client_secret)
            spotify = spotipy.Spotify(client_credentials_manager=spotifyCredentials)

            # It's a playlist link...
            if 'playlist' in query:

                # Now, let's get all the results from Spotify properly into an array...
                playlist = []
                result = spotify.playlist_items(query)
                while result:
                    playlist.extend(result['items'])
                    result = spotify.next(result)

                # Now let's add them to the local playlist...
                for track in playlist:
                    entry = self.spotify_to_entry(track['track'], audioFilter)
                    self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
                
                # Inform we're done adding a playlist.
                message = await language.get(self, ctx, 'music.queued_playlist')
                await ctx.send(message.format(len(playlist)))

            # It's a track link...
            elif 'track' in query:
                entry = self.spotify_to_entry(spotify.track(query), audioFilter)
                self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
                await ctx.send((await language.get(self, ctx, 'music.queued')).format(entry['title']))

        # Secondly, let's handle YouTube links.
        elif 'youtube.com' in query or 'youtu.be' in query:

            # It's a playlist link... (Not supported yet)
            if 'playlist?list=' in query:
                return await ctx.send(await language.get(self, ctx, 'music.not_supported'))

            # It's a track link...
            else:
                entry = self.get_from_youtube(query, audioFilter)
                self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
                await ctx.send((await language.get(self, ctx, 'music.queued')).format(entry['title']))
            
        # If still a hyperlink, then it's not supported.
        elif query.startswith('http://') or query.startswith('https://'):
            return await ctx.send(await language.get(self, ctx, 'music.not_supported'))

        # Finally, search for the song on YouTube...
        else:
            entry = self.get_from_youtube(f'ytsearch:{query}', audioFilter)
            self.bot.memory['music'][ctx.guild.id]['playlist'].append(entry)
            await ctx.send((await language.get(self, ctx, 'music.queued')).format(entry['title']))

        # Now let's see if we need to start playing directly, as in, nothing is playing...
        if not self.bot.memory['music'][ctx.guild.id]['playing']:
            self.start_play(ctx, self.bot.memory['music'][ctx.guild.id]['playingIndex'])

    def spotify_to_entry(self, track, audioFilter=None):
        """Parse a track from Spotify to an in-house entry."""

        # Get a proper query variable including the name of all the artists.
        query = f"ytsearch:{track['name']} - {track['artists'][0]['name']}"
        if len(track['artists']) > 1:
            for i in range(1, len(track['artists'])):
                query += f", {track['artists'][i]['name']}"

        # Send back the entry.
        return {
            'query': query,
            'title': f"{track['name']} - {track['artists'][0]['name']}",
            'duration': track['duration_ms'],
            'audiofilter': audioFilter
        }

    def get_from_youtube(self, query, audioFilter=None):
        """Function to find and get information of a video on YouTube."""
            
        # Declare yt-dlp options.
        ydl_options = {
            'noplaylist': True,
            'quiet': True,
            'skip_download': True
        }

        # Time to find a video matching the result and get the information from it.
        # However, sometimes an error occurs, and thus, hacky fixes in the except handler.
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            try:
                meta = ydl.extract_info(query, download=False)
            except:

                # Append lyrics to the query if searching and if not there already...
                if query.startswith('ytsearch:') and not query.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{query} lyrics', download=False)

                # If it's an URL, we might be region blocked.
                # However, lyrics trick might work by getting song title from the page HTML's code.
                elif 'youtube.com' in query or 'youtu.be' in query:
                    result = requests.get(query)
                    query = re.search('<\W*title\W*(.*)</title', result.text, re.IGNORECASE).group(1)[:-10]
                    meta = ydl.extract_info(f'ytsearch:{query} lyrics', download=False)

                # Raise exception if no fixes applicable.
                else:
                    raise

            # In case of multiple results, take the first one. However, if there are no results given back then
            # we will re-attempt with the lyrics appended to the end of the search query...
            if 'duration' not in meta:
                if len(meta['entries']) < 1 and query.startswith('ytsearch:') and not query.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{query} lyrics', download=False)
                meta = meta['entries'][0]

        # Send back the entry.
        return {
            'query': meta['formats'][0]['url'],
            'title': meta['title'],
            'duration': meta['duration'],
            'audiofilter': audioFilter
        }

    def start_play(self, ctx, index=None):
        """Function to start playing."""
        self.bot.memory['music'][ctx.guild.id]['playing'] = True
        self.play_handler(ctx, index)

    def play_handler(self, ctx, index=None):
        """Function that serves as the play handler."""

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
            entry = self.get_from_youtube(entry['query'], entry['audiofilter'])

        # Now let's actually start playing..
        ffmpegOptions = f"-af \"{entry['audiofilter']}\"" if entry['audiofilter'] else None
        ffmpegOptionsBefore = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(entry['query'], options=ffmpegOptions, before_options=ffmpegOptionsBefore), self.bot.memory['music'][ctx.guild.id]['volume'])
        ctx.voice_client.play(source, after=lambda e: self.play_handler(ctx))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # Make sure the bot is the last one left before we continue the timeout period.
        if before.channel is None or len(before.channel.members) != 1 or before.channel.members[0].id != self.bot.user.id:
            return

        # Grace period of 10 second; cancel in case someone joins.
        await asyncio.sleep(10)
        if len(before.channel.members) != 1:
            return

        # Bot is leaving the channel...
        del(self.bot.memory['music'][before.channel.guild.id])
        voice_client = discord.utils.get(self.bot.voice_clients, guild=before.channel.guild)
        await voice_client.disconnect()

def setup(bot):
    bot.add_cog(Music(bot))
