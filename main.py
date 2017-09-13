#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
'''
Usage:
    ./imap-email-checker [--config=PATH]

Options:
    -h --help                   Show this screen
    --config=PATH               Path to configuration file [default: ~/.imap-checker]
'''

import sys
import os
import re
import imaplib
import json
import logging
import webbrowser

from docopt import docopt
import notify2 as pynotify
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s %(message)s')
LOG = logging.getLogger(__name__)


def get_configuration(filepath: str) -> str:
    '''Get configuration from file'''
    try:
        with open(filepath, 'r') as conf_file:
            configuration_str = conf_file.read()
        configuration = json.loads(configuration_str)
    except IOError as io_error:
        configuration = {}
        LOG.error('could not read configuration file: %s', io_error)
        print('configuration file is needed with the following format:')
        print('''{
    "email": "name.surname@company.com",
    "server": "imap-server.com",
    "password": "xxxx",
    "time": "120",
    "notify": "on",
    "browser_url": ""
    "folders": ["INBOX", "Do not remove INBOX", "Another Folder"]
}''')
    sys.exit(1)

    return configuration


def open_browser_cb(notification, action: str, url: str):
    '''Open Outlook web page'''
    webbrowser.open_new_tab(url)
    notification.close()


def check_emails(account: dict) -> bool:
    '''Check unseen emails in folder'''

    server = account['server']
    email = account['email']
    password = account['password']
    folders = account['folders']

    conn = imaplib.IMAP4_SSL(server)

    ret, _ = conn.login(email, password)
    if ret != 'OK':
        LOG.fatal('could not login to the e-mail: %s', ret)

    report = dict()
    for folder in folders:
        ret, _ = conn.select(folder)
        if ret != 'OK':
            LOG.error('could not select folder %s: %s', folder, ret)
            continue

        ret, data = conn.status(folder, '(UNSEEN)')
        if ret != 'OK':
            LOG.error('could not check folder %s: %s', folder, ret)
            continue

        conn.close()

        unseen = int(re.search('[0-9]+', data[0].decode('utf-8')).group(0))
        LOG.debug('%d unseen email(s) in %s', unseen, folder)

        if unseen:
            report[folder] = unseen

    ret, _ = conn.logout()
    if ret != 'BYE':
        LOG.warning('could not logout: %s', ret)

    unseen = sum([unseen for unseen in report.values()])
    if unseen and unseen != account['unseen']:
        account['unseen'] = unseen

        LOG.debug("%d unseen e-email(s)", unseen)

        if account['notify'] == 'on':
            message = '{} unseen e-mails'.format(unseen)
            icon = '/usr/share/icons/Adwaita/scalable/status/mail-unread-symbolic.svg'
            notification = pynotify.Notification('PyEmail', message, icon)
            notification.add_action('accept', 'Open in browser',
                                    open_browser_cb, account['browser_url'])
            notification.show()

    return True


def main():
    '''Main function'''
    arguments = docopt(__doc__)
    print(arguments)
    config_file = os.path.expanduser(arguments['--config'])
    account = get_configuration(config_file)
    account['unseen'] = 0

    mainloop = GLib.MainLoop()
    GLib.timeout_add_seconds(int(account['time']), check_emails, account)

    pynotify.init('PyEmail', 'glib')

    mainloop.run()


if __name__ == '__main__':
    main()
