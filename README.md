# Goose Bot #

### Hybrid branch ###
Hello, welcome to the Goose Bot on the hybrid branch. Currently, this one is in development with three big features with two related to the bot's architecture. The first one is non-code modularity; people should be able to disable cogs per guild as well as setting permissions on each command individually. The second feature is Twitch integration; the bot should be working on Twitch as well for a specific sub-set of commands using the same code-base. The third feature is a website for controlling the bot.

To summarize;
* Better control about active cogs and permissions of each command per guild individually.
* Shared code-base for running on both Discord and Twitch.
* Website for administration.

### Introduction ###
Discord bot for spicing up a server and provide some fun. The code is open-source but this bot is running publicly on a VPS. I rather have you invite the bot yourself instead of starting up your own instance; this way I know if there are any issues lingering around quicker! The code is open-source for learning purposes and of course transparancy.

Use the link below to invite the bot to your server!
https://discordapp.com/oauth2/authorize?client_id=672445557293187128&scope=bot

Please note that this bot may not be perfect and may contain errors. If you encounter one, or you have a feature suggestion, you can use the Issues tab on Github or contact the owner of this bot on Discord at Niek#8930. Thanks!

### Requirements ###
* FFmpeg 
* PostgreSQL

### TODO ###
* Website for adding/controlling the bot
* Bot configuration per server
	* Limit cogs to certain channels
* Moderation features
	* Mute an user guild wise or channel wise
	* Block user from using the bot
	* Prune messages of an user
* Music feature
	* Role check on skip to force, else voting.
* Role management
	* Auto-add roles to new users
	* Click reaction to assign a role
