#!/usr/bin/env python
'''
Usage:
	./imap-email-checker --email=ACCOUNT_ADDRESS --imap=IMAP_SERVER_ADDRESS [(--notify=on | --notify=off)] [--pass=PASSWORD] [--delay=MIN]

Options:
	-h --help	show this screen
	--email		e-mail address
	--imap		server imap address
	--pass		user's password
	--delay		minutes between checks
	--notify	enable/disable notify (uses libnotify). Default is on
'''

from docopt import docopt
import sys		# just for exit status
import imaplib
import getpass	# portable password input
import re		# regex library in order to extract unseen e-mails count
import pynotify	# binding for libnotify
import time

# ==============================================
# Get configuration values
# ==============================================
arguments = docopt(__doc__, version='IMAP E-mail checker')

EMAIL_ACCOUNT = arguments['--email']
EMAIL_IMAP_SERVER = arguments['--imap']


if arguments['--pass']:
	password = arguments['--pass']
else:
	password = getpass.getpass()

if arguments['--delay']:
	min = arguments['--delay']
else:
	min = 10	# 10 minutes delay between e-mail checks (default)

if arguments['--notify']:
	notify = arguments['--notify']
else:
	notify = 'on'	# notification enable by default


WAIT = 60 * min


if __name__ == '__main__':
	unseen = '0'

	while True:
		M = imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER)

		try:
			rv, data = M.login(EMAIL_ACCOUNT, password)
		except imaplib.IMAP4.error as err:
			print('Login failed. %s' % (err))
			sys.exit(1)

		if rv != 'OK':
			print('Login failed: %s' % (data[0]))
			sys.exit(1)

		rv, data = M.select('INBOX')
		if rv == 'OK':
			rv, data = M.status('INBOX', '(UNSEEN)')
			if rv == 'OK' and len(data) == 1:
				unseen = re.search('[0-9]+', data[0]).group(0)
				print('[%s] %s unseen e-mail(s), next check in %d minutes.' %\
						(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
							unseen,
							min))
			M.close()

		M.logout()

		if notify == 'on':
			if unseen != '0':
				pynotify.init('markup')
				notification = pynotify.Notification('PyEmail',
						'''
						<b>{0}</b> Unreed e-mail(s)
						'''.format(unseen))
				notification.show()

		time.sleep(WAIT)
