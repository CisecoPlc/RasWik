#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Graphing Application
    Copyright (c) 2013 Ciseco Ltd.
    
    Author: Matt Lloyd
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
"""
from Tkinter import *
import ttk
import sys
import os
import subprocess
import argparse
import math
import serial
import json
import urllib2
import httplib
import shutil
import ConfigParser
import tkMessageBox
import threading
import Queue
import zipfile
import time as time_
#import ImageTk
from Tabs import *


if sys.platform == 'darwin':
    port = '/dev/tty.usbmodem000001'
elif sys.platform == 'win32':
    port = ''
else:
    port = '/dev/ttyAMA0'

baud = 9600


INTRO = """Welcome to the Wireless Inventors Kit Graph Application.

First set up the serial COM port used to communicate with the Raspberry Pi radio and press connect.

Then go to the tabs above to enjoy graphs for temperature, light levels and voltage.
"""

TEMPTEXT = """Graph of Temperature over Time
    
Based on thermistior readings from A0
    
Attach a thermistor and 10K resistor
to A0 as in Activity 10
"""

class GuiPart:
    def __init__(self, master, queue, endCommand, sendLLAP, connect):
        self.master = master
        self.queue = queue
        self.sendLLAPcommand = sendLLAP
        self.endCommand = endCommand
        self.connectCommand = connect
        
        self.debug = False # until we read config
        self.debugArg = False # or get command line
        self.configFileDefault = "wik_defaults.cfg"
        self.configFile = "wik.cfg"

        
        # variables used later
        self.gridComRowOffset = 1
        self.gridDigitalRowOffset = 1
        self.gridAnalogRowOffset = 10
        self.serialConsoleWidth = 45
        self.canvasWidth = 400
        self.canvasHeight = 459
        self.payload = StringVar()
        self.payload.set("HELLO")
        self.comport = StringVar()
        self.comport.set(port)
        self.connectText = StringVar()
        self.connectText.set("Connect")
        self.devID = StringVar()
        self.devID.set("--")
        self.gif = "XinoRF.gif"
        self.prof = "ProfWireless-250px.gif"
        self.profX = 207
        self.profY = 250
        self.historyList = []
        self.widthMain = 828
        self.heightMain = 662
        self.heightTab = 480
        self.widthOffset = 650
        self.heightOffset = 150
       
        self.tempGraph = {'Delay': StringVar(),
                      'DelayInput': 0,
                      'Repeat':  StringVar(),
                      'RepeatInput': 0,
                      'position': 0,
                      'count': 0,
                      'button': 0,
                      'forward': True,
                      'canvas': 0,
                      'line': ''}

        self.dataPoints = []

    def on_excute(self):
        self.checkArgs()
        self.readConfig()
        self.runBasic()
    
    def runBasic(self):
        # validation setup
        self.initValidationRules()
        
        # Set up the GUI
        self.master.geometry("{}x{}+{}+{}".format(self.widthMain,
                                                  self.heightMain,
                                                  self.config.get('WIKGraph',
                                                                  'window_width_offset'),
                                                  self.config.get('WIKBasic',
                                                                  'window_height_offset')
                                                  )
                             )
        self.master.protocol("WM_DELETE_WINDOW", self.endCommand)
        self.master.title("WIK Graph v{}".format(self.currentVersion))
        self.master.resizable(0,0)

        self.tabFrame = Frame(self.master, name='tabFrame')
        self.tabFrame.pack()
        self.initTabBar()
        self.initIntro()
        self.initTemp()
        
        self.tBarFrame.show()

        self.initLLAPBar()
        self.initSerialConsoles()

        self.setDefaults()
    
    def debugPrint(self, msg):
        if self.debugArg or self.debug:
            print(msg)

    def checkArgs(self):
        self.debugPrint("Parse Args")
        parser = argparse.ArgumentParser(description='Wireless Inventors Kit Graph Application')
        parser.add_argument('-d', '--debug',
                            help='Extra Debug Output, overrides wik.cfg setting',
                            action='store_true')
        parser.add_argument('-s', '--subprocess',
                            help='Used when launching as a sub process of WIK Launcher',
                            action='store_true')
                            
        self.args = parser.parse_args()
        
        if self.args.debug:
            self.debugArg = True
        else:
            self.debugArg = False

    def readConfig(self):
        self.debugPrint("Reading Config")

        self.config = ConfigParser.SafeConfigParser()

        # load defaults
        try:
            self.config.readfp(open(self.configFileDefault))
        except:
            self.debugPrint("Could Not Load Default Settings File")

        # read the user config file
        if not self.config.read(self.configFile):
            self.debugPrint("Could Not Load User Config, One Will be Created on Exit")

        if not self.config.sections():
            self.debugPrint("No Config Loaded, Quitting")
            sys.exit()

        self.debug = self.config.getboolean('Shared', 'debug')
        self.devID.set(self.config.get('Shared', 'devID'))

        try:
            f = open(self.config.get('Update', 'versionfile'))
            self.currentVersion = f.read()
            f.close()
        except:
            pass
            
    def initTabBar(self):
        self.debugPrint("Setting up TabBar")
        # tab button frame
        self.tBarFrame = TabBar(self.tabFrame, "Introduction", fname='tabBar')
        self.tBarFrame.config(relief=RAISED, pady=4)
        
        # tab buttons
        # place holder
        #Button(self.tBarFrame, text="Introduction").pack(side=LEFT)
        #Button(self.tBarFrame, text="Basic's").pack(side=LEFT)
        Button(self.tBarFrame, text='Quit', command=self.endCommand
               ).pack(side=RIGHT)


    def initIntro(self):
        self.debugPrint("Setting up Introduction Tab")
        iframe = Tab(self.tabFrame, "Introduction", fname='intro')
        iframe.config(relief=RAISED, borderwidth=2, width=self.widthMain,
                      height=self.heightTab)
        self.tBarFrame.add(iframe)
    
        canvas = Canvas(iframe, bd=0, width=self.widthMain-4,
                        height=self.heightTab-(29*4), highlightthickness=0)
        canvas.grid(row=0, column=0, columnspan=6)
        
        for n in range(4):
            Canvas(iframe, bd=0, highlightthickness=0,
                   width=self.widthMain-4, height=28
                   ).grid(row=self.gridComRowOffset+n, column=0, columnspan=6)

        # prof image
        self.profimage = PhotoImage(file=self.prof)
        canvas.create_image(self.profX/2, self.profY/2,
                           image=self.profimage)
                           
        canvas.create_text(180, 120, text=INTRO, anchor=NW)
        
        # com selection bits
        Label(iframe, text='Com Port').grid(row=self.gridComRowOffset+0,
                                            column=1, columnspan=2)
        Entry(iframe, textvariable=self.comport, width=17
              ).grid(row=self.gridComRowOffset+1, column=1, columnspan=2)
        Button(iframe, textvariable=self.connectText,
               command=self.connectCommand, width=10
               ).grid(row=self.gridComRowOffset+2, column=1, columnspan=2)

        Label(iframe, text='Device ID').grid(row=self.gridComRowOffset+0,
                                             column=3, columnspan=2)
        self.devIDInput = Entry(iframe, width=3, validate='key', justify=CENTER,
                                textvariable=self.devID, invalidcommand='bell',
                                validatecommand=self.vdev, name='devIDInput')
                                
        self.devIDInput.grid(row=self.gridComRowOffset+1, column=3,
                             columnspan=2)
        Label(iframe, text="A-Z, -, #, @, ?, \, *"
              ).grid(row=self.gridComRowOffset+2, column=3, columnspan=2)
        if not self.config.getboolean('Shared', 'devid_enabled'):
            self.devIDInput.config(state=DISABLED)
        
    def initTemp(self):
        self.debugPrint("Setting up Temp Tab")
        mframe = Tab(self.tabFrame, "Temperature", fname='temp')
        mframe.config(relief=RAISED, borderwidth=2, width=self.widthMain,
                      height=self.heightTab)
        self.tBarFrame.add(mframe)
        
        graphwidth = 500
        widths = (20, 55, (self.widthMain-55-64-35-graphwidth-10), 35, 20,
                  graphwidth+10, 20)
        heights = (28, self.heightTab-280-4, 56, 28, 56, 28, 56, 28)
        
        # pack the grid
        for n in range(7):
            Canvas(mframe, bd=0, relief=FLAT,
                   width=widths[n], height=28, highlightthickness=0
                   ).grid(row=0, column=n)

        for n in range(8):
            Canvas(mframe, bd=0, relief=FLAT,
                   height=heights[n], width=widths[1], highlightthickness=0
                   ).grid(row=n, column=1)

        # text and buttons to the left
        Label(mframe, text=TEMPTEXT).grid(row=1, column=1, columnspan=3,
                                           sticky=W+E+N+S)

        Label(mframe, text='Delay', anchor=E).grid(row=2, column=1, sticky=E)
        self.tempGraph['DelayInput'] = Entry(mframe,
                                         textvariable=self.tempGraph['Delay'],
                                         width=5, validate='key',
                                         invalidcommand='bell',
                                         validatecommand=self.vint,
                                         justify=CENTER)
        self.tempGraph['DelayInput'].grid(row=2, column=2, sticky=E+W)
        Label(mframe, text='ms', anchor=W).grid(row=2, column=3, sticky=W)
        
        Label(mframe, text='Repeat', anchor=E).grid(row=4, column=1, sticky=E)
        self.tempGraph['RepeatInput'] = Entry(mframe,
                                          textvariable=self.tempGraph['Repeat'],
                                          width=5, validate='key',
                                          invalidcommand='bell',
                                          validatecommand=self.vint,
                                          justify=CENTER)
        self.tempGraph['RepeatInput'].grid(row=4, column=2, sticky=E+W)
                                         
        self.tempGraph['button'] = Button(mframe, text='Go', command=self.tempGraphGo)
        self.tempGraph['button'].grid(row=6, column=1, columnspan=3, sticky=E+W)

        # main graph canvas
        self.tempGraph['canvas'] = Canvas(mframe, bg='white', bd=2, relief=RAISED,
                             height=300, width=graphwidth)
        self.tempGraph['canvas'].grid(row=1, column=5, rowspan=6)

        # axis and labels
        self.tempGraph['canvas'].create_line(50,275,470,275, width=2)
        self.tempGraph['canvas'].create_line(50,275,50,35,  width=2)
            
        for i in range(15):
            x = 50 + (i * 30)
            self.tempGraph['canvas'].create_line(x,275,x,270, width=2)
            # graphCanvas.create_text(x,279, text='%d'% (10*i), anchor=N)

        for i in range(9):
            y = 275 - (i * 30)
            self.tempGraph['canvas'].create_line(50,y,55,y, width=2)
            self.tempGraph['canvas'].create_text(46,y, text='%5.1f'% (5.*i),
                                             anchor=E)


    def initLLAPBar(self):
        self.debugPrint("Setting up LLAP Command Bar")
        # llap command box
        lframe = Frame(self.master, relief=RAISED, borderwidth=2,
                       name='llapFrame', pady=4)
        lframe.pack(expand=1, fill=BOTH)
        
        Label(lframe, text='Send a LLAP command to address ').pack(side=LEFT)
        Label(lframe, textvariable=self.devID, relief=RAISED,
              width=2).pack(side=LEFT)
        Label(lframe, text=' with DATA').pack(side=LEFT)
        
        self.payloadInput = Entry(lframe, width=9, validate='key',
                           textvariable=self.payload, invalidcommand='bell',
                           validatecommand=self.vpay, name='dataInput')
        self.payloadInput.pack(side=LEFT)

        # send and quite buttons
        Button(lframe, text='Send', command=self.sendCommand).pack(side=LEFT)
        
        # history
        Button(lframe, text='Send Previous',
               command=self.sendOldCommand).pack(side=RIGHT)
        self.historyBox = ttk.Combobox(lframe, width=14, justify=CENTER,
                                       state='readonly')
        self.historyBox.pack(side=RIGHT)
        self.historyBox['values'] = self.historyList
        Label(lframe, text='History', anchor=E).pack(side=RIGHT)


    def initSerialConsoles(self):
        self.debugPrint("Setting up Serial Console")
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
    
    def setDefaults(self):
        self.debugPrint("Setting Entry Defaults")
        self.tempGraph['Repeat'].set('20')
        self.tempGraph['RepeatInput'].config(validate='key')
        self.tempGraph['Delay'].set('1000')
        self.tempGraph['DelayInput'].config(validate='key')
        
    def anaRead(self, num):
        self.debugPrint("anaRead: {}".format(num))
        self.sendLLAP(self.devID.get(), "A{0:02d}READ".format(num))
   
    def tempGraphGo(self):
        self.debugPrint("Setup Graphing Run")
    
        self.tempGraph['count'] = 0
        self.dataPoints = [0]

        self.tempGraph['DelayInput'].config(state=DISABLED)
        self.tempGraph['RepeatInput'].config(state=DISABLED)
        self.tempGraph['button'].config(state=DISABLED)
        self.tempGraphDo()

    def tempGraphDo(self):
        self.debugPrint("Logging to graph count: {}".format(self.tempGraph['count']))
    
        if self.tempGraph['count'] < int(self.tempGraph['Repeat'].get()):
            self.tempGraph['count'] += 1
            self.anaRead(0)
            self.master.after(int(self.tempGraph['Delay'].get()), self.tempGraphDo)
        else:
            # enable button and entry
            self.tempGraph['DelayInput'].config(state=NORMAL)
            self.tempGraph['RepeatInput'].config(state=NORMAL)
            self.tempGraph['button'].config(state=NORMAL)
    
    def updateGraph(self, ADC):
        self.debugPrint("Updating Graph")
                              
        self.dataPoints.append(self.tmpCalc(ADC))
        
        if not self.tempGraph['line'] == '':
            self.tempGraph['canvas'].delete(self.tempGraph['line'])
        
        points = []
        
        start = len(self.dataPoints)-15
        if start < 0:
            start = 0
        stop = len(self.dataPoints)

        for n in range(start, stop):
            x = 470-((len(self.dataPoints)-n-1)*30)
            y = 275-((float(self.dataPoints[n])/5.0)*30)
            points.append([x,y])
        
        if len(self.dataPoints) > 1:
            self.tempGraph['line'] = self.tempGraph['canvas'].create_line(points,
                                                                  fill='black')
                              
                              
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
        self.debugPrint("Setting up GUI validation Rules")
        self.vpay = (self.master.register(self.validPayloadLenght),
                     '%P', '%W', '%S')
        self.vdev = (self.master.register(self.validDevID), '%d',
                     '%P', '%W', '%P', '%S')
        self.vfloat = (self.master.register(self.validFloat), '%d', '%s', '%S')
        self.vint = (self.master.register(self.validInt), '%d', '%s', '%S')
    
    def validInt(self, d, s, S):
        if d == '0':
            return True
        if S.isdigit():
            return True
        else:
            return False
    
    def validFloat(self, d, s, S):
        if d == '0':
            return True
        if S.isdigit() or (S == '.' and s.find('.') == -1):
            return True
        else:
            return False
    
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
            self.sendLLAP(self.historyBox.get()[1:3],
                          self.historyBox.get()[3:].strip('-'))
        
    def sendLLAP(self, devID, payload):
        self.text.config(state=NORMAL)
        self.text.insert(END, "Sending LLAP to {} with DATA: {}\n".
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
                self.text.insert(END,
                         "Received LLAP from {} with DATA: {}\n".format(
                                                msg['devID'], msg['payload']),
                         'receive')
                if msg['devID'] == self.devID.get():
                    if msg['payload'].startswith("A"):
                        if msg['payload'][2:3] == '0':
                            self.updateGraph(msg['payload'][4:])
                
                self.text.see(END)
                self.text.config(state=DISABLED)
                self.queue.task_done()
            except Queue.Empty:
                pass

    def tmpCalc(self, ADCvalue):
        BVAL = 3977              # default beta value for the thermistor; adjust for your thermistor
        RTEMP = 25.0 + 273.15    # reference temperature (25C expressed in Kelvin)
        RNOM = 10000.0           # default reference resistance at reference temperature; adjust to calibrate
        SRES = 10000.0           # default series resister value; adjust as per your implementation
        # calculate the temperature from an ADC value
        if float(ADCvalue) == 0:
            ADCvalue = 0.001        # catch div by zero
        elif float(ADCvalue) >= 1023:
            ADCvalue = 1022.009
        # value of the resistance of the thermistor
        Rtherm = (1023.0/float(ADCvalue) - 1)*10000
        # see http:#en.wikipedia.org/wiki/Thermistor for an explanation of the formula
        T = RTEMP*BVAL/(BVAL+RTEMP*(math.log(Rtherm/RNOM)))
        # convert from Kelvin to Celsius
        T = T - 273.15

        return "{:0.2f}".format(T)


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
        
        self.disconnectFlag = threading.Event()
        self.t_stop = threading.Event()

        # Create the queue
        self.queue = Queue.Queue()

        self.s = serial.Serial()
        self.s.baudrate = baud
        self.s.timeout = None            # blocking read's

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication,
                           self.sendLLAP, self.connect)

        self.gui.on_excute()

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
        self.master.after(5, self.periodicCall)

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

if __name__ == "__main__":
    root = Tk()
    client = ThreadedClient(root)
    root.mainloop()