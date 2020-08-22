# PTPAPI
## Prerequisites
* `python3`
* `pip3`

## Getting Started with the CLI
1. `pip3 install -r requirements.txt`
2. Copy `.ptp.conf.example` to `.ptp.conf` and fill in credentials (from Edit -> Security).
3. `python3 ptp-cli.py -h` for help

## Getting Started with the Discord Bot (standalone)
1. `pip3 install -r requirements.txt`
2. Copy `.ptp.conf.example` to `.ptp.conf` and fill in credentials (from Edit -> Security).
3. Create a new Discord App, then create a new Discord Bot for the app and copy and fill in the bot token value in the `.ptp.conf` file.
4. Using the client id for your Discord *App*, run the `authBot.sh <client-id>` script to authorize the Discord bot.
5. `python3 ptp-bot.py`
6. Send `!ptp help` to the PTP Discord bot for more help.

## Getting Started with the Discord Bot (docker-compose)
1. Copy `.ptp_docker.env.example` to `.ptp_docker.env` and fill in credentials (from Edit -> Security).
2. Create a new Discord App, then create a new Discord Bot for the app and copy and fill in the bot token value in the `.ptp_docker.env` file.
3. Using the client id for your Discord *App*, run the `authBot.sh <client-id>` script to authorize the Discord bot.
4. `docker-compose up`
5. Send `!ptp help` to the PTP Discord bot for more help.
