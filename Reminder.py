# ZLib license:# Copyright (c) 2012 Dirk de la Hunt#
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.# Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.# 3. This notice may not be removed or altered from any source distribution.
from Operation import Operation
import time

class Reminder(Operation):
    def __init__ (self, Parent, ID, Action, Contents, StartTime):
        Operation.__init__(self, Parent, ID, Action, Contents, StartTime)
        return

    def Process(self):
        subject = self.Action
        if (self.ID >= 0):
            subject = "Reminder: " + time.ctime(self.StartTime)
        result = self.Parent.SendMail(subject, self.Contents)
        self.Parent.SendMessage([subject + "\n" + self.Contents])
        return result
