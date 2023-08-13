import re
import subprocess

from discord.ext import commands
from utils import embed, language

class Info(commands.Cog):
    """Information commands about the bot."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command(alias=['profile'])
    @commands.guild_only()
    async def info(self, ctx: commands.Context, *, data: str=None):
        """Shows information about yours or someone elses their account."""

        # Get the correct data from the message.
        username = None
        if data is not None:
            data = data.split(' ', 1)
            username = data[0]

        # Get the user
        user = ctx.author
        if username is not None:

            # Only set the about field if username is 'set'.
            if username.lower() == 'set':
                await self.bot.db.execute("UPDATE guild_members SET about = $1 WHERE guild_id = $2 AND id = $3", data[1] if len(data) > 1 else '', ctx.guild.id, ctx.author.id)
                return await ctx.message.add_reaction('👌')

            # We're not setting, now check if user is getable, other just refer to yourself.
            user_id = re.findall("\d+", username)
            user = ctx.guild.get_member(int(user_id[0]) if len(user_id) > 0 else username)
            user = user if user is not None else ctx.author

        # Author field.
        author = {
            'name': f'{user.name}',
            'icon': user.avatar.url
        }

        # Get about field.
        about = await self.bot.db.fetch("SELECT about FROM guild_members WHERE guild_id = $1 AND id = $2", ctx.guild.id, user.id)
        about = about[0]['about'] if about[0]['about'] is not None else await language.get(self, ctx, 'info.empty_about')

        # Define embed fields data.
        fields = []
        fields.append({ 'name': await language.get(self, ctx, 'info.joined') + f' {ctx.guild.name}', 'value': user.joined_at.strftime('%d/%m/%Y'), 'inline': False })
        fields.append({ 'name': await language.get(self, ctx, 'info.created'), 'value': user.created_at.strftime('%d/%m/%Y'), 'inline': False })

        # Get additional fields from cogs.
        for cog in self.bot.cogs:
            cog = self.bot.get_cog(cog)
            if 'member_info_field' in dir(cog):
                field = await cog.member_info_field(ctx, user)
                if field is not None:
                    fields.append(field)

        # Create and send the embed.
        await ctx.send(embed=embed.create(
            self,
            description=about,
            colour=0x303136,
            fields=fields,
            author=author
        ))

    @commands.hybrid_command(alias='bot')
    async def botinfo(self, ctx: commands.Context):
        """Shows information about the bot."""

        # Get some data...
        guilds = await self.bot.db.fetch("SELECT COUNT(*) FROM guilds")
        guilds = int(guilds[0][0])
        members = await self.bot.db.fetch("SELECT COUNT(*) FROM guild_members")
        members = int(members[0][0])

        # Define embed fields data.
        fields = []
        fields.append({ 'name': 'Creator', 'value': '<@462311999980961793>', 'inline': False })
        fields.append({ 'name': 'Servers active', 'value': f'{guilds} ({members} total members)', 'inline': False })
        fields.append({ 'name': 'Last update', 'value': f'{subprocess.check_output(["git", "log", "-1", "--format=%cd "]).strip().decode("utf-8")}', 'inline': False })
        fields.append({ 'name': 'Source code', 'value': 'https://github.com/niekesselink/Goose-Bot', 'inline': False })

        # Create and send the embed.
        await ctx.send(embed=embed.create(
            self,
            title=await language.get(self, ctx, 'info.title'),
            description=await language.get(self, ctx, 'info.description'),
            colour=0x303136,
            thumbnail=ctx.bot.user.avatar.url,
            fields=fields
        ))

async def setup(bot):
    await bot.add_cog(Info(bot))
