import discord
import re
import requests

from discord.ext import commands
from io import BytesIO
from PIL import Image

class Memer(commands.Cog):

    def __init__(self, bot):
        """Initial function that runs when the class has been created."""
        self.bot = bot

    def get_avatar(self, ctx, mention):
        """Returns the avatar of a mentioned user, or it's own in case mention is invalid."""

        # Get the user
        user = ctx.author
        if mention is not None:
            user = ctx.guild.get_member(int(re.findall("\d+", mention)[0]))
            user = user if user is not None else ctx.author

        # Now, let's return the avatar...
        return self.get_image(user.avatar.url)

    def get_image(self, url):
        return Image.open(BytesIO(requests.get(url, stream=True).content))

    @commands.command()
    async def fakenews(self, ctx, user=None):

        # Prepare image and get user avatar
        base = Image.open('assets/memer/fakenews.bmp').convert('RGBA')
        avatar = self.get_avatar(ctx, user).resize((400, 400)).convert('RGBA')
        final_image = Image.new('RGBA', base.size)

        # Put the base over the avatar, and save the image.
        final_image.paste(avatar, (390, 0), avatar)
        final_image.paste(base, (0, 0), base)
        final_image = final_image.convert('RGBA')
        bytes = BytesIO()
        final_image.save(bytes, format='png')
        bytes.seek(0)

        # Now, let's send it.
        await ctx.send(file=discord.File(fp=bytes, filename='image.png'))

    @commands.command()
    async def slap(self, ctx, user):

        # Prepare image.
        base = Image.open('assets/memer/slap.bmp').resize((1000, 500)).convert('RGBA')
        avatar1 = self.get_image(ctx.author.avatar.url).resize((220, 220)).convert('RGBA')
        avatar2 = self.get_avatar(ctx, user).resize((200, 200)).convert('RGBA')

        base.paste(avatar1, (350, 70), avatar1)
        base.paste(avatar2, (580, 260), avatar2)
        base = base.convert('RGB')
        bytes = BytesIO()
        base.save(bytes, format='png')
        bytes.seek(0)

        # Now, let's send it.
        await ctx.send(file=discord.File(fp=bytes, filename='image.png'))

    @commands.command()
    async def spank(self, ctx, user):

        # Prepare image and get avatars.
        base = Image.open('assets/memer/spank.bmp').resize((500, 500))
        avatar1 = self.get_image(ctx.author.avatar.url).resize((140, 140)).convert('RGBA')
        avatar2 = self.get_avatar(ctx, user).resize((120, 120)).convert('RGBA')

        # Create image now.
        base.paste(avatar1, (225, 5), avatar1)
        base.paste(avatar2, (350, 220), avatar2)
        base = base.convert('RGBA')
        bytes = BytesIO()
        base.save(bytes, format='png')
        bytes.seek(0)

        # Now, let's send it.
        await ctx.send(file=discord.File(fp=bytes, filename='image.png'))

def setup(bot):
    bot.add_cog(Memer(bot))
