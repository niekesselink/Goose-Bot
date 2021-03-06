﻿import discord

def create(title, description, thumbnail=None, fields=None):
    """Function to create a Discord embed the easy way."""

    # Create the base embed.
    embed = discord.Embed(
        title=title,
        description=description,
        colour=0x73BBFF,
    )

    # Add thumbnail if given.
    if thumbnail is not None:
        embed.set_thumbnail(url=thumbnail)

    # Add fields if necessary.
    if fields is not None:
        for field in fields:
            embed.add_field(name=field, value=fields[field], inline=False)

    # Return the completed embed.
    return embed