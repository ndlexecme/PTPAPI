import os
import logging
import configparser

LOG = logging.getLogger(__name__)

def parse_config(configfile):
    if not os.path.isfile(configfile):
        LOG.critical("Missing config file '{}'!".format(configfile))
        LOG.critical("Please copy default config file '{}' to '{}' and fill in credentials.".format(os.path.join(appdir, '.ptp.conf.example'), configfile))
        exit(-1)

    config = configparser.ConfigParser()
    config.read(configfile)
    apiuser = config.get('Credentials', 'ApiUser')
    if apiuser == '':
        LOG.critical("Missing value for key '{}'!".format('ApiUser'))
        exit(-1)

    apikey = config.get('Credentials', 'ApiKey') 
    if apikey == '':
        LOG.critical("Missing value for key '{}'!".format('ApiKey'))
        exit(-1)

    discordtoken = config.get('Discord', 'Token') 
    if discordtoken == '':
        LOG.critical("Missing value for key '{}'!".format('Token'))
        exit(-1)

    return {
        'ptp': {'ApiUser': apiuser, 'ApiKey': apikey},
        'discord': {'token': discordtoken}
    }

def parse_env():
    apiuser = os.environ.get('PTP_APIUSER')
    if apiuser == '':
        LOG.critical("Missing environment variable '{}'!".format('PTP_APIUSER'))
        exit(-1)

    apikey = os.environ.get('PTP_APIKEY') 
    if apikey == '':
        LOG.critical("Missing environment variable '{}'!".format('PTP_APIKEY'))
        exit(-1)

    discordtoken = os.environ.get('PTP_DISCORD_TOKEN') 
    if discordtoken == '':
        LOG.critical("Missing environment variable '{}'!".format('PTP_DISCORD_TOKEN'))
        exit(-1)

    return {
        'ptp': {'ApiUser': apiuser, 'ApiKey': apikey},
        'discord': {'token': discordtoken}
    }
