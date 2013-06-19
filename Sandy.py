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
        self.master = master
        self.queue = queue
        self.sendLLAPcommand = sendLLAP
        # Set up the GUI
        
        gframe = Frame(master, relief=RAISED, borderwidth=4, name='grid')
        gframe.pack()
        
        # pack the grid to get the damn size right
        for n in range(29):
            #Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
            #       width=50, height=28, highlightthickness=0,
            #       highlightcolor='white'
            #       ).grid(row=n, column=0)
                   
           Canvas(gframe, bg="white", bd=0, relief=FLAT,
                  width=50, height=28, highlightthickness=0,
                  highlightcolor='white'
                  ).grid(row=n, column=1)
    

        # image in the middles
        canvas = Canvas(gframe, bg="white", width=574, height=784, bd=0,
                        relief=FLAT, highlightthickness=0)
        canvas.grid(row=0, column=3, columnspan=1, rowspan=29,
                    sticky=W+E+N+S, padx=5, pady=5)
        
        self.photoimage = PhotoImage(file="XinoRF.gif")
        canvas.create_image(286, 407, image=self.photoimage)
        
        # some lables
        Label(gframe, text='Radio Enable Pin').grid(row=17, column=4, columnspan=3, sticky=W)
        Label(gframe, text='Serial TX').grid(row=25, column=4, columnspan=3, sticky=W)
        Label(gframe, text='Serial RX').grid(row=26, column=4, columnspan=3, sticky=W)
        
        
        # analog buttons
        self.anaLabel = {'0': StringVar(),
                         '1': StringVar(),
                         '2': StringVar(),
                         '3': StringVar(),
                         '4': StringVar(),
                         '5': StringVar()}
        
        for n in range(6):
            Button(gframe, text='READ', command=lambda n=n: self.anaRead(n)
                   ).grid(row=21+n, column=2)
            Label(gframe, width=5, textvariable=self.anaLabel['{}'.format(n)], relief=RAISED
                  ).grid(row=21+n, column=1)

        self.digital = {'02': StringVar(),
                       '03': StringVar(),
                       '04': StringVar(),
                       '05': StringVar(),
                       '06': StringVar(),
                       '07': StringVar(),
                       '09': StringVar(),
                       '10': StringVar(),
                       '11': StringVar(),
                       '12': StringVar(),
                       '13': StringVar()}

        # input buttons
        Button(gframe, text='READ', command=lambda: self.read('02')
               ).grid(row=24, column=4, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['02'], relief=RAISED
              ).grid(row=24, column=5)
        Button(gframe, text='READ', command=lambda: self.read('03')
               ).grid(row=23, column=4, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['03'], relief=RAISED
              ).grid(row=23, column=5)
        Button(gframe, text='READ', command=lambda: self.read('07')
               ).grid(row=19, column=4, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['07'], relief=RAISED
              ).grid(row=19, column=5)
        Button(gframe, text='READ', command=lambda: self.read('10')
               ).grid(row=15, column=4, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['10'], relief=RAISED
              ).grid(row=15, column=5)
        Button(gframe, text='READ', command=lambda: self.read('12')
               ).grid(row=13, column=4, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['12'], relief=RAISED
              ).grid(row=13, column=5)


        # output buttons
        self.vpwm = (master.register(self.validPWM), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        Button(gframe, text='LOW', command=lambda: self.off('06')
               ).grid(row=20, column=5, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('06')
               ).grid(row=20, column=4, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('06')
               ).grid(row=20, column=6, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['06'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital06'
              ).grid(row=20, column=7)

        Button(gframe, text='LOW', command=lambda: self.off('09')
               ).grid(row=16, column=5, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('09')
               ).grid(row=16, column=4, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('09')
               ).grid(row=16, column=6, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['09'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital09'
              ).grid(row=16, column=7)
        Button(gframe, text='LOW', command=lambda: self.off('11')
               ).grid(row=14, column=5, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('11')
               ).grid(row=14, column=4, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('11')
               ).grid(row=14, column=6, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['11'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital11'
              ).grid(row=14, column=7)
        Button(gframe, text='LOW', command=lambda: self.off('13')
               ).grid(row=12, column=5, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('13')
               ).grid(row=12, column=4, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('13')
               ).grid(row=12, column=6, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['13'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital13'
              ).grid(row=12, column=7)


        # servo button
        Label(gframe, text='SERVO').grid(row=21, column=4, sticky=W)
        servo = Scale(gframe, orient=HORIZONTAL, from_=0, to=180, digits=3,
              command=lambda value: self.servo(value)
              )
        servo.grid(row=21, column=5, columnspan=3, sticky=W+E)
        servo.set(90)
 
        # count button
        self.vcount = (master.register(self.validCount), '%d', '%P', '%S')

        Button(gframe, text='COUNT', command=lambda: self.count('READ')
               ).grid(row=22, column=4, sticky=W+E)
        Button(gframe, text='SET', command=lambda: self.count('SET')
               ).grid(row=22, column=5, sticky=W+E)
        self.countEntry = Entry(gframe, width=5, textvariable=self.digital['04'], validate='key',
              invalidcommand='bell', validatecommand=self.vcount, justify=CENTER
              )
        self.countEntry.grid(row=22, column=6)


        # bottom frame
        frame = Frame(master, relief=RAISED, borderwidth=2)
        frame.pack(expand=1, fill=BOTH)
        
        # serial console
        self.text = Text(frame, state=DISABLED, relief=RAISED, borderwidth=2, height=6, width=60)
        self.text.pack(side=LEFT, expand=1, fill=BOTH)
        self.serialText = Text(frame, state=DISABLED, relief=RAISED, borderwidth=2, height=6, width=60)
        self.serialText.pack(side=LEFT, expand=1, fill=BOTH)
        
        # llap command box
        frame = Frame(master, relief=RAISED, borderwidth=2)
        frame.pack(expand=1, fill=BOTH)
        
        labela = Label(frame, text='a')
        labela.pack(side=LEFT)
        
        self.devID = StringVar()
        self.payload = StringVar()

        self.vlen = (master.register(self.validLenght), '%P', '%W', '%S')
        
        self.devIDInput = Entry(frame, width=2, validate='key', justify=CENTER,
                                textvariable=self.devID, invalidcommand='bell',
                                validatecommand=self.vlen, name='devIDInput')

        self.devIDInput.pack(side=LEFT)
        
        self.input = Entry(frame, width=9, validate='key',
                           textvariable=self.payload, invalidcommand='bell',
                           validatecommand=self.vlen, name='payloadInput')
        self.input.pack(side=LEFT)
        
        self.maxLenght = {str(self.devIDInput): 2, str(self.input): 9}
        self.devID.set("XX")
        self.payload.set("HELLO")

        # send and quite buttons
        Button(frame, text='Send', command=self.sendCommand).pack(side=LEFT)
        Button(frame, text='Quit', command=endCommand).pack(side=RIGHT)

        # status bar button
        frame2 = Frame(master, relief=RAISED, borderwidth=1)
        frame2.pack(fill=BOTH, expand=1)
        bah = Button(frame2, text='Bah')
        bah.pack(side=LEFT)
            
    def anaRead(self, num):
        print("anaRead: {}".format(num))
        self.sendLLAP("XX", "A{0:02d}READ".format(num))
    
    def read(self, num):
        print("read: {}".format(num))
        self.sendLLAP("XX", "D{}READ".format(num))
    
    def on(self, num):
        print("high: {}".format(num))
        self.sendLLAP("XX", "D{}HIGH".format(num))
    
    def off(self, num):
        print("low: {}".format(num))
        self.sendLLAP("XX", "D{}LOW".format(num))
    
    def pwm(self, num):
        print("pwm: {}".format(num))
        if self.digital[num].get().isdigit():
            if int(self.digital[num].get()) < 255:
                self.sendLLAP("XX", "D{}PWM{}".format(num, self.digital[num].get()))
            else:
                self.appendText("D{} PWM: {} is too large. Range 0-255\n".format(num, self.digital[num].get()))
        else:
            self.appendText("D{} PWM: {} is not a number. Range 0-255\n".format(num, self.digital[num].get()))
            
    def servo(self, value):
        print("servo")
        self.sendLLAP("XX", "SERVO{}".format(value))

    def count(self, mode):
        print("count: {}".format(mode))
        if mode == 'READ':
            self.sendLLAP("XX", "COUNT")
        else:
            self.sendLLAP("XX", "COUNT{}".format(self.digital['04'].get()))
    
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
    def validLenght(self, P, W, S):
        l = self.maxLenght[W]
        # only allow if the string length of based on entry name
        return (len(P) <= l)
    
    def validPWM(self, d, i, P, s, S, v, V, W):
        if d == '0':
            return True
        elif S.isdigit() and (len(P) <=3) :
            return True
        else:
            return False

    def validCount(self, d, P, S):
        if d == '0':
            return True
        elif S.isdigit() and (len(P) <=4) :
            return True
        else:
            return False
    
    # send commands
    def sendCommand(self):
        self.sendLLAP(self.devID.get(), self.payload.get())
        #self.devIDInput.delete(0, END)
        #self.input.delete(0, END)
    
    def sendLLAP(self, devID, payload):
        self.text.config(state=NORMAL)
        self.text.insert(END, "Sending LLAP TO {} with Paylaod: {}\n".
                         format(devID, payload))
        self.sendLLAPcommand(devID, payload)
        self.text.see(END)
        self.text.config(state=DISABLED)

    # display update stuff
    def appendText(self,msg):
        self.text.config(state=NORMAL)
        self.text.insert(END, msg)
        self.text.see(END)
        self.text.config(state=DISABLED)

    def appendSerial(self, msg):
        self.serialText.config(state=NORMAL)
        self.serialText.insert(END, msg)
        self.serialText.see(END)
        self.serialText.config(state=DISABLED)

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
                self.text.insert(END, "Recieve LLAP from {} with Paylaod: {}\n".
                                 format(msg['devID'],msg['payload']))
                if msg['devID'] == "XX":
                    if msg['payload'].startswith("A"):
                        self.anaLabel[
                                      msg['payload'][2:3]
                                      ].set(msg['payload'][3:])
                    
                    elif msg['payload'].startswith("COUNT"):
                        # we have a count
                        self.digital['04'].set(msg['payload'][5:])
                        self.countEntry.config(validate='key')
                    
                    elif msg['payload'][3:].startswith("PWM"):
                        # we have pwm
                        self.digital[
                                     msg['payload'][1:3]
                                     ].set(msg['payload'][6:])
                    
                    elif msg['payload'].startswith("D"):
                        self.digital[
                                     msg['payload'][1:3]
                                     ].set(msg['payload'][3:])
                        if (msg['payload'][1:3] == '06' or
                            msg['payload'][1:3] == '09' or
                            msg['payload'][1:3] == '11' or
                            msg['payload'][1:3] == '13'):
                            self.master.nametowidget(".grid.digital{}".format(
                                  msg['payload'][1:3])).config(validate='key')
                            

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
            self.gui.appendSerial(llapMsg)
    
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
                    char = self.s.read()
                    self.gui.appendSerial(char)
                    if char == 'a':
                        llapMsg = 'a'
                        llapMsg += self.s.read(11)
                        self.gui.appendSerial(llapMsg[1:])
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
root.geometry("+650+150")
client = ThreadedClient(root, port)
root.mainloop()