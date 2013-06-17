"""
This recipe describes how to handle asynchronous I/O in an environment where
you are running Tkinter as the graphical user interface. Tkinter is safe
to use as long as all the graphics commands are handled in a single thread.
Since it is more efficient to make I/O channels to block and wait for something
to happen rather than poll at regular intervals, we want I/O to be handled
in separate threads. These can communicate in a threasafe way with the main,
GUI-oriented process through one or several queues. In this solution the GUI
still has to make a poll at a reasonable interval, to check if there is
something in the queue that needs processing. Other solutions are possible,
but they add a lot of complexity to the application.

Created by Jacob Hallen, AB Strakt, Sweden. 2001-10-17
"""
from Tkinter import *
import time
import threading
import random
import Queue
import serial
import sys

#port = 'Com16'
port = '/dev/tty.usbmodem000001'

class GuiPart:
    def __init__(self, master, queue, endCommand, sendLLAP):
        self.queue = queue
        self.sendLLAP = sendLLAP
        # Set up the GUI
        
        
        butframe = Frame(master, relief=RAISED, borderwidth=1)
        butframe.pack()
        
        Button(butframe, text='Read', command=self.read)
        
        frame = Frame(master, relief=RAISED, borderwidth=1)
        frame.pack()
        
        self.text = Text(frame, state=DISABLED, relief=RAISED, borderwidth=1, height=12, name='frame1')
        self.text.pack(fill=BOTH, expand=1)
        
        labela = Label(frame, text='a')
        labela.pack(side=LEFT)
        
        self.devID = StringVar()
        self.payload = StringVar()

        

        self.vcmd = (master.register(self.validLenght),
                            '%P', '%W')
        self.devIDInput = Entry(frame, width=2, validate='key',
                                        textvariable=self.devID,
                                        invalidcommand='bell',
                                        validatecommand=self.vcmd,
                                        name='devIDInput')

        self.devIDInput.pack(side=LEFT)
        
        self.input = Entry(frame, width=9, validate='key',
                                   textvariable=self.payload,
                                   invalidcommand='bell',
                                   validatecommand=self.vcmd,
                                   name='payloadInput')
        self.input.pack(side=LEFT)
        
        self.maxLenght= {str(self.devIDInput): 2, str(self.input): 9}
        
        
        send = Button(frame, text='Send', command=self.sendCommand)
        send.pack(side=LEFT)
        
        console = Button(frame, text='Done', command=endCommand)
        console.pack(side=RIGHT)
        
        frame2 = Frame(master, relief=RAISED, borderwidth=1)
        frame2.pack(fill=BOTH, expand=1)
        bah = Button(frame2, text='Bah')
        bah.pack(side=LEFT)
        # Add more GUI stuff here
        
        
    def read(self):
        print("read")
    
    def on(self):
        print("on")
    
    def off(self):
        print("off")
    
    # valid percent substitutions (from the Tk entry man page)
    # %d = Type of action (1=insert, 0=delete, -1 for others)
    # %i = index of char string to be inserted/deleted, or -1
    # %P = value of the entry if the edit is allowed
    # %s = value of entry prior to editing
    # %S = the text string being inserted or deleted, if any
    # %v = the type of validation that is currently set
    # %V = the type of validation that triggered the callback
    #      (key, focusin, focusout, forced)
    # %W = the tk name of the widget
    def validLenght(self, P, W):
        l = self.maxLenght[W]
        # only allow if the string length of based on entry name
        return (len(P) <= l)
    
    def sendCommand(self):
        self.sendLLAP(self.devIDInput.get(), self.input.get())
        #self.devIDInput.delete(0, END)
        #self.input.delete(0, END)
    
    
    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        while self.queue.qsize():
            try:
                msg = self.queue.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                self.text.config(state=NORMAL)
                self.text.insert(END, "Recieve LLAP from {} with Paylaod: {}\n".format(msg['devID'],msg['payload']))
                self.text.see(END)
                self.text.config(state=DISABLED)
            except Queue.Empty:
                pass

class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master, port):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.endApplication) 


        # Create the queue
        self.queue = Queue.Queue()
        
        self.s = serial.Serial()
        self.s.baudrate = 9600
        self.s.timeout = 0            # non-blocking read's
        self.s.port = port
        self.s.open()

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication, self.sendLLAP)

        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            self.thread1.join()
            self.s.close()
            self.master.destroy()
            sys.exit(1)
        self.master.after(100, self.periodicCall)

    def sendLLAP(self, devID, data):
        llapMsg = "a{}{}".format(devID, data)
        while len(llapMsg) < 12:
            llapMsg += '-'
        if self.s.isOpen() == True:
            self.s.write(llapMsg)
    
    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        One important thing to remember is that the thread has to yield
        control.
        """
        while self.running:
            if self.s.isOpen():
                if self.s.inWaiting() >= 12:
                    if self.s.read() == 'a':
                        llapMsg = 'a'
                        llapMsg += self.s.read(11)
                        self.queue.put({'devID': llapMsg[1:3], 'payload': llapMsg[3:].rstrip("-")})

    def endApplication(self):
        self.running = 0


root = Tk()
root.geometry("+1000+250")
client = ThreadedClient(root, port)
root.mainloop()