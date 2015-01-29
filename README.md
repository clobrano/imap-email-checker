# imap-email-checher
E-mail (IMAP) checker in python with pop-up notification (uses libnotify python wrapper)


**imap-email-checker** *checks* at configurable intervals (in minutes) the provided email account (if IMAP is enable on server).

User's password is NOT stored anywhere. Credentials can be provided at each run using [getpass](https://docs.python.org/2/library/getpass.html) python module or as command-line argument (in plain text this way, so be careful).

## Dependencies

* [docopt](http://docopt.org/)
