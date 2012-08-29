# ZLib license:# Copyright (c) 2012 Dirk de la Hunt#
# This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.# Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:# 1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.# 2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.# 3. This notice may not be removed or altered from any source distribution.
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
