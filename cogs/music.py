import asyncio
import discord
import os
import youtube_dl

from datetime import datetime
from discord import FFmpegPCMAudio
from discord.ext import commands
from utils import data, embed, language

class Music(commands.Cog):
    """Commands for playing music in a voice channel."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Define memory variables...
        if 'music' not in self.bot.memory:
            self.bot.memory['music'] = {}

    @commands.command()
    @commands.guild_only()
    async def join(self, ctx):
        """Brings the bot to to the music channel."""

        # Make sure the person using the command is in a voice channel.
        if ctx.message.author.voice is None:
            message = await language.get(ctx, 'music.usernotinchannel')
            return await ctx.send(message.format(ctx.message.author.mention))

        # Are we in a voice client?
        if ctx.voice_client is not None:

            # Ignore if we are in the same channel already...
            if ctx.message.author.voice.channel is ctx.voice_client.channel:
                message = await language.get(ctx, 'music.alreadythere')
                return await ctx.send(message.format(ctx.message.author.mention))

            # Move to the same channel.
            await ctx.voice_client.move_to(ctx.message.author.voice.channel)

        # We're not in a channel but are going to now...
        else:
            await ctx.message.author.voice.channel.connect()

        # Do we have a playlist but not playing? Also known as techincal difficulty...
        if ctx.guild.id in self.bot.memory['music'] and ctx.voice_client.source is None:
            self.play_song(ctx)

    @commands.command()
    @commands.guild_only()
    async def leave(self, ctx):
        """Makes the bot leave the music channel."""

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            message = await language.get(ctx, 'music.botnotinchannel')
            return await ctx.send(message.format(ctx.message.author.mention))

        # Now leave.
        await ctx.voice_client.disconnect()

        # Destroy the queue if we had one...
        if ctx.guild.id in self.bot.memory['music']:
            del(self.bot.memory['music'][ctx.guild.id])

    @commands.command()
    @commands.guild_only()
    async def volume(self, ctx, volume: int):
        """Changes the volume."""

        # Can we run this command in the current context?
        if not self.allowed_to_run_command_check(ctx):
            return

        # Now let's change the volume...
        ctx.voice_client.source.volume = volume / 100
        message = await language.get(ctx, 'music.volume')
        await ctx.send(message.format(volume))

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song."""

        # Can we run this command in the current context?
        if not self.allowed_to_run_command_check(ctx):
            return

        # Let's pause the song...
        ctx.voice_client.pause()

    @commands.command()
    async def resume(self, ctx):
        """Resumes playing the current song."""

        # Can we run this command in the current context?
        if not self.allowed_to_run_command_check(ctx):
            return

        # Let's resume the song...
        ctx.voice_client.resume()

    @commands.command()
    @commands.guild_only()
    async def skip(self, ctx, volume: int):
        """Skips the current playing song."""

        # Can we run this command in the current context?
        if not self.allowed_to_run_command_check(ctx):
            return

        # Let's skip the song...
        ctx.voice_client.stop()
        await ctx.send(await language.get(ctx, 'music.skip'))

    async def allowed_to_run_command_check(self, ctx):
        """Function to check if we are playing something, used for various commands above."""

        # Are we in a voice channel voice channel?
        if ctx.voice_client is None:
            message = await language.get(ctx, 'music.botnotinchannel')
            await ctx.send(message.format(ctx.message.author.mention))
            return False
            
        # And also, in the same channel?
        if ctx.message.author.voice.channel is not ctx.voice_client.channel:
            message = await language.get(ctx, 'music.notsamechannel')
            await ctx.send(message.format(ctx.message.author.mention))
            return False

        # Ensure we have a source...
        if ctx.voice_client.source is None:
            message = await language.get(ctx, 'music.notplaying')
            await ctx.send(message.format(ctx.message.author.mention))
            return False

        # All is good...
        return True

    @commands.command()
    @commands.guild_only()
    async def playlist(self, ctx):
        """Shows the playlist of the bot if present."""

        # Do we have a queue or are we still in a channel? If not, no playlist.
        if ctx.guild.id not in self.bot.memory['music'] or ctx.voice_client is None:
            message = await language.get(ctx, 'music.notplaying')
            return await ctx.send(message.format(ctx.message.author.mention))

        # Define fields data with now playing.
        fields = {
            await language.get(ctx, 'music.playlist.now'): self.bot.memory['music'][ctx.guild.id][0]['title']
        }

        # Add the future entries to the fields data.
        if len(self.bot.memory['music'][ctx.guild.id]) < 2:
            fields.update({ await language.get(ctx, 'music.playlist.next'): await language.get(ctx, 'music.playlist.nothing') })
        else:
            fields.update({ await language.get(ctx, 'music.playlist.next'): '\n'.join([f"{i}) {self.bot.memory['music'][ctx.guild.id][i]['title']}" for i in range(1, len(self.bot.memory['music'][ctx.guild.id]))]) })

        # Send the embed...
        await ctx.send(embed=embed.create(
            title=await language.get(ctx, 'music.playlist.title'),
            description=await language.get(ctx, 'music.playlist.description'),
            fields=fields
        ))

    @commands.command()
    @commands.guild_only()
    async def play(self, ctx, url: str):
        """Plays or queues a song from YouTube, pass video id or url."""

        # This command only works when the bot is in a voice channel...
        if ctx.voice_client is None:
            message = await language.get(ctx, 'music.botnotinchannel')
            return await ctx.send(message.format(ctx.message.author.mention))
            
        # And also, only in the same channel...
        if ctx.message.author.voice.channel is not ctx.voice_client.channel:
            message = await language.get(ctx, 'music.notsamechannel')
            return await ctx.send(message.format(ctx.message.author.mention))
            
        # Declare youtube-dl options, simplified.
        ydl_opts = {
            'noplaylist': True,
            'skip_download': True,
            'quiet': True
        }

        # Start typing incidicator.
        await ctx.channel.trigger_typing()

        # Download the metadata of the video.
        meta = None
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(url, download=False)

            # Get how many seconds a song may be.
            max_duration = int(await self.bot.db.fetch(f"SELECT value FROM guild_settings WHERE guild_id = {ctx.guild.id} AND key = 'music.maxduration'"))

            # Only allow if it's not longer than set amount of minutes.
            if meta['duration'] > max_duration:
                message = await language.get(ctx, 'music.toolong')
                return await ctx.send(message.format(ctx.message.author.mention, max_duration))
                    
        # We can add it, let's define the object for in the queue.
        entry = {
            'url': url,
            'title': meta['title'],
            'duration': meta['duration'],
            'start': None
        }

        # Is there a queue already? If not, make one.
        if ctx.guild.id not in self.bot.memory['music']:
            self.bot.memory['music'][ctx.guild.id] = []

        # Now add the song the queue.
        self.bot.memory['music'][ctx.guild.id].append(entry)

        # Now let's see if we need to start playing directly, as in, nothing is playing...
        if not ctx.voice_client.is_playing():
            self.play_song(ctx)
            return await ctx.send(await language.get(ctx, 'music.start'))
                
        # Get total seconds in playlist.
        total_seconds = 0 - meta['duration']
        for i in range(0, len(self.bot.memory['music'][ctx.guild.id])):
            total_seconds += self.bot.memory['music'][ctx.guild.id][i]['duration']

        # Retract how far we are now in current song.
        total_seconds = total_seconds - (datetime.now() - self.bot.memory['music'][ctx.guild.id][0]['start']).total_seconds()

        # Declare variables for converting it into a nice figure...
        result = []
        intervals = (
            ('hours', 3600),    # 60 * 60
            ('minutes', 60),
            ('seconds', 1),
        )

        # Now make it readable for how long we need to wait for this song...
        for name, count in intervals:
            value = round(total_seconds // count)
            if value:
                total_seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))

        # Inform.
        message = await language.get(ctx, 'music.queued')
        await ctx.send(message.format(
            ctx.message.author.mention,
            len(self.bot.memory['music'][ctx.guild.id]) - 1,
            ', '.join(result[:2])
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

        # Do we have a queue or are we still in a channel? If not, end.
        if ctx.guild.id not in self.bot.memory['music'] or ctx.voice_client is None:
            return

        # Pop the previous song from the queue if we have to.
        if pop:
            self.bot.memory['music'][ctx.guild.id].pop(0)

        # Now let's make sure we still can play something, if not delete queue from memory.
        if len(self.bot.memory['music'][ctx.guild.id]) == 0:
            del(self.bot.memory['music'][ctx.guild.id])
            return

        # Now get an url, since we do have one in the queue.
        url = self.bot.memory['music'][ctx.guild.id][0]['url']

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
        if ctx.voice_client.source is not None:
            volume = ctx.voice_client.source.volume

        # Now let's actually start playing..
        self.bot.memory['music'][ctx.guild.id][0]['start'] = datetime.now()
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'{ctx.guild.id}.mp3'), volume)
        ctx.voice_client.play(source, after=lambda e: self.play_song(ctx, pop=True))

def setup(bot):
    bot.add_cog(Music(bot))
