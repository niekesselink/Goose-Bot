import asyncio
import discord

from datetime import datetime
from discord.ext import commands

class Secrets(commands.Cog):
    """Secret commands for some fun easter eggs."""

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 3600, commands.BucketType.guild)
    @commands.command(hidden=True)
    @commands.guild_only()
    async def AAAAAAAAAAAAAAAAH(self, ctx):
        """AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH."""

        # Only add this if there's one song in the queue so this one will be next.
        # Silent exit if conditions not met; it's an easter egg after all... sucks for cooldown.
        if ctx.guild.id not in self.bot.memory['music'] and len(self.bot.memory['music'][ctx.guild.id]) == 1:
            return

        # Define the entry...
        entry = {
            'url': 'mbIUn8TYKAU',
            'title': '**AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH**',
            'duration': 360,
            'start': None
        }

        # Get total seconds in playlist.
        total_seconds = 0
        for i in range(0, len(self.bot.memory['music'][ctx.guild.id])):
            total_seconds += self.bot.memory['music'][ctx.guild.id][i]['duration']

        # And queue it!
        self.bot.memory['music'][ctx.guild.id].append(entry)

        # We got it coming for ya...
        await ctx.send('Honk... ehm... **AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH**!')

        # Now let's start the AAAH script...
        self.bot.loop.create_task(self.do_aah_script(ctx, total_seconds))

    async def do_aah_script(self, ctx, wait_seconds):
        """Function that goes with the AAAAAAAAAAAAAAAAH easter egg..."""

        # Wait for start, plus five for download, you never know...
        await asyncio.sleep(wait_seconds + 5)

        # Declare old volume for later and set a block...
        old_volume = ctx.voice_client.source.volume

        # Wait for the right moment, increase volume when there... (2:00 in video)
        second_difference = (datetime.now() - self.bot.memory['music'][ctx.guild.id][0]['start']).total_seconds()
        await asyncio.sleep(120.5 - second_difference)
        ctx.voice_client.source.volume = 2

        # And now let's go AAAAAAH!
        await asyncio.sleep(16)
        await ctx.send(file=discord.File(f'assets/aaaaaah/1.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH')
        await asyncio.sleep(3)
        await ctx.send(file=discord.File(f'assets/aaaaaah/2.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH')
        await asyncio.sleep(3)
        await ctx.send(file=discord.File(f'assets/aaaaaah/3.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH')
        await asyncio.sleep(3.5)
        await ctx.send(file=discord.File(f'assets/aaaaaah/4.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH')
        await asyncio.sleep(3)
        await ctx.send(file=discord.File(f'assets/aaaaaah/5.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        await asyncio.sleep(9)
        await ctx.send(file=discord.File(f'assets/aaaaaah/6.jpg'), content='AAAAAAEH!')
        await asyncio.sleep(1)
        await ctx.send(file=discord.File(f'assets/aaaaaah/7.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        await asyncio.sleep(5)

        # Restore volume, it's bridge time, and wait...
        ctx.voice_client.source.volume = old_volume

        # Second but shorter wave incoming; getting ready!
        await asyncio.sleep(34)
        ctx.voice_client.source.volume = 2

        # Here we go, finale!
        await asyncio.sleep(1)
        await ctx.send(file=discord.File(f'assets/aaaaaah/8.jpg'), content='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAAAAAAAAH')
        await asyncio.sleep(14)

        # Restore volume, we're done now...
        ctx.voice_client.source.volume = old_volume

def setup(bot):
    bot.add_cog(Secrets(bot))
