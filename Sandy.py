#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Sandy Example 3
    
    TK text and llapserial
"""
import LLAPSerial, queue

from Tkinter import *

class Application(Frame):
    def addText(self):
        self.count += 1
        self.text.config(state=NORMAL)
        self.text.insert(END, "hello, world {}\n".format(self.count))
        self.text.see(END)
        self.text.config(state=DISABLED)
        self.after(500, self.addText)
    
    def createText(self):
        self.text = Text()
        self.text.config(state=DISABLED)
        self.text.pack()
        self.addText()
        
    
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.q = Queue.Queue()
        self.l = LLAPSerial.LLAPSerial(self.q)
        self.l.connect('/dev/usbmodem00001')
        
        self.count = 0
        self.createText()

if __name__ == "__main__" :
    root = Tk()
    app = Application(master=root)
    app.mainloop()
    root.destroy()
