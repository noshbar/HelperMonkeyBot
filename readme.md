From http://iwasdeportedandalligotwasthislousydomain.co.uk/static.php?page=helpermonkeybotpython:

#Introduction

(Helper)MonkeyBot is a free note-taker/reminder/download-helper program with an instant-messenger interface, avoiding opening firewall ports, or having to SSH in to start a download on your home PC.

You basically use Google Talk to tell a program on your home PC to store/retrieve information for you, or to download files.

MonkeyBot is written in Python and is open source under the ZLib license, using SQLite for its database and SleekXMPP for instant messaging functionality.

#Features

* Store messages with different built-in/custom categories, e.g.,
todo:Kill everyone
* Remotely set up downloads to occur at specified times, e.g.,
download@9pm:http://noshbar.xtreemhost/files/monkeybot/monkeybot.py
* Set up reminders to be e-mailed and IM'd about, e.g.,
remind@2 Jul@13h00:Satan's birthday
* Show and delete existing messages
* Do full text searches through messages, optionally showing only URLs from messages that return a match, e.g.,
searchurls:3d*
* Uses the widely-supported XMPP protocol (so Google Talk works like a charm)
* No need to open an incoming port on your firewall, as the client connects out
* Single-web-page PHP utility to view and filter messages in a browser

#How to use

###Preparations:

* You will need a dedicated MonkeyBot chat account, so go ahead and create one e.g., GoMonkeyBotGo@gmail.com
* Add the new account as a chat contact so that you can see the MonkeyBot account in your IM Client.

###Dependencies:

* Python 2.7
* SQLite for Python with FTS4 support (OSX and Linux should be fine)
* SleekXMPP

###Starting the program:

* Either double-click the MonkeyBot Python script, or run it from a command-line with `python monkeybot.py`
* Enter the MonkeyBot username, in this case, GoMonkeyBotGo@gmail.com
* Enter the password for the MonkeyBot account
* Enter your account address as the one to listen to (MonkeyBot will not obey anyone else)
* Enter your secret handshake phrase. MonkeyBot will ignore anything until the magic phrase is typed.

Once that is done, you should see your GoMonkeyBotGo@gmail account come online in your chat window.
As soon as you type your magic phrase, you should see the MonkeyBot reply with a confirmation phrase, indicating it is ready for commands.

Note that the following command-line options are available:
- `-h show this help`
- `-u monkeybot-username`
- `-p monkeybot-password`
- `-g monkeybot-owner`
- `-k secret-handshake-phrase`
- `-f download-folder`
- `-s chat-server (if not talk.google.com)`
- `-d name-of-local-SQLite-database`
- `-c handshake-confirm-message (if "Listening..." does not suit)`
