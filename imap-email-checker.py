#!/usr/bin/env python
'''
Usage:
	./imap-email-checker --email=ACCOUNT_ADDRESS --imap=IMAP_SERVER_ADDRESS [(--notify=on | --notify=off)] [--pass=PASSWORD] [--time=MIN] [--debug]

Options:
	-h --help	show this screen
	--email		e-mail address
	--imap		server imap address
	--pass		user's password
	--time		minutes between checks
	--notify	enable/disable notify (uses libnotify). Default is on
	--debug		enable debug (stdout)
'''

from docopt import docopt
import sys		# just for exit status
import imaplib
import getpass	# portable password input
import re		# regex library in order to extract unseen e-mails count
import pynotify	# binding for libnotify
import time
from datetime import datetime

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

if arguments['--time']:
	min = eval(arguments['--time'])
else:
	min = 10	# 10 minutes delay between e-mail checks (default)

if arguments['--notify']:
	notify = arguments['--notify']
else:
	notify = 'on'	# notification enable by default

debug = arguments['--debug']

WAIT = 60 * min

def signal(message):
	if notify == 'on':
		message += ' {0}'.format(datetime.now())
		pynotify.init('PyEmail')
		notification = pynotify.Notification('PyEmail', message)
		notification.show()


def log(message):
	if debug:
		print(message)

def error(message):
	print('[Error]: {0}'.format(message))

if __name__ == '__main__':
	unseen = '0'

	connected = False

	while True:
		try:
			M = imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER)

			rv, data = M.login(EMAIL_ACCOUNT, password)

			if 'OK' != rv:
				log ('Could not connect to %s' % EMAIL_IMAP_SERVER)

			elif not connected:
				connected = True
				log ('Connected')
				signal ('Connected')

				rv, data = M.select('INBOX')
				if rv == 'OK':
					rv, data = M.status('INBOX', '(UNSEEN)')
					if rv == 'OK' and len(data) == 1:
						unseen = re.search('[0-9]+', data[0]).group(0)
						log('[%s] %s unseen e-mail(s), next check in %d minutes.' %\
								(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
									unseen,
									min))
						M.close()

				M.logout()

				if unseen != '0':
					signal('%s Unseen email(s)' % unseen)


		except imaplib.IMAP4.error as err:
			msg = '%s for user "%s" and imap server "%s"' % (err, EMAIL_ACCOUNT, EMAIL_IMAP_SERVER)
			error(msg)
			signal(msg)
			sys.exit(1)

		except Exception as e:
			print(e)
			signal('Error: {0}'.format(e.strerror))
			if not 101 == e.errno:
				sys.exit(1)

		time.sleep(WAIT)
	
	signal ('Exiting')
