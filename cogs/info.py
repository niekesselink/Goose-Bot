import discord
import os
import psutil
import subprocess

from discord.ext import commands
from utils import embed, language

class Info(commands.Cog):
    """Information commands about the bot."""

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

        # Get reference to the current running process.
        self.process = psutil.Process(os.getpid())

    @commands.command()
    async def honk(self, ctx):
        """Honk honk."""

        # Send the first message.
        image1 = discord.Embed()
        image1.set_image(url='https://i.imgur.com/Jj5Pg0i.jpg')
        honk = await ctx.send(embed=image1)

        # Now let's get the difference from when we created the message and when it was created on server.
        difference = honk.created_at - ctx.message.created_at
        miliseconds = int(difference.total_seconds() * 1000)

        # Update previous message 
        image2 = discord.Embed()
        image2.set_image(url='https://i.imgur.com/OkcVNjy.jpeg')
        await honk.edit(embed=image2)
        
        #Send a new one with how long that take.
        message = await language.get(self, ctx, 'info.honk')
        await ctx.send(message.format(miliseconds))

    @commands.command()
    async def info(self, ctx):
        """Shows information about the Goose bot."""

        # Get some data...
        guilds = await self.bot.db.fetch("SELECT COUNT(*) FROM guilds")
        guilds = int(guilds[0][0])
        members = await self.bot.db.fetch("SELECT COUNT(*) FROM guild_members")
        members = int(members[0][0])
        ramUsage = self.process.memory_full_info().rss / 1024**2

        # Define embed fields data.
        fields = {
            'Creator': '<@462311999980961793>',
            'Servers active': f'{guilds} ({members} total members)',
            'Last update': f'{subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8")}',
            'RAM usage': f'{ramUsage:.2f} MB'
        }

        # Create and send the embed.
        await ctx.send(embed=embed.create(
            title=await language.get(self, ctx, 'info.title'),
            description=await language.get(self, ctx, 'info.description'),
            thumbnail=ctx.bot.user.avatar_url,
            fields=fields
        ))

        # Check if the guild count from database matches the one from the bot, if not, inform owner, but only for Goose bot!
        if self.bot.user.id == 672445557293187128 and len(ctx.bot.guilds) != guilds:
            owner = self.bot.get_user(462311999980961793)
            await owner.send("**ERROR** Guild count data mismatch!")

    @commands.command()
    async def source(self, ctx):
        """Check out the bot's source code."""
        message = await language.get(self, ctx, 'info.source')
        await ctx.send(message.format('https://github.com/niekesselink/Goose-Bot'))

def setup(bot):
    bot.add_cog(Info(bot))
