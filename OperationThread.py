# ZLib license:# Copyright (c) 2012 Dirk de la Hunt#
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.# Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.# 3. This notice may not be removed or altered from any source distribution.

from Reminder import Reminder
from Downloader import Downloader
import sys
import threading
import smtplib
import time
import datetime
import os

class OperationThread(threading.Thread):
    CurrentDay = -1
    Parent = None
    Operations = None
    ListMutex = None
    refreshNeeded = True
    
    def __init__ (self, Parent):
        self.Parent = Parent
        self.ListMutex = threading.Lock()
        self.refreshNeeded = True
        threading.Thread.__init__(self)
        return
    
    def DownloadFolder(self):
        return self.Parent.DownloadFolder

    def WorkingFolder(self):
        return self.Parent.WorkingFolder
    
    def OperationStarted(self, ID):
        self.Parent.OperationStarted(ID)
        
    def OperationCompleted(self, ID, Code):
        self.Parent.OperationCompleted(ID, Code)
        
    def SendMessage(self, Message):
        self.Parent.SendMessage(Message)
    
    def Query(self, Query, Params = []):
        return self.Parent.Query(Query, Params)
    
    def Which(self, Program):
        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        if ('win32' in sys.platform) and not ('.exe' in Program):
            Program = Program + '.exe'

        fpath, fname = os.path.split(Program)
        if fpath:
            if is_exe(Program):
                return Program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, Program)
                if is_exe(exe_file):
                    return exe_file
        return None

    def SendMail(self, Subject, Contents):
        try:
            Contents = "From: " + self.Parent.Username + "\r\nTo: " + self.Parent.God + "\r\nSubject: " + Subject + "\r\n\r\n" + Contents
            fromaddr = self.Parent.Username
            toaddrs  = self.Parent.God
            username = self.Parent.Username
            password = self.Parent.Password
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()  
            server.login(username,password)  
            result = server.sendmail(fromaddr, toaddrs, Contents)
            server.quit()
            if (len(result) == 0):
                return True
        except:
            print(sys.exc_info()[0])
            return False
        return False
    
    def Refresh(self):
        self.refreshNeeded = True

    def reload(self):
        self.refreshNeeded = False
        self.ListMutex.acquire()
        self.Operations = []
        rows = self.Query("SELECT message.id, message.action, messages.contents, operation.start FROM operation, messages INNER JOIN message ON messages.rowid=operation.id WHERE messages.rowid=message.id AND operation.status=0 AND message.deleted=0;", [])
        for row in rows:
            if (row[1] == 'remind'):
                operation = [int(row[0]), row[1], str(row[2]), int(row[3]), False];
                self.Operations.append(operation)
            else:
                urls = self.Query("SELECT url, id FROM url WHERE messageId=?", [row[0]])
                for url in urls:
                    s = str(url[0])
                    operation = [int(url[1]), row[1], s, int(row[3]), False];
                    self.Operations.append(operation)
        self.ListMutex.release()
        
        return self.Operations
    
    def doDayChange(self):
        today = datetime.date.today()
        if (today.day == self.CurrentDay):
            return
        
        self.CurrentDay = today.day
        start = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        end = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        startTimeStamp = int(time.mktime(start.timetuple()))
        endTimeStamp = int(time.mktime(end.timetuple()))

        rows = self.Query("SELECT message.id, messages.contents, operation.start FROM operation, messages INNER JOIN message ON messages.rowid=operation.id WHERE messages.rowid=message.id AND operation.status=0 AND message.action='remind' AND message.deleted=0 AND operation.start>=? AND operation.start<=?;", [startTimeStamp, endTimeStamp])
        if (len(rows) > 0):
            mailContents = ''
            for row in rows:
                mailContents = mailContents + '@ ' + time.ctime(int(row[2])) + "\n"
                mailContents = mailContents + str(row[1]) + "\n\n"
                
            action = "Reminders for " + str(start.year) + '/' + str(start.month) + '/' + str(start.day)
            Reminder(self, -1, action, mailContents, 0).start()
        self.reload()
        return
    
    def run(self):
        time.sleep(5)
        while True:
            # pretend we're 15 minutes in the future
            try:
                self.doDayChange()
                if (self.refreshNeeded):
                    self.reload()
                now = int(time.time()) + (15 * 60)
                self.ListMutex.acquire()
                operations = list(self.Operations)
                self.ListMutex.release()
                if (operations):
                    for operation in operations:
                        if (not operation[4]) and (now > operation[3]):
                            operation[4] = True
                            operationThread = None
                            if (operation[1] == 'remind'):
                                operationThread = Reminder(self, operation[0], operation[1], operation[2], operation[3])
                            else: #assume we have something to download as a url in some other text
                                operationThread = Downloader(self, operation[0], operation[1], operation[2], operation[3])
                                
                            if (operationThread):
                                operationThread.start()
            except:
                print(sys.exc_info())
                sys.exit()
                pass
                                    
            time.sleep(60)
        return
