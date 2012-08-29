# ZLib license:
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.
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