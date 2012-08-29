# ZLib license:# Copyright (c) 2012 Dirk de la Hunt#
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.# Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.# 3. This notice may not be removed or altered from any source distribution.
from Operation import Operation
import sys
import os
import urllib

class Downloader(Operation):
    LocalPath = ''
    UrlFile = ''
    
    def __init__ (self, Parent, ID, Action, Contents, StartTime):
        Contents = str(Contents)
        self.LocalPath = Parent.DownloadFolder() + str(ID) + '/'
        self.UrlFile = self.LocalPath + "url.txt"
        Operation.__init__(self, Parent, ID, Action, Contents, StartTime)
        return

    def downloadUrlLib(self):
        try:
            urllib.urlretrieve(self.Contents, self.LocalPath)
            return True
        except:
            self.Parent.SendMessage(['Exception thrown trying to download: ' + self.Contents, sys.exc_info()[0]])
        return False
        
    def downloadWget(self):
        try:
            result = os.system('wget -q -i ' + self.UrlFile + ' -O ' + self.LocalPath)
            return (result == 0)
        except:
            self.Parent.SendMessage(['Exception thrown trying to download', sys.exc_info()[0]])
        return False
            
    def downloadCurl(self):
        try:
            result = os.system('curl -L -K ' + self.UrlFile + ' -o ' + self.LocalPath)
            return (result == 0)
        except:
            self.Parent.SendMessage(['Exception thrown trying to download', sys.exc_info()[0]])
        return False

    def Process(self):
        try:
            if not (os.path.exists(self.LocalPath)):
                os.mkdir(self.LocalPath)

            filename = os.path.basename(self.Contents)
            if (not filename) or (len(filename) == 0):
                filename = 'index.html'
            self.LocalPath = self.LocalPath + filename
            
            info = open(self.UrlFile, 'w')
            if (info == None):
                return self.downloadUrlLib()
            info.write(self.Contents)
            info.close()
            
            result = False
            if (self.Parent.Which('wget')):
                result = self.downloadWget()
            elif (self.Parent.Which('curl')):
                result = self.downloadCurl()
            else:
                result = self.downloadUrlLib()

            if (self.Action == 'download'):
                if (result):
                    self.Parent.SendMessage(['Downloaded: ' + self.Contents])
                else:
                    self.Parent.SendMessage(['Could not download: ' + self.Contents])

            return result
        except:
            self.Parent.SendMessage(['Exception thrown trying to process download', sys.exc_info()[0]])
            return False
        
        return False
