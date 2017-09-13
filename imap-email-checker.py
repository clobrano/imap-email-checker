#!/usr/bin/env python3
'''
Usage:
    ./imap-email-checker [--config=PATH] [--email=ACCOUNT_ADDRESS] [--imap=IMAP_SERVER_ADDRESS] [(--notify=on | --notify=off)] [--pass=PASSWORD] [--time=MIN] [--debug]

Options:
    -h --help                   Show this screen
    --email=ACCOUNT_ADDRESS     E-mail address
    --imap=IMAP_SERVER_ADDRESS  Server imap address
    --pass=PASSWORD             User's password
    --time=MIN                  Minutes between checks
    --notify=on|off             Enable/disable notify (uses libnotify). Default is on
    --debug                     Enable debug (stdout)
    --config=PATH               Path to configuration file [default: ~/.imap-checker]
'''

from docopt import docopt
import sys
import imaplib
import getpass
import re
import notify2 as pynotify
import time
import json
import os
import socket


def get_configuration(configuration_fullpath: str) -> str:
    try:
        with open(configuration_fullpath, 'r') as c:
            configuration_str = c.read()
        configuration = json.loads(configuration_str)
    except IOError as e:
        configuration = {}
        print("Could not find configuration file: {}".format(e))
    return configuration


def signal(message):
    if notify == 'on':
        pynotify.init('PyEmail')
        notification = pynotify.Notification('PyEmail', message)
        notification.show()


def log(message):
    if debug:
        print('[{time}] {message}'.format(
            time=format_time_hms(),
            message=message))


def error(message):
    print('[Error]: {0}'.format(message))


def format_time_hms():
    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    return time_str.split('.')[0]


def check_folder(connection, folder):
    rv, data = connection.select(folder)
    if rv == 'OK':
        rv, data = connection.status(folder, '(UNSEEN)')
        if rv == 'OK' and len(data) == 1:
            return int(re.search('[0-9]+', data[0].decode('utf-8')).group(0))
        connection.close()
    return 0


# ==============================================
# Get configuration values
# ==============================================
arguments = docopt(__doc__, version='IMAP E-mail checker')
if arguments['--config']:
    CONFIG = os.path.expanduser(arguments['--config'])
else:
    CONFIG = os.path.expanduser(os.path.join('~', '.imap-checker'))
configuration = get_configuration(CONFIG)

if arguments['--email']:
    EMAIL_ACCOUNT = arguments['--email']
elif configuration['email']:
    EMAIL_ACCOUNT = configuration['email']
else:
    log("No email account defined. Exiting...")
    sys.exit(1)

if arguments['--imap']:
    IMAP_SERVER = arguments['--imap']
elif configuration['server']:
    IMAP_SERVER = configuration['server']
else:
    log("No imap server defined. Exiting...")
    sys.exit(1)

# TODO better if we encrypt password but at the moment you can provide it securely from command line with getpass
if arguments['--pass']:
    password = arguments['--pass']
elif configuration['password']:
    password = configuration['password']
else:
    password = getpass.getpass()

if arguments['--time']:
    min = eval(arguments['--time'])
elif configuration['time']:
    min = int(configuration['time'])
else:
    min = 10    # 10 minutes delay between e-mail checks (default)

if arguments['--notify']:
    notify = arguments['--notify']
elif configuration['notify']:
    notify = configuration['notify']
else:
    notify = 'on'   # notification enable by default

debug = arguments['--debug']

WAIT = 60 * min


if __name__ == '__main__':
    unseen = 0
    connected = False

    while True:
        try:
            M = imaplib.IMAP4_SSL(IMAP_SERVER)
            rv, data = M.login(EMAIL_ACCOUNT, password)

            if 'OK' != rv:
                log('Could not connect to %s' % IMAP_SERVER)
                break

            elif not connected:
                connected = True
                log('Connected')

            new_unseen = 0
            updated_folders = []

            for folder in configuration['folders']:
                folder_unseen = check_folder(M, folder)
                log('{unseen} unseen e-mail(s) in {folder}, next check in {min} minutes.'
                    .format(unseen=folder_unseen, folder=folder, min=min))

                if folder_unseen > 0:
                    new_unseen += folder_unseen
                    updated_folders.append(folder)

            M.logout()

            if new_unseen == 0:
                unseen = new_unseen

            if new_unseen != unseen:
                if len(updated_folders) > 2:
                    signal('{num} Unseen email(s) in {folders} folder(s)'
                           .format(num=new_unseen, folders=len(updated_folders)))
                else:
                    signal('{num} Unseen email(s) in {folders}'
                           .format(num=new_unseen, folders=' and '.join(updated_folders)))
                unseen = new_unseen

        except imaplib.IMAP4.error as err:
            msg = '%s for user "%s" and imap server "%s"' % (err, EMAIL_ACCOUNT, IMAP_SERVER)
            error(msg)
            signal(msg)
            sys.exit(1)

        except (socket.timeout, socket.gaierror):
            pass

        time.sleep(WAIT)

    signal('Exiting')
