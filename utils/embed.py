import discord

def create(self, title=None, description=None, colour=None, thumbnail=None, fields=None, author=None):
    """Function to create a Discord embed the easy way."""

    # Create the base embed.
    embed = discord.Embed(
        title='' if title is None else title,
        description='' if description is None else description,
        colour=discord.Color(value=int(self.bot.config.colour, 16)) if colour is None else colour,
    )

    # Add thumbnail if given.
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)

    # Add fields if necessary.
    if fields is not None:
        for field in fields:
            embed.add_field(name=field, value=fields[field], inline=False)

    # Add author if that is also given, also check for url and add if present.
    if author is not None:
        embed.set_author(name=author['name'], icon_url=author['icon'])

    # Return the completed embed.
    return embed