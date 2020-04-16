import discord

from discord.ext import commands
from utils import data

INSTALLED_COGS = [
    # 'cogs.aidungeon',
    'cogs.general',
    'cogs.image',
    'cogs.music',
]

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.log('Initialising bot', 'Goose-Bot')
        self.config = data.getjson('config.json')
        super().__init__(command_prefix=self.config.prefix, description=self.config.description, *args, **kwargs)

    def token(self):
        return self.config.token

    def log(self, value, name=None):
        print(f'[{name}]', value)

    def load(self, *cogs):
        for cog in cogs:
            self.load_extension(cog)
            self.log(f'Loaded {cog}', 'Goose-Bot')

    def unload(self, *cogs):
        for cog in cogs:
            self.unload_extension(cog)
            self.log(f'Unloaded {cog}', 'Goose-Bot')

    def reloadconfig (self):
        self.config = data.getjson('config.json')

    async def on_command(self, ctx):
        self.log(ctx.message.clean_content, ctx.author.name)

    async def on_ready(self):
        await self.user.edit(username=self.config.username)
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='humans.'),
            status=discord.Status.online
        )

    async def on_command_error(self, ctx, exception):
        if type(exception) == discord.ext.commands.errors.CommandNotFound:
            return

        await ctx.send(embed=discord.Embed(
            title='Oeps. A honking error...',
            description=f'`{str(exception)}`',
            colour=0xFF0000,
        ))

def main():
    bot = Bot()
    bot.load(*INSTALLED_COGS)
    bot.run(bot.token())

if __name__ == "__main__":
    main()
