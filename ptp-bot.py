#!python3

import os
import json
import logging
import copy
import tabulate

import discord

from config import parse_config
import ptp
from argparsejson.argparsejson import parse_arguments

appdir = os.path.abspath(os.path.dirname(__file__))

COMMANDS = json.load(open(os.path.join(appdir, "ptp-commands.json"), "r"))
CLIENT_COMMANDS = copy.deepcopy(COMMANDS)
del CLIENT_COMMANDS["args"][1]
del CLIENT_COMMANDS["args"][0]

LOG = logging.getLogger(__name__)

class PTPClient(discord.AutoShardedClient):
    prefix = "!ptp"
    activity = discord.Activity(name=prefix, type=discord.ActivityType.listening)

    def __init__(self, ptp, parser):
        super().__init__()
        self._ptp = ptp
        self._parser = parser

    async def on_ready(self):
        LOG.info('Logged on as {}!'.format(self.user))
        await self.change_presence(activity=self.activity)

    async def on_message(self, message):
        if message.author == self.user:
            return

        inputargs = list(map(lambda x: x.lower(), message.content.split(' ')))
        if self.prefix != inputargs[0]:
            return

        inputargs.pop(0)

        LOG.info('Message from {0.author}: {0.content}'.format(message))

        async with message.channel.typing():
            try:
                args = self._parser.parse_args(inputargs)
            except:
                msg = self._parser.format_help()
                await message.channel.send(msg)
                return

            if args.action == "help" or args.action is None:
                msg = self._parser.format_help()
            elif args.action == "usage":
                msg = self._parser.format_usage()
            elif args.action == "freeleech" or args.action == "fl":
                try:
                    results = ptp.parse_ptp(self._ptp, args, returnJson=True)
                except ConnectionError:
                    msg = ":exclamation: *Unable to connect to PTP to perform your request. Please try again later!* :exclamation:"
                    await message.channel.send(msg)
                    return
                except Exception as e:
                    msg = ":exclamation: An exception occurred: *{}* :exclamation:".format(e)
                    await message.channel.send(msg)
                    return

                total = results.get('total', 0) if results else 0
                returned = results.get('returned', 0) if results else 0
                msg = "Currently freeleech (total:**{}** | returned:**{}**)\n".format(total, returned)
                await self._sendMessage(message, msg)

                if results:
                    await self._sendMovieResults(message, results.get('movies', []), returnJson=args.json)

                return
            elif args.action == "search" or args.action == "s":
                try:
                    results = ptp.parse_ptp(self._ptp, args, returnJson=True)
                except ConnectionError:
                    msg = ":exclamation: *Unable to connect to PTP to perform your request. Please try again later!* :exclamation:"
                    await message.channel.send(msg)
                    return
                except Exception as e:
                    msg = ":exclamation: An exception occurred: *{}* :exclamation:".format(e)
                    await message.channel.send(msg)
                    return

                total = results.get('total', 0) if results else 0
                returned = results.get('returned', 0) if results else 0
                msg = "Movies (total:**{}** | returned:**{}**)\n".format(total, returned)
                await self._sendMessage(message, msg)

                if results:
                    await self._sendMovieResults(message, results.get('movies', []), returnJson=args.json)

                return
            elif args.action == "summary" or args.action == "sum":
                try:
                    results = ptp.parse_ptp(self._ptp, args, returnJson=True)
                except ConnectionError:
                    msg = ":exclamation: *Unable to connect to PTP to perform your request. Please try again later!* :exclamation:"
                    await message.channel.send(msg)
                    return
                except Exception as e:
                    msg = ":exclamation: An exception occurred: *{}* :exclamation:".format(e)
                    await message.channel.send(msg)
                    return

                msg = "Current PTP Information\n\n"

                headers = [
                    ["Ratio", "Up", "Down", "Buffer", "Seeding"],
                    ["Bonus", "BPRate", "HNRs"]
                ]

                for h in headers:
                    table = [[]]
                    for x in h:
                        retrieved = results.get(x.lower())
                        if x.lower() == "up":
                            retrieved += " :arrow_up:"
                        elif x.lower() == "down":
                            retrieved += " :arrow_down:"
                        elif x.lower() == "hnrs":
                            retrieved += " :white_check_mark:"

                        table[0].append(retrieved)

                    msg += tabulate.tabulate(table, h, tablefmt="pretty")
                    msg += "\n\n"

                await self._sendMessage(message, msg)

                fl = results.get('fl', {}) if results else {}
                total = fl.get('total', 0)
                returned = len(fl.get('movies', []))
                msg = "Currently freeleech (total:**{}** | returned:**{}**)\n".format(total, returned)
                await self._sendMessage(message, msg)

                if returned > 0:
                    await self._sendMovieResults(message, fl.get('movies', []), returnJson=args.json)

                golden = len(fl.get('golden', []))
                msg = "\nCurrently golden freeleech (**{}**)\n".format(golden)
                await self._sendMessage(message, msg)

                if golden > 0:
                    await self._sendMovieResults(message, fl.get('golden', []), returnJson=args.json, detailed=args.detailed)

                return
            else:
                try:
                    msg = ptp.parse_ptp(self._ptp, args)
                    if args.json:
                        msg = "```\n{}\n```\n".format(json.dumps(msg, indent=1))
                except ConnectionError:
                    msg = ":exclamation: *Unable to connect to PTP to perform your request. Please try again later!* :exclamation:"
                    await message.channel.send(msg)
                    return

            if msg != '':
                for part in msg.split('\n\n'):
                    await message.channel.send(part + '\n\n')

    async def _sendMessage(self, message, msg):
        MAX_MSG_SIZE = 2000

        if len(msg) > MAX_MSG_SIZE:
            for p in range(0, len(msg), MAX_MSG_SIZE):
                calcRange = (p + MAX_MSG_SIZE) % len(msg)
                chunk = msg[p:p+calcRange]
                if len(chunk) > 0:
                    await message.channel.send(chunk)
        else:
            await message.channel.send(msg)

    async def _sendMovieResults(self, message, movies, returnJson=False, detailed=True):
        i = 1
        for m in movies:
            if returnJson:
                msg = "```\n{}\n```\n".format(json.dumps(m, indent=1))
            else:
                msg = "[{1}] **{0[Title]}** - {0[Year]}".format(m, i)
                if detailed:
                    msg += "\n>>>\t\t Tags: *{}*".format(', '.join(m["Tags"]))
                        
                    for t in m['Torrents']:
                        msg += "\n\t\t *{0[Codec]}/{0[Container]}/{0[Source]}/{0[Resolution]}*\t **[** {0[Seeders]} :arrow_up: **|** {0[Leechers]} :arrow_down: **]**\t Golden? {1}".format(t, ":white_check_mark:" if t["GoldenPopcorn"] else ":x:")
                    msg += "\n"
            await self._sendMessage(message, msg)
            i += 1

def main():
    parser = parse_arguments(COMMANDS)
    arguments = parser.parse_args()

    if arguments.debug:
      logging.basicConfig(level=logging.DEBUG)
    else:
      logging.basicConfig(level=logging.INFO)

    configfile = os.path.join(appdir, '.ptp.conf')
    config = parse_config(configfile)

    ptpobj = ptp.PTP(config.get('ptp', {}).get('ApiUser'), config.get('ptp', {}).get('ApiKey'), appdir, logger=LOG)

    clientparser = parse_arguments(CLIENT_COMMANDS, prog=PTPClient.prefix, add_help=False)

    client = PTPClient(ptpobj, clientparser)
    client.run(config.get('discord', {}).get('token'))

if __name__ == "__main__":
    main()
