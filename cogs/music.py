import discord
import youtube_dl
import os

from discord.ext import commands
from discord import FFmpegPCMAudio
from os import system

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Makes the bot join your channel')
    async def join(self, ctx):
        # Make sure the person using the command is in a voice channel
        if ctx.message.author.voice is None:
            await ctx.send('Honk honk. Get first in a channel yourself bitch.')
            return

        # Now go to the channel nicely
        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command(brief='Makes the bot leave your channel')
    async def leave(self, ctx):
        # Leave nicely if we are in a channel, or tell otherwise
        if ctx.voice_client is None:
            await ctx.send('Honk honk. I\'m not there bitch.')
        else:
            await ctx.voice_client.disconnect()

    @commands.command(brief='This will play a song \'play [url]\'')
    async def play(self, ctx, url: str):
        # Get the previous downloaded audio file, remove it if we aren't playing already (file in use)
        song_there = os.path.isfile('audio.mp3')
        try:
            if song_there:
                os.remove('audio.mp3')
        except PermissionError:
            await ctx.send('Honk honk. No. Playing already bitch.')
            return

        # Define download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'outtmpl': 'audio.mp3',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        # Declare the youtube-dl downloader
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            # Download the metadata of the video
            meta = ydl.extract_info([url], download=False)

            # Only allow if it's not longer than 6 minutes
            if meta['duration'] > 360:
                await ctx.send('Honk honk. Nobody got time to listen to that.')
                return

            # We need to download it, inform the chat
            await ctx.send('Honk honk. Wait a little bit, getting the audio ready...')

            # Download from YouTube now, finish using the downloader
            ydl.download([url])

        # Now let's actually start playing
        ctx.voice_client.play(discord.FFmpegPCMAudio('audio.mp3'))

        # Inform that we are playing now
        await ctx.send('HONK HONK! PLAYING!')

def setup(bot):
    bot.add_cog(Music(bot))