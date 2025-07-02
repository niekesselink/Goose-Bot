# Goose Bot
## Introduction
Discord bot for spicing up a server and provide some fun. The code is open-source but this bot is running publicly on a VPS. I rather have you invite the bot yourself instead of starting up your own instance; this way I know if there are any issues lingering around quicker! The code is open-source for learning purposes and of course transparancy. Í am self-hosting this bot for a few servers. If you're interested, reach out to me through a direct message.

Please note that this bot may not be perfect and may contain errors. If you encounter one, or you have a feature suggestion, you can use the Issues tab on Github or contact the owner of this bot on Discord at Niek#7864. Thanks!

## Note on playing music
To play music, the bot requires cookies. Sadly, it's a limitation made by YouTube.

You can get your cookies by logging into YouTube.com and then exporting them using the browser extension such as "Get cookies.txt LOCALLY" which I am using myself. Extract the cookies to a file called `cookies.txt` and place it in the root directory of the bot. The bot will automatically detect it and use it for playing music.

## Setup
There is a configuration file called `config.json.example` in the root directory of the bot. You can edit this file to change the bot's settings. In here, you also place your bot token, PostgeSQL connection string, Spotify API tokens and YouTube API tokens. Make sure to rename the file to `config.json` after editing it.

## Requirements
* FFmpeg 
* PostgreSQL