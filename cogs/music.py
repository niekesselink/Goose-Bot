import asyncio
import discord
import os
import spotipy
import youtube_dl

from datetime import datetime
from discord import FFmpegPCMAudio
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from utils import language

class Music(commands.Cog):
    """Commands for playing music in a voice channel."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Define memory variables...
        if 'music.playlists' not in self.bot.memory:
            self.bot.memory['music.playlists'] = {}
        if 'music.volumes' not in self.bot.memory:
            self.bot.memory['music.volumes'] = {}

    @commands.command()
    @commands.guild_only()
    async def join(self, ctx):
        """Brings the bot to to the music channel."""

        # Make sure the person using the command is in a voice channel.
        if ctx.author.voice is None:
            return await ctx.send(await language.get(self, ctx, 'music.user_not_in_channel'))

        # Are we in a voice client?
        if ctx.voice_client is not None:

            # Just a message in case it's the same channel...
            if ctx.author.voice.channel is ctx.voice_client.channel:
                return await ctx.send(await language.get(self, ctx, 'music.already_there'))

            # Inform that we are already in a channel.
            return await ctx.send(await language.get(self, ctx, 'music.already_in_channel'))

        # We're not in a channel but are going to now...
        else:
            await ctx.author.voice.channel.connect()

        # Let's deafen ourselves...
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel, self_deaf=True)

        # Create a playlist if not present.
        if ctx.guild.id not in self.bot.memory['music.playlists']:
            self.bot.memory['music.playlists'][ctx.guild.id] = []

        # Do we have a playlist but not playing? Let's start playing again then...
        if len(self.bot.memory['music.playlists'][ctx.guild.id]) > 0 and ctx.voice_client.source is None:
            self.play_song(ctx)

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        """Makes the bot leave the music channel."""

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_in_channel'))

        # Now leave and react.
        await ctx.voice_client.disconnect()
        await ctx.message.add_reaction('👋')

        # Clean up since we're done...
        self.clean_up(ctx.guild.id)

    @commands.command(aliases=['playing', 'np'])
    @commands.guild_only()
    async def now(self, ctx):
        """Shows the current playing song."""

        # Do we have a queue or are we still in a channel? If not, no playlist.
        if ctx.guild.id not in self.bot.memory['music.playlists'] or ctx.voice_client is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_playing'))
        
        # Send what we are playing now.
        message = await language.get(self, ctx, 'music.now')
        await ctx.send(message.format(self.bot.memory['music.playlists'][ctx.guild.id][0]['title']))

    @commands.command(aliases=['queue', 'q'])
    @commands.guild_only()
    async def playlist(self, ctx):
        """Shows the playlist of the bot if present."""

        # Do we have a queue or are we still in a channel? If not, no playlist.
        if ctx.guild.id not in self.bot.memory['music.playlists'] or ctx.voice_client is None:
            return await ctx.send(await language.get(self, ctx, 'music.not_playing'))

        # Is there something coming up, if not just a plain message.
        if len(self.bot.memory['music.playlists'][ctx.guild.id]) < 2:
            return await ctx.send(await language.get(self, ctx, 'music.playlist.nothing'))

        # Declare top part of the message...
        message = await language.get(self, ctx, 'music.playlist')
        message += '```nim\n   ⬐ {0}\n0) {1}'.format(await language.get(self, ctx, 'music.playlist.now'), self.bot.memory['music.playlists'][ctx.guild.id][0]['title'])
        message += '\n\n   ⬐ {0}\n'.format(await language.get(self, ctx, 'music.playlist.next'))

        # Add all the songs we have queued.
        if len(self.bot.memory['music.playlists'][ctx.guild.id]) > 1:
            for i in range(1, len(self.bot.memory['music.playlists'][ctx.guild.id])):
                message += '{0}) {1}\n'.format(i, self.bot.memory['music.playlists'][ctx.guild.id][i]['title'])

        # Add an end message and send.
        message += '\n{0}```'.format(await language.get(self, ctx, 'music.playlist.end'))
        return await ctx.send(message)

    @commands.command()
    @commands.guild_only()
    async def volume(self, ctx, volume: int):
        """Changes the volume."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, True):
            return

        # Now let's change the volume...
        ctx.voice_client.source.volume = volume / 100
        self.bot.memory['music.volumes'][ctx.guild.id] = volume / 100

        # Inform as well.
        message = await language.get(self, ctx, 'music.volume')
        await ctx.send(message.format(volume))

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

    @commands.command(aliases=['p'])
    @commands.guild_only()
    async def play(self, ctx, *, url: str):
        """Plays or queues a song from YouTube, pass video id or url."""

        # Can we run this command in the current context?
        if not await self.allowed_to_run_command_check(ctx, False):
            return
            
        # Declare youtube-dl options, simplified.
        ydl_opts = {
            'noplaylist': True,
            'skip_download': True,
            'quiet': True
        }

        # Start typing incidicator.
        await ctx.channel.trigger_typing()

        # Extract the right data in case it's a Spotify link, we want to make it a search string.
        if 'spotify.com' in url:

            # First, let's set up a connection to Spotify to do so through Spotipy and get information about the track from the URL.
            credentials = SpotifyClientCredentials(client_id=self.bot.config.spotify_client_id, client_secret=self.bot.config.spotify_client_secret)
            spotify = spotipy.Spotify(client_credentials_manager=credentials)
            track = spotify.track(url)

            # Now format it with all the possible artists.
            url = f"{track['name']} - {track['album']['artists'][0]['name']}"
            if len(track['album']['artists']) > 1:
                for i in range(1, len(track['album']['artists'])):
                    url += f", {track['album']['artists'][i]['name']}"
            
        # If the url is not from YouTube then we search for the first fitting result matching the search string...
        if not 'youtube.com' in url and not 'youtu.be' in url:
            url = f'ytsearch:{url}'

        # Download the metadata of the video.
        meta = None
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:

            # Sometimes an error occurs here for unknown reasons due to youtube-dl.
            # If it occurs, we will try again by appending lyrics, but only if it's not a hyperlink and we didn't do it before already...
            try:
                meta = ydl.extract_info(url, download=False)
            except:
                if url.startswith('ytsearch:') and not url.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{url} lyrics', download=False)
                else:
                    raise

            # Get how many seconds a song may be.
            db_result = await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {ctx.guild.id} AND key = 'music.max_duration'")
            max_duration = int(db_result[0]['value'])

            # Fix for search, sometimes we won't get any results without lyrics being appened...
            # so we have to do a check here as well and run the extraction again but with lyrics appended this time.
            if 'duration' not in meta:
                if len(meta['entries']) < 1 and url.startswith('ytsearch:') and not url.endswith(' lyrics'):
                    meta = ydl.extract_info(f'{url} lyrics', download=False)

                meta = meta['entries'][0]

            # Only allow if it's not longer than set amount of minutes.
            if meta['duration'] > max_duration or meta['is_live']:
                message = await language.get(self, ctx, 'music.too_long')
                return await ctx.send(message.format(max_duration))
                    
        # We can add it, let's define the object for in the queue.
        entry = {
            'url': meta['webpage_url'],
            'title': meta['title'],
            'duration': meta['duration'],
            'start': None
        }

        # Now add the song the queue.
        self.bot.memory['music.playlists'][ctx.guild.id].append(entry)

        # Now let's see if we need to start playing directly, as in, nothing is queued to play...
        if len(self.bot.memory['music.playlists'][ctx.guild.id]) == 1:
            message = await language.get(self, ctx, 'music.start')
            await ctx.send(message.format(meta['title']))
            return self.play_song(ctx)
                
        # Get total seconds in playlist.
        total_seconds = 0 - meta['duration']
        for i in range(0, len(self.bot.memory['music.playlists'][ctx.guild.id])):
            total_seconds += self.bot.memory['music.playlists'][ctx.guild.id][i]['duration']

        # Retract how far we are now in current song.
        if self.bot.memory['music.playlists'][ctx.guild.id][0]['start'] is not None:
            total_seconds = total_seconds - (datetime.now() - self.bot.memory['music.playlists'][ctx.guild.id][0]['start']).total_seconds()

        # Declare variables for converting it into a nice figure...
        result = []
        intervals = (
            ('core.hours', 3600), # 60 * 60
            ('core.minutes', 60),
            ('core.seconds', 1)
        )

        # Now make it readable for how long we need to wait for this song...
        for name, count in intervals:
            value = round(total_seconds // count)
            if value:
                total_seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, await language.get(self, ctx, name)))

        # Inform.
        message = await language.get(self, ctx, 'music.queued')
        separator = await language.get(self, ctx, 'core.separator')
        await ctx.send(message.format(
            len(self.bot.memory['music.playlists'][ctx.guild.id]) - 1,
            result[0] if len(result) == 1 else f' {separator} '.join([', '.join(result[:-1]), result[-1]]),
            meta['title']
        ))

    def play_song(self, ctx, pop=False):
        """Function to actually play a song."""

        # Remove previous downloaded file.
        song_there = os.path.isfile(f'{ctx.guild.id}.mp3')
        try:
            if song_there:
                os.remove(f'{ctx.guild.id}.mp3')
        except:
            pass

        # Do we still have a queue or are we still in a channel? If one check fails then end.
        if ctx.guild.id not in self.bot.memory['music.playlists'] or ctx.voice_client is None:
            return

        # Pop the previous song from the queue if we have to.
        if pop:
            self.bot.memory['music.playlists'][ctx.guild.id].pop(0)

        # Now let's make sure we still can play something...
        if len(self.bot.memory['music.playlists'][ctx.guild.id]) == 0:
            return

        # We can still play, let's get the next song.
        url = self.bot.memory['music.playlists'][ctx.guild.id][0]['url']

        # Declare the options for youtube-dl.
        ydl_opts = {
            'noplaylist': True,
            'format': 'bestaudio/best',
            'outtmpl': f'{ctx.guild.id}.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        # Declare the youtube-dl downloader and download the song.
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Set a proper volume...
        volume = 1
        if ctx.guild.id in self.bot.memory['music.volumes']:
            volume = self.bot.memory['music.volumes'][ctx.guild.id]

        # Now let's actually start playing..
        self.bot.memory['music.playlists'][ctx.guild.id][0]['start'] = datetime.now()
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{ctx.guild.id}.mp3'), volume)
        ctx.voice_client.play(source, after=lambda e: self.play_song(ctx, pop=True))

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
        self.clean_up(before.channel.guild.id)

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

    def clean_up(self, guild_id):
        """Function to clean up the playing bot for a guild."""

        # Destroy the queue if we had one...
        if guild_id in self.bot.memory['music.playlists']:
            del(self.bot.memory['music.playlists'][guild_id])

        # Destory the stored volume.
        if guild_id in self.bot.memory['music.volumes']:
            del(self.bot.memory['music.volumes'][guild_id])

def setup(bot):
    bot.add_cog(Music(bot))
