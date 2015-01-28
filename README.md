# imap-email-checher
E-mail (IMAP) checker in python with pop-up notification (uses libnotify python wrapper)

Script that checks every at intervals the provided email account (if IMAP is enable on server).

User's password is NOT stored anywhere. Credentials are provided at each run using [getpass](https://docs.python.org/2/library/getpass.html) python module.
  
  
