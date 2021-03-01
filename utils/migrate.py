import json

async def go(bot):
    """Function to apply newly set database changes for the bot."""

    # Loop through the guilds.
    for guild in bot.guilds:

        # Add the guild itself to the database.
        await bot.db.execute(f"INSERT INTO guilds (id) VALUES ({guild.id}) ON CONFLICT (id) DO NOTHING")

        # Get config variables and add the default of it to the database if none present.
        with open('assets/json/settings.json') as content:
            configs = json.load(content)
            for config in configs:
                await bot.db.execute(f"INSERT INTO guild_settings (guild_id, key, value) VALUES ({guild.id}, '{config}', '{configs[config]}') ON CONFLICT (guild_id, key) DO NOTHING")

        # Now loop through members and add them to the database as well.
        for member in guild.members:
            await bot.db.execute(f"INSERT INTO guild_members (guild_id ,id) VALUES ({guild.id}, {member.id}) ON CONFLICT (guild_id, id) DO NOTHING")
