#!python3

import os
import json
import logging
import copy

import ptp
from config import parse_config
from argparsejson.argparsejson import parse_arguments

appdir = os.path.abspath(os.path.dirname(__file__))

LOG = logging.getLogger(__name__)

COMMANDS = json.load(open(os.path.join(appdir, "ptp-commands.json"), "r"))

def perform_actions(PTPClient, args, parser=None):
    if args.i:
      print("-- PTP Interactive Mode --")
      while True:
        inputs = input("> ").lower()
        cmd = inputs.split(' ')[0]
        args = inputs.split(' ')[1:]
        if cmd in ["quit", "q"]:
          print("-- Exited --")
          return
        elif cmd == "help":
          parser.print_help()
        elif cmd == "usage":
          parser.print_usage()
        elif len(list(filter(lambda x: cmd in [x.get('name'), x.get('abbrev')], PTPClient.IMPLEMENTED))) == 0:
          LOG.critical("Invalid command '{}'.".format(cmd))
        else:
          newparser = parse_arguments(COMMANDS, prog="")
          newargs = newparser.parse_args([cmd] + args)
          perform_actions(PTPClient, newargs)

    else:
        msg = ptp.parse_ptp(PTPClient, args, returnJson=args.json)
        if args.json:
            print(json.dumps(msg, indent=2))
        else:
            print(msg)

def main():
    parser = parse_arguments(COMMANDS)
    arguments = parser.parse_args()

    if arguments.debug:
      logging.basicConfig(level=logging.DEBUG)

    LOG.debug(parser)
    LOG.debug(arguments)

    if arguments.action == "help" or (arguments.action is None and not arguments.i):
        parser.print_help()
        exit()

    if arguments.action == "usage":
        parser.print_usage()
        exit()

    configfile = os.path.join(appdir, '.ptp.conf')
    config = parse_config(configfile).get('ptp')

    ptpobj = ptp.PTP(config.get('ApiUser'), config.get('ApiKey'), appdir, logger=LOG)

    try:
        perform_actions(ptpobj, arguments, parser=parser)
    except ConnectionError:
        LOG.critical("Unable to connect to PTP to perform your request. Please try again later!")

if __name__ == "__main__":
    main()
