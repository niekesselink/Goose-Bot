import discord
import os
import youtube_dl

from discord import FFmpegPCMAudio
from discord.ext import commands
from os import system
from utils import data

QUEUES = {}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = data.getjson('config.json')

    @commands.command(no_pm=True)
    async def join(self, ctx):
        """ Summons the goose to your voice channel """

        # Make sure the person using the command is in a voice channel
        if ctx.message.author.voice is None:
            await ctx.send('Honk honk. Get first in a channel yourself!')
            return

        # Now go to the channel nicely
        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command(no_pm=True)
    async def leave(self, ctx):
        """ Makes the goose leave any voice channel it is in """

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('Honk honk. I\'m not in a channel!')
            return

        # Now leave.
        await ctx.voice_client.disconnect()

    @commands.command(no_pm=True)
    async def volume(self, ctx, volume: int):
        """Changes the volume output of the bot"""

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('Honk honk. I\'m not in a channel!')
            return

        # Now let's change the volume...
        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Honk honk! I'll honk now at {}% volume.".format(volume))

    @commands.command(no_pm=True)
    async def play(self, ctx, url: str):
        """ Plays or queues a song from YouTube. Usage: .playsong [url] """

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('Honk honk. I\'m not in a channel!')
            return

        # And also, only in the same channel...
        if ctx.message.author.voice.channel is not ctx.voice_client.channel:
            await ctx.send('Honk honk. We\'re not in the same channel!')
            return

        # Declare youtube-dl options, simplified.
        ydl_opts = {
            'noplaylist': True
        }

        # Declare the youtube-dl downloader and start typing incidicator.
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            async with ctx.typing():

                # Download the metadata of the video
                meta = ydl.extract_info(url, download=False)

                # Only allow if it's not longer than set amount of minutes
                if meta['duration'] > self.config.music.maxduration:
                    await ctx.send(f'Honk honk. No, I\'m not going to honk longer than {self.config.music.maxduration} seconds.')
                    return

                # Are we playing already? If so, add the song to the queue.
                if ctx.voice_client.is_playing():

                    # Is there a queue already? If not, make one.
                    if ctx.guild.id not in QUEUES:
                        QUEUES[ctx.guild.id] = []

                    # Now add the song the queue.
                    QUEUES[ctx.guild.id].append(url)

                    # Inform and return.
                    await ctx.send('Honk honk. Song added to the queue!')
                    return

                # If code hits here, then there is no queue. Let's play.
                self.play_song(ctx, url)
                await ctx.send('Honk honk. Beginning to honk!')

    # Function to actually play a song.
    def play_song(self, ctx, url=None):

        # Remove previous downloaded file.
        song_there = os.path.isfile(f'{ctx.guild.id}.mp3')
        try:
            if song_there:
                os.remove(f'{ctx.guild.id}.mp3')
        except:
            return

        # If we don't have an url, then get one from the queue.
        if url is None:

            # First check if we actually have an entry, if not stop and clear queue.
            if len(QUEUES[ctx.guild.id]) == 0:
                del(QUEUES[ctx.guild.id])
                return

            # Now get an url, since we do have one in the queue.
            url = QUEUES[ctx.guild.id][0]
            QUEUES[ctx.guild.id].pop(0)

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
            ydl.download([url])

        # Set a proper volume...
        volume = self.config.music.volume
        if ctx.voice_client.source is not None:
            volume = ctx.voice_client.source.volume

        # Now let's actually start playing..
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{ctx.guild.id}.mp3'), volume)
        ctx.voice_client.play(source, after=lambda e: self.play_song(ctx))

def setup(bot):
    bot.add_cog(Music(bot))
