#!/usr/bin/env python3
import sys
import getopt
import random
import discord
import lib.token_handler
from lib.config import get_config
from lib.event_handler import EventHandler
from lib.misc_functions import add_random_reaction

# Check if valid python version
if not (sys.version_info.major == 3 and sys.version_info.minor >= 5 and sys.version_info.minor <= 6):
    print('Sorry, only works with python 3.5 or 3.6 right now')
    sys.exit(1)

# Load config/settings
try:
    random_reactions = get_config('random_reactions') == 'true'
    reaction_frequency = 1 - float(get_config('reaction_frequency'))
except Exception:
    print('Error parsing config file. Please ensure config/config.ini exists and is proper format')
    sys.exit(1)


def print_usage():
    message = """
    Usage: python3 bot.py [option] [arg]
        When ran without any arguments, the bot will attempt to start,
        loading the login token from the saved config

    -h --help       Display this help message
    -t --token      Run with a one-time token from this command line parameter
    -s --save-token Save a token from this command line parameter into the config file
    """
    print(message)


token = None
if len(sys.argv) > 1:
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ht:s:', ['help', 'token=', 'save-token='])
    except getopt.GetoptError:
        print_usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_usage()
            sys.exit(0)
        elif opt in ('-t', '--token'):
            token = arg
        elif opt in ('-s', '--save-token'):
            lib.token_handler.save_token(arg)
            print('Token saved\nRun again with no arguments to use with these saved credentials')
            sys.exit(0)
else:
    token = lib.token_handler.read_token()

if token:
    client = discord.Client()
    handler = EventHandler()

    @client.event
    async def on_ready():
        handler.initialize(client)
        await client.change_presence(game=discord.Game(name='Bepis'))
        print('Logged in as {}'.format(client.user.name))
        print('Invite Link: https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=2048'.format(client.user.id))
        print('------')

    @client.event
    async def on_message(message):
        if random_reactions:
            if random.random() > reaction_frequency:
                await add_random_reaction(client, message)
        await handler.handle_message(message)

    @client.event
    async def on_reaction_add(reaction, user):
        await handler.handle_reaction_add(reaction, user)

    print('Logging in and starting up...')
    try:
        client.run(token)
    except Exception as e:
        print(e)
        exit(1)
else:
    print_usage()
    exit(1)
