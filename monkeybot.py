#!/usr/bin/python
# -*- coding: utf-8 -*-

# ZLib license:# Copyright (c) 2012 Dirk de la Hunt#
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.# Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.# 3. This notice may not be removed or altered from any source distribution.
import sqlite3 as lite
import sys
import time
import datetime
import os
import re
import logging
import argparse
import getpass

from DateTimeParser import DateTimeParser
from OperationThread import OperationThread

from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout

class MonkeyBot(ClientXMPP):
    God = ''
    Username = ''
    Password = ''
    Server   = ''
    PassPhrase = ''
    ConfirmPhrase = ''
    Database = None
    UrlRegEx = None
    ReplyTo  = None
    WorkingFolder = None
    DownloadFolder = None
    LastChatted = 0
    LastInsertedID = -1
    CurrentDatabase = None #string containing current database path

    idle = False

    def makeUrlFinderRegEx(self):
        urls = '(?: %s)' % '|'.join("""http https svn telnet gopher file wais ftp""".split())
        ltrs = r'\w'
        gunk = r'/#~:.?+=&%@!\-'
        punc = r'.:?\-'
        any = "%(ltrs)s%(gunk)s%(punc)s" % { 'ltrs' : ltrs,
                                             'gunk' : gunk,
                                             'punc' : punc }

        url = r"""
            \b                            # start at word boundary
                %(urls)s    :             # need resource and a colon
                [%(any)s]  +?             # followed by one or more
                                          #  of any valid character, but
                                          #  be conservative and take only
                                          #  what you need to....
            (?=                           # look-ahead non-consumptive assertion
                    [%(punc)s]*           # either 0 or more punctuation
                    (?:   [^%(any)s]      #  followed by a non-url char
                        |                 #   or end of the string
                          $
                    )
            )
            """ % {'urls' : urls,
                   'any' : any,
                   'punc' : punc }

        self.UrlRegEx = re.compile(url, re.VERBOSE | re.MULTILINE)
        return self.UrlRegEx

    def SendMessage(self, Messages):
        try:
            for message in Messages:
                if (self.ReplyTo):
                    self.send_message(mto=self.ReplyTo, mbody=message)
        except:
            print(sys.exc_info()[0])
        return

    def changeDatabase(self, Action, Contents):
        if (self.Database):
            self.Database.close()

        self.CurrentDatabase = None

        if (os.path.isfile(Contents)):
            try:
                self.Database = lite.connect(Contents, check_same_thread = False)
                if (self.Database):
                    self.CurrentDatabase = Contents
                    return ['Database changed to: ' + Contents]
                else:
                    return ['Database could not be changed to: ' + Contents]
            except lite.Error, e:
                return ['Exception throw trying to change database to: ' + Contents, e.args[0]]

        try:
            self.Database = lite.connect(Contents, check_same_thread = False)
            if (self.Database):
                tables = [
                "CREATE TABLE category(id integer primary key, destFolder varchar(512), description varchar(64));",
                "CREATE TABLE filter(id integer primary key, description varchar(64), type integer, byteOffset integer, bytes varchar(32), categoryId integer, minFileSize integer);",
                "CREATE TABLE url(id integer primary key, messageId integer, url varchar(2048), visitedCount integer, added integer);",
                "CREATE VIRTUAL TABLE messages USING fts4(contents);",
                "CREATE TABLE operation(id integer primary key, start integer, finished integer, status integer);",
                "CREATE TABLE message(id integer primary key, messageId integer, added integer, showCount integer, readCount integer, action varchar(32), deleted integer);"
                ]
                cursor = self.Database.cursor()
                for table in tables:
                    cursor.execute(table)
                self.Database.commit()
                self.CurrentDatabase = Contents
                return ['Database created at: ' + Contents]
            else:
                return ['Could not create database at: ' + Contents]
        except lite.Error, e:    
            return ["Database error %s: " % e.args[0]]
                
        return ['Unknown error changing database: ' + Contents]

    def processURLs(self, Action, Contents, MessageId):
        when = DateTimeParser().parseDateTime(self.getActionTime(Action))
        if (not when):
            when = int(time.time())
        Action = self.getActionText(Action)
        
        if (not self.UrlRegEx):
            print('No URL RegEx created, no URLs will be parsed')
            return
        
        urls = self.UrlRegEx.findall(Contents)
        if (not urls) or (len(urls) == 0):
            return
        
        try:
            cursor = self.Database.cursor()
            now = int(time.time())
            for url in urls:
                url = str(url)
                cursor.execute("INSERT INTO url(messageId, url, visitedCount, added) VALUES(?, ?, 0, ?)", [MessageId, url, now])
            self.Database.commit()
            
            cursor.execute("INSERT INTO operation(id, start, finished, status) VALUES(?, ?, -1, 0)", [MessageId, when])
            self.Database.commit()
            self.OperationThread.Refresh()
        except:
            print('Exception thrown in processURLs')
            print(sys.exc_info()[0])
            return
        
        return

    def showMessage(self, Action, Contents):
        cursor = self.Database.cursor()
        
        if (Contents == 'today'):
            start = datetime.date.today()
            end = datetime.datetime(start.year, start.month, start.day, 23, 59, 59)
            startTimeStamp = int(time.mktime(start.timetuple()))
            endTimeStamp = int(time.mktime(end.timetuple()))
            cursor.execute("SELECT contents FROM messages WHERE rowid IN (SELECT messageId FROM message WHERE added >= ? AND added <= ?)", [startTimeStamp, endTimeStamp])
        else:
            try:
                messageId = int(Contents)
                cursor.execute("SELECT contents FROM messages WHERE rowid IN (SELECT messageId FROM message WHERE id=?)", [messageId])
            except:
                cursor.execute("SELECT contents FROM messages WHERE rowid IN (SELECT messageId FROM message WHERE action=?)", [Contents])

        result = []
        rows = cursor.fetchall()
        for row in rows:
            result.append(row[0])
            
        return result

    def storeMessage(self, Action, Contents):
        justAction = self.getActionText(Action)
        messageId = -1
        self.LastInsertedID = -1
        cursor = self.Database.cursor()
        try:
            cursor.execute("INSERT INTO messages(contents) VALUES(?)", [Contents])
            self.Database.commit()
            messageId = cursor.lastrowid
        except lite.Error, e:
            return ['Exception thrown in storeMessage1', e.args[0]]
        
        try:
            now = int(time.time())
            cursor.execute("INSERT INTO message(messageId, added, action, showCount, readCount, deleted) values(?, ?, ?, 0, 0, 0)", [messageId, now, justAction])
            self.Database.commit()
            messageId = cursor.lastrowid
            self.LastInsertedID = messageId
            self.processURLs(Action, Contents, messageId)
        except lite.Error, e:
            return ['Exception thrown in storeMessage2', e.args[0]]
        
        return ['Message stored as #' + str(messageId)]

    def deleteMessage(self, Action, Contents):
        cursor = self.Database.cursor()
        messageId = int(Contents)
        cursor.execute("UPDATE message SET deleted=deleted+1 WHERE message.id=?", [messageId]);
        self.Database.commit()
        return ['Message deleted']

    def remind(self, Action, Contents):
        self.storeMessage(Action, Contents)
        messageId = self.LastInsertedID
        
        actionTime = self.getActionTime(Action)
        parser = DateTimeParser()
        when = parser.parseDateTime(actionTime)
        if not (when):
            return ['Reminder NOT set: invalid date time combination', str(actionTime)]

        try:
            cursor = self.Database.cursor()
            cursor.execute("DELETE FROM operation WHERE id = ?", [messageId])
            cursor.execute("INSERT INTO operation(id, start, finished, status) VALUES(?, ?, ?, 0)", [messageId, when, -1])
            self.Database.commit()
            self.OperationThread.Refresh()
        except lite.Error, e:
            return ['Could not set reminder', e.args[0]]
        
        return ['Reminder set for: ' + time.ctime(when)]


    def searchMessage(self, Action, Contents):
        result = []
        with self.Database:
            cursor = self.Database.cursor()
            cursor.execute("SELECT message.id, messages.contents FROM messages INNER JOIN message ON messages.rowid=message.messageid WHERE contents MATCH ?", [Contents])
            rows = cursor.fetchall()
            for row in rows:
                result.append(str(row[0]) + ': ' + str(row[1]))
        return result

    def searchUrls(self, Action, Contents):
        result = []
        with self.Database:
            cursor = self.Database.cursor()
            cursor.execute("SELECT url.messageId, url.url FROM url WHERE url.messageId IN (SELECT message.messageId FROM message INNER JOIN messages ON message.messageId=messages.rowid WHERE contents MATCH ?)", [Contents])
            rows = cursor.fetchall()
            for row in rows:
                result.append(str(row[0]) + ': ' + row[1])
        return result

    def Query(self, Query, Params = []):
        try:
            cursor = self.Database.cursor()
            cursor.execute(Query, Params)
            if ('INSERT' in Query):
                self.Database.commit()
            rows = cursor.fetchall()
            return rows
        except:
            print(sys.exc_info()[0])
        return []

    def OperationStarted(self, ID):
        self.Query("UPDATE operation SET status=1, start=? WHERE id=?", [int(time.time()), ID])  

    def OperationCompleted(self, ID, Code):
        self.Query("UPDATE operation SET status=?, finished=? WHERE id=?", [Code, int(time.time()), ID])

    def invalidAction(Database, Action, Contents):
        return self.invalidHandler()

    #action name, show text to user, store incoming text
    AvailableActions = [
        ('delete', True, False, deleteMessage),
        ('download', True, True, storeMessage),
        ('remind', True, True, remind),
        ('show', True, False, showMessage),
        ('search', True, False, searchMessage),
        ('searchurls', True, False, searchUrls),
        ('changedb', True, False, changeDatabase),
        ('invalid', False, False, invalidAction),
    ]

    def invalidHandler(self):
        actionString = 'Invalid action, valid actions are:'
        for action in self.AvailableActions:
            if (action[1]):
                actionString = actionString + ' ' + action[0]
        return [actionString]

    def getMessageAction(self, Message):
        return Message.split(':', 1)[0]

    def getActionText(self, ActionText):
        if ('@' in ActionText):
            return ActionText.split('@', 1)[0]
        else:
            return ActionText

    def getActionTime(self, ActionText):
        if ('@' in ActionText):
            return ActionText.split('@', 1)[1]
        else:
            return None

    def getMessageContent(self, Message):
        return Message.split(':', 1)[1]
    
    def processMessage(self, Message):
        if (Message == None) or (len(Message)) == 0:
            return ['Empty message']

        if not (':' in Message):
            return ['Invalid message format (action:contents)'];

        action = None
        result = ''
        
        # split the string into actionText:content
        actionText = self.getMessageAction(Message)
        content = self.getMessageContent(Message)

        # try and find the action passed to us
        for availableAction in self.AvailableActions:
            if (availableAction[0] == self.getActionText(actionText)):
                action = availableAction
                break

        try:
            if (action):
                result = action[3](self, actionText, content)
            else:
                result = self.storeMessage(actionText, content)
        except:
            result = ['Exception happened handling message, continuing...', (sys.exc_info()[0])]
            
        return result

    def onlineStatus(self, Status):
        if (self.Username == Status['to'].bare) and (self.God == Status['from'].bare):
            print('Ohai God')

    def offlineStatus(self, Status):
        if (self.Username == Status['to'].bare) and (self.God == Status['from'].bare):
            self.ReplyTo = None

    def tickTock(self, args = None, kwargs = None):
        now = int(time.time())
        if (self.idle == False) and (now - self.LastChatted > (60 * 15)):
            self.send_presence('away', 'Zzz')
            self.idle = True
            if (self.Database):
                self.Database.close()
                self.Database = None
        return

    def __init__(self, Args):
        if not (os.path.exists(args.f)):
            os.mkdir(args.f)
        self.WorkingFolder = os.getcwd()

        self.Username = Args.u
        self.Password = Args.p
        self.God = Args.g
        self.Server = Args.s
        self.PassPhrase = Args.k
        self.ConfirmPhrase = Args.c
        self.DownloadFolder = Args.f

        ClientXMPP.__init__(self, self.Username, self.Password)
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.makeUrlFinderRegEx()
        self.OperationThread = OperationThread(self)
        self.OperationThread.start()
        self.add_event_handler("got_online", self.onlineStatus)
        self.add_event_handler("got_offline", self.offlineStatus)
        self.schedule('ticktocker', 60, self.tickTock, None, None, True)
        print(self.changeDatabase('changedb', Args.d))
        try:
            if (self.Database):
                cursor = self.Database.cursor()
                cursor.execute("UPDATE operation SET status=0, finished=-1 WHERE status=1")
                self.Database.commit()
        except:
            pass

        return


    def session_start(self, event):
        self.send_presence('away', 'Zzz')
        self.get_roster()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if not (msg['from'].bare == self.God):
                return

            if (msg['body'] == self.PassPhrase):
                self.LastChatted = int(time.time())
                self.send_message(mto=msg['from'], mbody=self.ConfirmPhrase)
                self.send_presence('chat', 'Awaiting commands')
                if (self.idle) and (not self.Database):
                    print(self.changeDatabase('changedb', self.CurrentDatabase))    
                self.idle = False;
                return
                    
            now = int(time.time())
            if (now - self.LastChatted > (60 * 15)):
                return
            
            if (msg['body'] == 'Go to hell'):
                self.OperationThread._Thread__stop()
                sys.exit(0)
                    
            self.LastChatted = int(time.time())
            self.ReplyTo = msg['from']
            results = self.processMessage(msg['body'])
            self.SendMessage(results)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, format='%(levelname)-8s %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', metavar='Username', help='MonkeyBot account username e.g., monkeybot@google.com')
    parser.add_argument('-p', metavar='Password', help='MonkeyBot account password')
    parser.add_argument('-g', metavar='God', help='The account MonkeyBot takes orders from e.g., monkeygod@google.com')
    parser.add_argument('-k', metavar='Keyphrase', help='Secret handshake keyphrase to initiate communications', default='Ahoy')
    parser.add_argument('-f', metavar='Folder', help='Download folder (must end with a \'/\')', default=os.getcwd() + '/downloads/')
    parser.add_argument('-s', metavar='Server', help='Chat server (default: talk.google.com)', default='talk.google.com')
    parser.add_argument('-d', metavar='Database', help='Filename of local SQLite database', default=os.getcwd() + '/monkey.db')
    parser.add_argument('-c', metavar='Confirmation', help='Handshake confirmation message', default='Listening...')
    try:
        args = parser.parse_args()
    except:
        exit(0)

    while (not args.u) or (len(args.u) == 0):
        args.u = raw_input("MonkeyBot Account Username: ")
    while (not args.p) or (len(args.p) == 0):
        args.p = getpass.getpass("Password: ")
    while (not args.g) or (len(args.g) == 0):
        args.g = raw_input("Commanding account: ")

    helperMonkey = MonkeyBot(args)
    helperMonkey.connect((args.s, 5222))
    helperMonkey.process(block=True)
