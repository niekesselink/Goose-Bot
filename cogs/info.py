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
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgMembers = round(len(self.bot.users) / len(self.bot.guilds))

        # Define embed fields data.
        fields = {
            'Creator': '<@462311999980961793>',
            'Servers active': f'{len(ctx.bot.guilds)} (avg: {avgMembers} users/server)',
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

    @commands.command()
    async def invite(self, ctx):
        """Get a link to invite the bot to your own server."""
        message = await language.get(self, ctx, 'info.invite')
        await ctx.send(message.format(discord.utils.oauth_url(self.bot.user.id)))

    @commands.command()
    async def source(self, ctx):
        """Check out the bot's source code."""
        message = await language.get(self, ctx, 'info.source')
        await ctx.send(message.format('https://github.com/niekesselink/Goose-Bot'))

def setup(bot):
    bot.add_cog(Info(bot))
