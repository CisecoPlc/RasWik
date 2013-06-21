"""
This recipe describes how to handle asynchronous I/O in an environment where
you are running Tkinter as the graphical user interface. Tkinter is safe
to use as long as all the graphics commands are handled in a single thread.
Since it is more efficient to make I/O channels to block and wait for something
to happen rather than poll at regular intervals, we want I/O to be handled
in separate threads. These can communicate in a thread safe way with the main,
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
import ttk
#import ImageTk

#port = 'Com16'
port = '/dev/tty.usbmodem000001'
#port = '/dev/ttyAMA0'

version = "SandyWare v0.9x " 

class GuiPart:
    def __init__(self, master, queue, endCommand, sendLLAP, connect):
        self.master = master
        self.queue = queue
        self.sendLLAPcommand = sendLLAP
        self.endCommand = endCommand
        self.connectCommand = connect
        
        # variables used later
        self.gridComRowOffset = 1
        self.gridDigitalRowOffset = 1
        self.gridAnalogRowOffset = 10
        self.serialConsoleWidth = 45
        self.canvasWidth = 400
        self.canvasHeight = 459
        self.servoVal = IntVar()
        self.payload = StringVar()
        self.payload.set("HELLO")
        self.comport = StringVar()
        self.comport.set(port)
        self.connectText = StringVar()
        self.connectText.set("Connect")
        self.devID = StringVar()
        self.devID.set("XX")
        self.gif = "XinoRF 3 copy.gif"
        self.historyList = []
        
        # validation setup
        self.initValidationRules()
        
        # Set up the GUI
        self.initTabBar()
        self.initGrid()
        self.initBottom()
        self.initSerialConsoles()
    
    def initTabBar(self):
        # TODO
        
        # tab button frame
        self.tBarFrame = Frame(self.master, relief=RAISED, name='tabBar')
        self.tBarFrame.pack(fill=X)
        
        # tab buttons
        # place holder
        Button(self.tBarFrame, text="Basic's").pack(side=LEFT)
        Label(self.tBarFrame, text=version).pack(side=RIGHT)
    
    def initGrid(self):
        # grid frame
        gframe = Frame(self.master, relief=RAISED, borderwidth=2, name='grid')
        gframe.pack()

        # pack the grid to get the damn size right
        for n in range(17):
            """
            Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   highlightcolor='white'
                   ).grid(row=n, column=0)
            """       
            Canvas(gframe, bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   ).grid(row=n, column=1)
    
        # com selection bits
        Label(gframe, text='Com Port').grid(row=self.gridComRowOffset+0,
                                            column=0, columnspan=3)
        Entry(gframe, textvariable=self.comport, width=17
              ).grid(row=self.gridComRowOffset+1, column=0, columnspan=3)
        Button(gframe, textvariable=self.connectText,
               command=self.connectCommand, width=10
               ).grid(row=self.gridComRowOffset+2, column=0, columnspan=3)

        Label(gframe, text='Device ID').grid(row=self.gridComRowOffset+4,
                                             column=0, columnspan=3)
        self.devIDInput = Entry(gframe, width=3, validate='key', justify=CENTER,
                                textvariable=self.devID, invalidcommand='bell',
                                validatecommand=self.vdev, name='devIDInput')
                                
        self.devIDInput.grid(row=self.gridComRowOffset+5, column=0,
                             columnspan=3)
        Label(gframe, text="A-Z, -, #, @, ?, \, *").grid(row=self.gridComRowOffset+6, column=0, columnspan=3)

        # image in the middles
        canvas = Canvas(gframe, width=self.canvasWidth,
                        height=self.canvasHeight, bd=0,
                        relief=FLAT, highlightthickness=0)
        canvas.grid(row=0, column=3, columnspan=1, rowspan=18,
                    sticky=W+E+N+S, padx=5, pady=5)
        
        self.photoimage = PhotoImage(file=self.gif)
        canvas.create_image(self.canvasWidth/2, self.canvasHeight/2,
                            image=self.photoimage)
        
        # some labels
        Label(gframe, text='Radio Enable Pin'
              ).grid(row=self.gridDigitalRowOffset+5, column=5, columnspan=3,
                     sticky=W)
        Label(gframe, text='Serial TX'
              ).grid(row=self.gridDigitalRowOffset+13, column=5, columnspan=3,
                     sticky=W)
        Label(gframe, text='Serial RX'
              ).grid(row=self.gridDigitalRowOffset+14, column=5, columnspan=3,
                     sticky=W)
        
        
        # analog buttons
        self.anaLabel = {'0': StringVar(),
                         '1': StringVar(),
                         '2': StringVar(),
                         '3': StringVar(),
                         '4': StringVar(),
                         '5': StringVar()}
        
        for n in range(6):
            Button(gframe, text='READ', command=lambda n=n: self.anaRead(n)
                   ).grid(row=self.gridAnalogRowOffset+n, column=1)
            Label(gframe, width=5, textvariable=self.anaLabel['{}'.format(n)],
                  relief=RAISED
                  ).grid(row=self.gridAnalogRowOffset+n, column=0)
            Label(gframe, width=4, bg='red', fg='white', text='A{0:02d}'.format(n)
                  ).grid(row=self.gridAnalogRowOffset+n, column=2)

        # digital variables
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
        
        # digital labels
        for n in range(14):
            if n > 7:
                r = self.gridDigitalRowOffset+13 - n
                color = 'green4'
                fgcolor = 'white'
            else:
                r = self.gridDigitalRowOffset+14 - n
                color = 'blue'
                fgcolor = 'white'
            Label(gframe, bg=color, fg=fgcolor, text="D{0:02d}".format(n)).grid(row=r,
                                                                    column=4)

        # input buttons
        Button(gframe, text='READ', command=lambda: self.read('02')
               ).grid(row=self.gridDigitalRowOffset+12, column=5, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['02'], relief=RAISED,
              anchor=CENTER,
              ).grid(row=self.gridDigitalRowOffset+12, column=8)
        Button(gframe, text='READ', command=lambda: self.read('03')
               ).grid(row=self.gridDigitalRowOffset+11, column=5, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['03'], relief=RAISED,
              anchor=CENTER,
              ).grid(row=self.gridDigitalRowOffset+11, column=8)
        Button(gframe, text='READ', command=lambda: self.read('07')
               ).grid(row=self.gridDigitalRowOffset+7, column=5, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['07'], relief=RAISED,
              anchor=CENTER,
              ).grid(row=self.gridDigitalRowOffset+7, column=8)
        Button(gframe, text='READ', command=lambda: self.read('10')
               ).grid(row=self.gridDigitalRowOffset+3, column=5, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['10'], relief=RAISED,
              anchor=CENTER,
              ).grid(row=self.gridDigitalRowOffset+3, column=8)
        Button(gframe, text='READ', command=lambda: self.read('12')
               ).grid(row=self.gridDigitalRowOffset+1, column=5, sticky=W+E)
        Label(gframe, width=5, textvariable=self.digital['12'], relief=RAISED,
              anchor=CENTER,
              ).grid(row=self.gridDigitalRowOffset+1, column=8)


        # output buttons
        Button(gframe, text='LOW', command=lambda: self.off('06')
               ).grid(row=self.gridDigitalRowOffset+8, column=6, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('06')
               ).grid(row=self.gridDigitalRowOffset+8, column=5, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('06')
               ).grid(row=self.gridDigitalRowOffset+8, column=7, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['06'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital06'
              ).grid(row=self.gridDigitalRowOffset+8, column=8)

        Button(gframe, text='LOW', command=lambda: self.off('09')
               ).grid(row=self.gridDigitalRowOffset+4, column=6, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('09')
               ).grid(row=self.gridDigitalRowOffset+4, column=5, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('09')
               ).grid(row=self.gridDigitalRowOffset+4, column=7, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['09'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital09'
              ).grid(row=self.gridDigitalRowOffset+4, column=8)
        Button(gframe, text='LOW', command=lambda: self.off('11')
               ).grid(row=self.gridDigitalRowOffset+2, column=6, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('11')
               ).grid(row=self.gridDigitalRowOffset+2, column=5, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('11')
               ).grid(row=self.gridDigitalRowOffset+2, column=7, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['11'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital11'
              ).grid(row=self.gridDigitalRowOffset+2, column=8)
        Button(gframe, text='LOW', command=lambda: self.off('13')
               ).grid(row=self.gridDigitalRowOffset+0, column=6, sticky=W+E)
        Button(gframe, text='HIGH', command=lambda: self.on('13')
               ).grid(row=self.gridDigitalRowOffset+0, column=5, sticky=W+E)
        Button(gframe, text='PWM', command=lambda: self.pwm('13')
               ).grid(row=self.gridDigitalRowOffset+0, column=7, sticky=W+E)
        Entry(gframe, width=5, textvariable=self.digital['13'], validate='key',
              invalidcommand='bell', validatecommand=self.vpwm, justify=CENTER,
              name='digital13'
              ).grid(row=self.gridDigitalRowOffset+0, column=8)


        # servo button
        Label(gframe, text='SERVO').grid(row=self.gridDigitalRowOffset+9,
                                         column=5, sticky=W)
        servo = Scale(gframe, orient=HORIZONTAL, from_=0, to=180, digits=3,
                      command=lambda value: self.servo(value), showvalue=0,
                      )
        servo.grid(row=self.gridDigitalRowOffset+9, column=6, columnspan=2,
                   sticky=W+E)
        
        Label(gframe, width=5, textvariable=self.servoVal, anchor=CENTER,
              relief=RAISED).grid(row=self.gridDigitalRowOffset+9, column=8)
              
        # set servo intial val
        servo.set(90)
        
        # count button
        Label(gframe, text='COUNT').grid(row=self.gridDigitalRowOffset+10, column=5, sticky=W)
        Button(gframe, text='READ', command=lambda: self.count('READ')
               ).grid(row=self.gridDigitalRowOffset+10, column=6, sticky=W+E)
        Button(gframe, text='SET', command=lambda: self.count('SET')
               ).grid(row=self.gridDigitalRowOffset+10, column=7, sticky=W+E)
        self.countEntry = Entry(gframe, width=5,
                                textvariable=self.digital['04'], validate='key',
                                invalidcommand='bell',
                                validatecommand=self.vcount, justify=CENTER
                                )
        self.countEntry.grid(row=self.gridDigitalRowOffset+10, column=8)

    def initBottom(self):
        # llap command box
        lframe = Frame(self.master, relief=RAISED, borderwidth=2,
                       name='llapFrame')
        lframe.pack(expand=1, fill=BOTH)
        
        Label(lframe, text='Send a LLAP command: a').pack(side=LEFT)
        Label(lframe, textvariable=self.devID, relief=RAISED,
              width=2).pack(side=LEFT)
        
        
        self.payloadInput = Entry(lframe, width=9, validate='key',
                           textvariable=self.payload, invalidcommand='bell',
                           validatecommand=self.vpay, name='dataInput')
        self.payloadInput.pack(side=LEFT)

        # send and quite buttons
        Button(lframe, text='Send', command=self.sendCommand).pack(side=LEFT)
        
        # history
        Label(lframe, text='History', width=10, anchor=E).pack(side=LEFT)
        self.historyBox = ttk.Combobox(lframe, width=12, state='readonly')
        self.historyBox.pack(side=LEFT)
        self.historyBox['values'] = self.historyList
        Button(lframe, text='Send Previous', command=self.sendOldCommand).pack(side=LEFT)

        Button(lframe, text='Quit', command=self.endCommand).pack(side=RIGHT)

    def initSerialConsoles(self):
        # serial console
        sframe = Frame(self.master, relief=RAISED, borderwidth=2,
                       name='serialFrame')
        sframe.pack(expand=1, fill=BOTH)

        self.text = Text(sframe, state=DISABLED, relief=RAISED, borderwidth=2,
                         height=6, width=self.serialConsoleWidth)
        self.text.pack(side=LEFT, expand=1, fill=BOTH)
        self.serialText = Text(sframe, state=DISABLED, relief=RAISED,
                               borderwidth=2, height=6,
                               width=self.serialConsoleWidth)
        self.serialText.pack(side=LEFT, expand=1, fill=BOTH)

        self.text.tag_config('send', foreground='red')
        self.text.tag_config('receive', foreground='blue')
        self.serialText.tag_config('send', foreground='red')
        self.serialText.tag_config('receive', foreground='blue')
    
        # status bar button
#        bframe = Frame(master, relief=RAISED, borderwidth=1,
#                       name='statusBarFrame')
#        bframe.pack(fill=BOTH, expand=1)
#        bah = Button(bframe, text='Bah')
#        bah.pack(side=LEFT)

    def anaRead(self, num):
        print("anaRead: {}".format(num))
        self.sendLLAP(self.devID.get(), "A{0:02d}READ".format(num))
    
    def read(self, num):
        print("read: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}READ".format(num))
    
    def on(self, num):
        print("high: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}HIGH".format(num))
    
    def off(self, num):
        print("low: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}LOW".format(num))
    
    def pwm(self, num):
        print("pwm: {}".format(num))
        if self.digital[num].get().isdigit():
            if int(self.digital[num].get()) < 255:
                self.sendLLAP(self.devID.get(),
                              "D{}PWM{}".format(num, self.digital[num].get()))
            else:
                self.appendText("D{} PWM: '{}' is too large. Range 0-255\n".
                                format(num, self.digital[num].get()))
        else:
            self.appendText("D{} PWM: '{}' is not a number. Range 0-255\n".
                            format(num, self.digital[num].get()))
            
    def servo(self, value):
        print("servo")
        self.servoVal.set(int(float(value)))
        self.sendLLAP(self.devID.get(), "SERVO{}".format(int(float(value))))
        

    def count(self, mode):
        print("count: {}".format(mode))
        if mode == 'READ':
            self.sendLLAP(self.devID.get(), "COUNT")
        elif mode == 'SET':
            #check we have a number
            if self.digital['04'].get().isdigit():
                self.sendLLAP(self.devID.get(),
                              "COUNT{}".format(self.digital['04'].get()))
            else:
                self.appendText("Setting COUNT requires a number\n")

    # validation rules

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

    def initValidationRules(self):
        self.vpwm = (self.master.register(self.validPWM), '%d', '%P', '%S')
        self.vcount = (self.master.register(self.validCount), '%d', '%P', '%S')
        self.vpay = (self.master.register(self.validPayloadLenght),
                     '%P', '%W', '%S')
        self.vdev = (self.master.register(self.validDevID), '%d',
                     '%P', '%W', '%P', '%S')

    def validPayloadLenght(self, P, W, S):
        if len(P) <= 9:
            if S.islower():
                self.payload.set(P.upper())
                self.payloadInput.after_idle(self.vpaySet)
            else:
                return True
        else:
            return False
                
    def validDevID(self, d, P, W, s, S):
        valid = False 
        validChar = ['-', '#', '@', '?', '\\', '*']
        for c in validChar:
            if S.startswith(c):
                valid = True
    
        if d == '0' or d == '-1':
            return True
        elif S.islower() and (len(P) <= 2):
            self.devID.set(P.upper())
            self.devIDInput.after_idle(self.vdevSet)
        elif (S.isupper() or valid) and (len(P) <= 2):
            return True
        else:
            return False
    
    def validPWM(self, d, P, S):
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

    def vdevSet(self):
        self.devIDInput.icursor(self.devIDInput.index(INSERT)+1)
        self.devIDInput.config(validate='key')

    def vpaySet(self):
        self.payloadInput.icursor(self.payloadInput.index(INSERT)+1)
        self.payloadInput.config(validate='key')

    # send commands
    def sendCommand(self):
        self.sendLLAP(self.devID.get(), self.payload.get())
        llap = "a{}{}".format(self.devID.get(), self.payload.get())
        while len(llap) < 12:
            llap += '-'
        
        if len(self.historyList) == 0 or self.historyList[0] != llap:
            self.historyList.insert(0, llap)
            self.historyBox['values'] = self.historyList
            self.historyBox.current(0)
                           
    def sendOldCommand(self):
        if self.historyBox.get().startswith("a"):
            self.sendLLAP(self.historyBox.get()[1:3], self.historyBox.get()[3:].strip('-'))
        
    def sendLLAP(self, devID, payload):
        self.text.config(state=NORMAL)
        self.text.insert(END, "Sending LLAP to {} with Data: {}\n".
                         format(devID, payload), 'send')
        self.sendLLAPcommand(devID, payload)
        self.text.see(END)
        self.text.config(state=DISABLED)


    # display update stuff
    def appendText(self,msg):
        self.text.config(state=NORMAL)
        self.text.insert(END, msg)
        self.text.see(END)
        self.text.config(state=DISABLED)

    def appendSerial(self, msg, tag):
        self.serialText.config(state=NORMAL)
        self.serialText.insert(END, msg, tag)
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
                self.text.insert(END, "Received LLAP from {} with Data: {}\n".
                                 format(msg['devID'],msg['payload']), 'receive')
                if msg['devID'] == self.devID.get():
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
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.endApplication)
        self.master.title("Sandy")
        self.master.resizable(0,0)
        
        self.disconnectFlag = threading.Event()
        self.t_stop = threading.Event()

        # Create the queue
        self.queue = Queue.Queue()

        self.s = serial.Serial()
        self.s.baudrate = 9600
        self.s.timeout = None            # blocking read's

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication,
                           self.sendLLAP, self.connect)


        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()
    
    def connect(self):
        if self.gui.connectText.get().startswith('Connect'):
            self.s.port = self.gui.comport.get()
            try:
                self.s.open()
                self.gui.connectText.set('Disconnect')
            except serial.SerialException, e:
                self.gui.appendText("Could not open port %r: %s\n" % (port, e))
        else:
            self.disconnectFlag.set()
            self.gui.connectText.set('Connect')
            
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
            self.gui.appendSerial(llapMsg, 'send')
    
    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        One important thing to remember is that the thread has to yield
        control.
        """
        while self.running:
            if self.s.isOpen():
                if self.s.inWaiting():
                    char = self.s.read()
                    self.gui.appendSerial(char, 'receive')
                    if char == 'a':
                        llapMsg = 'a'
                        llapMsg += self.s.read(11)
                        self.gui.appendSerial(llapMsg[1:], 'receive')
                        self.queue.put({'devID': llapMsg[1:3],
                                       'payload': llapMsg[3:].rstrip("-")})
            if self.disconnectFlag.isSet():
                self.s.close()
                self.disconnectFlag.clear()

            self.t_stop.wait(0.01)
    
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
client = ThreadedClient(root)
root.mainloop()