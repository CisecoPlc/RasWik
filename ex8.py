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
#import ImageTk

#port = 'Com16'
port = '/dev/tty.usbmodem000001'

class GuiPart:
    def __init__(self, master, queue, endCommand, sendLLAP):
        self.queue = queue
        self.sendLLAP = sendLLAP
        # Set up the GUI
        
        gframe = Frame(master, relief=RAISED, borderwidth=1)
        gframe.pack()
        
        # pack the grid to get the damn size right
        for n in range(29):
            Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   highlightcolor='white'
                   ).grid(row=n, column=0)
            
            Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   highlightcolor='white'
                   ).grid(row=n, column=1)
            
            Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   highlightcolor='white'
                   ).grid(row=n, column=2)
        
        canvas = Canvas(gframe, bg="white", width=574, height=784, bd=0,
                        relief=FLAT, highlightthickness=0)
        canvas.grid(row=0, column=3, columnspan=1, rowspan=29,
                    sticky=W+E+N+S, padx=5, pady=5)
        
        self.photoimage = PhotoImage(file="XinoRF.gif")
        canvas.create_image(286, 407, image=self.photoimage)
        
        # analog buttons
        self.anaLabel = {'0': StringVar(),
                         '1': StringVar(),
                         '2': StringVar(),
                         '3': StringVar(),
                         '4': StringVar(),
                         '5': StringVar()}
        
        for n in range(6):
            Button(gframe, text='Read',
                   command=lambda n=n: self.anaRead(n)
                   ).grid(row=21+n, column=2)
            Label(gframe, width=5,
                  textvariable=self.anaLabel['{}'.format(n)]
                  ).grid(row=21+n, column=1)

        # input buttons
        self.inputLabel = {'2': StringVar(),
                           '3': StringVar(),
                           '7': StringVar(),
                           '10': StringVar(),
                           '12': StringVar()}
        Button(gframe, text='Read', command=lambda: self.read(2)
               ).grid(row=24, column=4)
        Label(gframe, width=5, textvariable=self.inputLabel['2']
              ).grid(row=24, column=5)
        Button(gframe, text='Read', command=lambda: self.read(3)
               ).grid(row=23, column=4)
        Label(gframe, width=5, textvariable=self.inputLabel['3']
              ).grid(row=23, column=5)
        Button(gframe, text='Read', command=lambda: self.read(7)
               ).grid(row=19, column=4)
        Label(gframe, width=5, textvariable=self.inputLabel['7']
              ).grid(row=19, column=5)
        Button(gframe, text='Read', command=lambda: self.read(10)
               ).grid(row=15, column=4)
        Label(gframe, width=5, textvariable=self.inputLabel['10']
              ).grid(row=15, column=5)
        Button(gframe, text='Read', command=lambda: self.read(12)
               ).grid(row=13, column=4)
        Label(gframe, width=5, textvariable=self.inputLabel['12']
              ).grid(row=13, column=5)




#        for n in range(10):
#            Button(gframe, text='Read', command=lambda n=n: self.read(n)).grid(row=n, column=0)
#            Button(gframe, text='Off', command=lambda n=n: self.off(n)).grid(row=n, column=1)
#            Button(gframe, text='On', command=lambda n=n: self.on(n)).grid(row=n, column=2)
        
        

#        for n in range(10,20):
#            Button(gframe, text='Read', command=lambda n=n: self.read(n)).grid(row=n, column=6)
#            Button(gframe, text='Off', command=lambda n=n: self.off(n)).grid(row=n, column=5)
#            Button(gframe, text='On', command=lambda n=n: self.on(n)).grid(row=n, column=4)
     
     
        # bottom frame
        frame = Frame(master, relief=RAISED, borderwidth=1)
        frame.pack()
        # serial console
        self.text = Text(frame, state=DISABLED, relief=RAISED, borderwidth=1,
                         height=12, name='frame1')
        self.text.pack(fill=BOTH, expand=1)
        
        labela = Label(frame, text='a')
        labela.pack(side=LEFT)
        
        self.devID = StringVar()
        self.payload = StringVar()



        self.vcmd = (master.register(self.validLenght), '%P', '%W')
        
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
        
        self.maxLenght = {str(self.devIDInput): 2, str(self.input): 9}
        self.devID.set("XX")
        self.payload.set("HELLO")

        Button(frame, text='Send', command=self.sendCommand).pack(side=LEFT)
        Button(frame, text='Done', command=endCommand).pack(side=RIGHT)

        
        frame2 = Frame(master, relief=RAISED, borderwidth=1)
        frame2.pack(fill=BOTH, expand=1)
        bah = Button(frame2, text='Bah')
        bah.pack(side=LEFT)
        # Add more GUI stuff here
        
    def anaRead(self, num):
        print("anaRead: {}".format(num))
        self.sendLLAP("XX", "A{0:02d}READ".format(num))
    
    def read(self, num):
        print("read: {}".format(num))
    
    def on(self, num):
        print("on: {}".format(num))
    
    def off(self, num):
        print("off: {}".format(num))
    
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
        self.sendLLAP(self.devID.get(), self.payload.get())
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
                if msg['devID'] == "XX":
                    if msg['payload'].startswith("A"):
                        self.anaLabel[
                                      msg['payload'][2:3]
                                      ].set(msg['payload'][3:])

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
        self.master.title("Sandy")
        self.master.resizable(0,0)


        # Create the queue
        self.queue = Queue.Queue()
        
        self.s = serial.Serial()
        self.s.baudrate = 9600
        self.s.timeout = 0            # non-blocking read's
        self.s.port = port
        try:
            self.s.open()
        except serial.SerialException, e:
            sys.stderr.write("could not open port %r: %s\n" % (port, e))
            self.running = 0
            self.kill(0)
        
        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication,
                           self.sendLLAP)

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
            #  some cleanup before actually shutting it down.
            self.kill(1)
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
                        self.queue.put({'devID': llapMsg[1:3],
                                       'payload': llapMsg[3:].rstrip("-")})
    
    def kill(self, t):
        if t:
            self.thread1.join()
        self.s.close()
        self.master.destroy()
        sys.exit(1)

    def endApplication(self):
        self.running = 0


root = Tk()
root.geometry("+750+150")
client = ThreadedClient(root, port)
root.mainloop()