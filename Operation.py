# ZLib license:
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.
import threading

class Operation(threading.Thread):
    # Parent is of type OperationThread, ID is the ID of the operation in the operation table
    def __init__ (self, Parent, ID, Action, Contents, StartTime):
        self.Parent = Parent
        self.ID = ID
        self.Action = Action
        self.Contents = Contents
        self.StartTime = StartTime
        threading.Thread.__init__(self)
        return

    def Process(self):
        return True
        
    def run(self):
        self.Parent.OperationStarted(self.ID)
        code = 1
        if (self.Process()):
            code = 2
        self.Parent.OperationCompleted(self.ID, code)
        return