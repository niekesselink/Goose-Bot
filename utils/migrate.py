import json

async def go(bot):
    """Function to apply newly set database changes for the bot."""

    # Loop through the guilds.
    for guild in bot.guilds:

        # Add the guild itself to the database.
        await bot.db.execute("INSERT INTO guilds (id) VALUES ($1)", guild.id)

        # Get config variables and add the default of it to the database if none present.
        with open('assets/json/settings.json') as content:
            configs = json.load(content)
            for config in configs:
                await bot.db.execute("INSERT INTO guild_settings (guild_id, key, value) VALUES ($1, $2, $3)", guild.id, config, configs[config])

        # Now loop through members and add them to the database as well.
        for member in guild.members:
            await bot.db.execute("INSERT INTO guild_members (guild_id, id) VALUES ($1, $2)", guild.id, member.id)
