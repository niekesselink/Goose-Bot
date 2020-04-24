import discord
import os
import youtube_dl

from discord import FFmpegPCMAudio
from discord.ext import commands

QUEUES = {}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def join(self, ctx):
        """ Summons the goose to your voice channel """

        # Make sure the person using the command is in a voice channel
        if ctx.message.author.voice is None:
            await ctx.send(f'**Honk honk.** Get first in a channel yourself {ctx.message.author.mention}!')
            return

        # Now go to the channel nicely
        channel = ctx.message.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        """ Makes the goose leave any voice channel it is in """

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('**Honk honk.** I\'m not in a channel!')
            return

        # Now leave.
        await ctx.voice_client.disconnect()

        # Destroy the queue if we had one...
        if ctx.guild.id in QUEUES:
            del(QUEUES[ctx.guild.id])

    @commands.command()
    @commands.guild_only()
    async def volume(self, ctx, volume: int):
        """ Changes the volume output of the bot """

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('**Honk honk.** I\'m not in a channel!')
            return

        # Ensure we have a source.
        if ctx.voice_client.source is None:
            await ctx.send(f'**Honk honk.** {ctx.message.author.mention}, why? I\'m not playing something!')
            return

        # Now let's change the volume...
        ctx.voice_client.source.volume = volume / 100
        await ctx.send("**Honk honk!** Oke, I'll honk now at {}% volume.".format(volume))

    @commands.command()
    @commands.guild_only()
    async def playlist(self, ctx):
        """ Shows the playlist of the bot if present """

        # Do we have a queue or are we still in a channel? If not, no playlist.
        if ctx.guild.id not in QUEUES or ctx.voice_client is None:
            await ctx.send('**Honk honk.** I\'m not playing anything!')
            return

        # Make an embed
        embed = discord.Embed(
            title='Goose\'s playlist',
            description='These are the songs I am honking or going to honk very soon! Remember, you can add songs by using .play followed by a YouTube URL or video id.',
            colour=self.bot.get_colour()
        )

        # Add what we are now playing.
        embed.add_field(name='Honking...', value=QUEUES[ctx.guild.id][0]['title'], inline=False)

        # And now what we are playing next, if something...
        if len(QUEUES[ctx.guild.id]) <= 1:
            embed.add_field(name='Honks upcoming...', value='Nothing :-(', inline=False)
        else:
            embed.add_field(name='Honks upcoming...',
                            value='\n'.join([f"{i}) {QUEUES[ctx.guild.id][i]['title']}" for i in range(1, len(QUEUES[ctx.guild.id]))]),
                            inline=False)

        # Send the embed...
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx, url: str):
        """ Plays or queues a song from YouTube, paste video id or url after .play! """

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            await ctx.send('**Honk honk.** I\'m not in a channel!')
            return

        # And also, only in the same channel...
        if ctx.message.author.voice.channel is not ctx.voice_client.channel:
            await ctx.send(f'**Honk honk.** We\'re not in the same channel {ctx.message.author.mention}!')
            return

        # Declare youtube-dl options, simplified.
        ydl_opts = {
            'noplaylist': True,
            'skip_download': True,
            'quiet': True
        }

        # Declare the youtube-dl downloader and start typing incidicator.
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            async with ctx.typing():

                # Download the metadata of the video
                meta = ydl.extract_info(url, download=False)

                # Only allow if it's not longer than set amount of minutes
                if meta['duration'] > self.bot.config.music.maxduration:
                    await ctx.send(f'**Honk honk.** {ctx.message.author.mention}, no, I\'m not going to honk longer than {self.bot.config.music.maxduration} seconds.')
                    return

                # First let's define the object for in the queue.
                entry = {
                    'url': url,
                    'title': meta['title']
                }

                # Is there a queue already? If not, make one.
                if ctx.guild.id not in QUEUES:
                    QUEUES[ctx.guild.id] = []

                # Now add the song the queue.
                QUEUES[ctx.guild.id].append(entry)

                # Now let's see if we need to start playing directly, as in, nothing is playing...
                if not ctx.voice_client.is_playing():
                    self.play_song(ctx)
                    await ctx.send('**Honk honk.** Beginning to honk!')
                    return

                # Inform and return.
                await ctx.send(f'**Honk honk.** {ctx.message.author.mention}, I\'ve added your song to the queue!\n'
                               f'Your song is at position #{len(QUEUES[ctx.guild.id]) - 1}, so be patient...')

    # Function to actually play a song.
    def play_song(self, ctx, pop=False):

        # Remove previous downloaded file.
        song_there = os.path.isfile(f'{ctx.guild.id}.mp3')
        try:
            if song_there:
                os.remove(f'{ctx.guild.id}.mp3')
        except:
            pass

        # Do we have a queue or are we still in a channel? If not, end.
        if ctx.guild.id not in QUEUES or ctx.voice_client is None:
            return

        # Pop the previous song from the queue if we have to.
        if pop:
            QUEUES[ctx.guild.id].pop(0)

        # Now let's make sure we still can play something, if not delete queue from memory.
        if len(QUEUES[ctx.guild.id]) == 0:
            del(QUEUES[ctx.guild.id])
            return

        # Now get an url, since we do have one in the queue.
        url = QUEUES[ctx.guild.id][0]['url']

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
        volume = self.bot.config.music.volume
        if ctx.voice_client.source is not None:
            volume = ctx.voice_client.source.volume

        # Now let's actually start playing..
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{ctx.guild.id}.mp3'), volume)
        ctx.voice_client.play(source, after=lambda e: self.play_song(ctx, pop=True))
        
def setup(bot):
    bot.add_cog(Music(bot))
