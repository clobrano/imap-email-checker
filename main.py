#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python :
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

import os
import re
import imaplib
import json
import logging
import webbrowser

import notify2 as pynotify
import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s %(funcName)s: %(message)s')
LOG = logging.getLogger(__name__)


def get_configuration(filepath: str) -> str:
    '''Get configuration from file'''
    try:
        with open(filepath, 'r') as conf_file:
            configuration_str = conf_file.read()
        configuration = json.loads(configuration_str)
    except IOError as io_error:
        configuration = {}
        print("Could not find configuration file: ", io_error)

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
    config_file = os.path.expanduser(os.path.join('~', '.imap-checker'))
    account = get_configuration(config_file)
    account['unseen'] = 0

    mainloop = GLib.MainLoop()
    GLib.timeout_add_seconds(int(account['time']), check_emails, account)

    pynotify.init('PyEmail', 'glib')

    mainloop.run()


if __name__ == '__main__':
    main()
