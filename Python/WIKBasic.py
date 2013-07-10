#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Basic Interface
    Ciseco Ltd. Copyright 2013
    
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
import time
#import ImageTk
from Tabs import *


if sys.platform == 'darwin':
    port = '/dev/tty.usbmodem000001'
elif sys.platform == 'win32':
    port = ''
else:
    port = '/dev/ttyAMA0'

baud = 9600


INTRO = """ BIG Introduction Text
Sandy
LLAP
Basic's
Advance Analog
"""
ADCExplain = """This is lots of text about how we can do different analog readings
Volts
Temperature
Percentage

RAW ADC is the number give back by the Xino RF this is between 0 and 1023

"""

ADC = """This is the raw ADC value converted to Volts
Volts = (RawADC / 1023 * 5.0V) * Correction Factor"""

TMP = """Temperature is calculated using the following formula
RTemp = (1023.0/RawADC) - 1)*10000
Kelvin = RTEMP*BVAL / (BVAL+RTEMP*( log(Rtherm/RNOM) ) )
Temperature = Kelvin - 273.15"""

LDR = """The light reading from the LDR is presented as a percentage
Percentage = RawADC / 1023 * 100"""

LEDTEXT = """LED traffic lights
Connect the matching LED and a 470R 
resistor to the following pins
D13 Red
D11 Yellow
D10 Green"""

SCANTEXT = """Scanning LED's
Connect an LED and 470R resistor 
to each of the following pins
D13, D11, D09, D06"""


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
        self.servoVal = IntVar()
        self.payload = StringVar()
        self.payload.set("HELLO")
        self.comport = StringVar()
        self.comport.set(port)
        self.connectText = StringVar()
        self.connectText.set("Connect")
        self.devID = StringVar()
        self.devID.set("--")
        self.gif = "XinoRF.gif"
        self.historyList = []
        self.widthMain = 828
        self.heightMain = 662
        self.heightTab = 480
        self.widthOffset = 650
        self.heightOffset = 150
        
        self.anaLabel = {'0': StringVar(),
                         '1': StringVar(),
                         '2': StringVar(),
                         '3': StringVar(),
                         '4': StringVar(),
                         '5': StringVar(),
                         '0VOLT': StringVar(),
                         '0TMP': StringVar(),
                         '0LDR': StringVar(),
                         '0Correction': StringVar()}

        
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
        
        self.scan = {'Delay': StringVar(),
                     'DelayInput': 0,
                     'Repeat':  StringVar(),
                     'RepeatInput': 0,
                     'position': 0,
                     'count': 0,
                     'button': 0,
                     'forward': True}
        
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
                                                  self.config.get('WIKBasic',
                                                                  'window_width_offset'),
                                                  self.config.get('WIKBasic',
                                                                  'window_height_offset')
                                                  )
                             )
        self.master.protocol("WM_DELETE_WINDOW", self.endCommand)
        self.master.title("WIK Basic's Interface v{}".format(self.currentVersion))
        self.master.resizable(0,0)

        self.tabFrame = Frame(self.master, name='tabFrame')
        self.tabFrame.pack()
        self.initTabBar()
        self.initIntro()
        self.initGrid()
        self.initAdvAna()
        self.initLights()
        
        self.tBarFrame.show()

        self.initLLAPBar()
        self.initSerialConsoles()

        self.setDefaults()
    
    def debugPrint(self, msg):
        if self.debugArg or self.debug:
            print(msg)

    def checkArgs(self):
        self.debugPrint("Parse Args")
        parser = argparse.ArgumentParser(description='Wireless Inventors Kit Basic Interface')
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


        Label(iframe, text=INTRO).grid(row=0, column=0, columnspan=6,
                                       sticky=W+E+N+S)
    
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
    
    def initGrid(self):
        self.debugPrint("Setting up Basic's Tab")
        # grid frame
        gframe = Tab(self.tabFrame, "Basic's", fname='grid')
        gframe.config(relief=RAISED, borderwidth=2, width=self.widthMain,
                      height=self.heightTab)
        self.tBarFrame.add(gframe)

        # pack the grid to get the damn size right
        Canvas(gframe, bd=0, highlightthickness=0, width=self.widthMain-4,
               height = 28).grid(row=0, column=0, columnspan=9)
               
        for n in range(17):
            """
            Canvas(aframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                   width=50, height=28, highlightthickness=0,
                   highlightcolor='white'
                   ).grid(row=n, column=0)
            """       
            Canvas(gframe, bd=0, width=50, height=28, highlightthickness=0,
                   ).grid(row=n, column=1)
    
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
        Label(gframe, text='Reserved for Radio Enable Pin'
              ).grid(row=self.gridDigitalRowOffset+5, column=5, columnspan=4,
                     sticky=W)
        Label(gframe, text='Serial TX'
              ).grid(row=self.gridDigitalRowOffset+13, column=5, columnspan=3,
                     sticky=W)
        Label(gframe, text='Serial RX'
              ).grid(row=self.gridDigitalRowOffset+14, column=5, columnspan=3,
                     sticky=W)
        
        
        # analog buttons
        for n in range(6):
            Button(gframe, text='READ', command=lambda n=n: self.anaRead(n)
                   ).grid(row=self.gridAnalogRowOffset+n, column=1)
            Label(gframe, width=5, textvariable=self.anaLabel['{}'.format(n)],
                  relief=RAISED
                  ).grid(row=self.gridAnalogRowOffset+n, column=0)
            Label(gframe, width=4, bg='red', fg='white',
                  text='A{0:02d}'.format(n)
                  ).grid(row=self.gridAnalogRowOffset+n, column=2)
        
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
            Label(gframe, bg=color, fg=fgcolor,
                  text="D{0:02d}".format(n)).grid(row=r, column=4)

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
        Label(gframe, width=5, textvariable=self.digital['13'], relief=RAISED,
              anchor=CENTER
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
              
        # set servo initial val
        servo.set(90)
        
        # count button
        Label(gframe, text='COUNT').grid(row=self.gridDigitalRowOffset+10,
                                         column=5, sticky=W)
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

    def initAdvAna(self):
        self.debugPrint("Setting up Advanced Analog Tab")
        aframe = Tab(self.tabFrame, "Advanced Analog", fname='advana')
        aframe.config(relief=RAISED, borderwidth=2, width=self.widthMain,
                      height=self.heightTab)
        self.tBarFrame.add(aframe)
    
        cols = 12
        # pack the grid to get the damn size right
        for n in range(1,17):
            """
            Canvas(gframe, bg=("black" if n%2 else "gray"), bd=0, relief=FLAT,
                    width=50, height=28, highlightthickness=0,
                    highlightcolor='white'
                    ).grid(row=n, column=0)
            """
            Canvas(aframe, bd=0, relief=FLAT, width=(self.widthMain-4)/cols,
                   height=28, highlightthickness=0
                   ).grid(row=n, column=1)
        

        Canvas(aframe, bd=0, relief=FLAT, width=(self.widthMain-4),
               height=28, highlightthickness=0).grid(row=0, column=0,
                                                     columnspan=cols)

        Button(aframe, text='Read', command=lambda:self.anaRead(0)
               ).grid(row=10-4, column=1, rowspan=2,
                      columnspan=cols-2, sticky=W+E+N+S)
               
        Label(aframe, text=ADCExplain).grid(row=1, column=1, columnspan=cols-2,
                                            rowspan=5, sticky=W+E+N+S)
    
        Label(aframe, text='Volts').grid(row=9,
                                           column=1, sticky=E)
        Label(aframe, text='Correction Factor').grid(row=10,
                                                     column=1, sticky=E)
        Label(aframe, textvariable=self.anaLabel['0VOLT'], width=10,
              relief=RAISED).grid(row=9, column=2, sticky=W)
              
        self.correctionInput = Entry(aframe,
                                     textvariable=self.anaLabel['0Correction'],
                                     width=9, validate='key',
                                     invalidcommand='bell',
                                     validatecommand=self.vfloat,
                                     justify=CENTER, name='correctionInput')
        self.correctionInput.grid(row=10, column=2, sticky=W)
              
        Label(aframe, text=ADC).grid(row=8, column=3,
                                     columnspan=cols-4, rowspan=3, sticky=W+E)

        
        Label(aframe, text='Temperature',
              anchor=E).grid(row=12, column=1, sticky=E)
        Label(aframe, textvariable=self.anaLabel['0TMP'], width=10,
              relief=RAISED).grid(row=12,
                                  column=2, sticky=W)
        Label(aframe, text=TMP).grid(row=11, column=3,
                                     columnspan=cols-4, rowspan=3, sticky=W+E)

        
        Label(aframe, text='Percentage',
              anchor=E).grid(row=15, column=1, sticky=E)
        Label(aframe, textvariable=self.anaLabel['0LDR'], width=10,
              relief=RAISED).grid(row=15, column=2,
                                  sticky=W)
        Label(aframe, text=LDR).grid(row=14, column=3,
                                     columnspan=cols-4, rowspan=3, sticky=W+E)

    def initLights(self):
        self.debugPrint("Setting up LED Tab")
        mframe = Tab(self.tabFrame, "LED's", fname='leds')
        mframe.config(relief=RAISED, borderwidth=2, width=self.widthMain,
                      height
                      =self.heightTab)
        self.tBarFrame.add(mframe)
    
        lframe = Frame(mframe, name='left')
        lframe.pack(side=LEFT)
        canvas = Canvas(lframe, bd=0, width=(self.widthMain/2)-2,
                        height=self.heightTab-4, highlightthickness=0)
        canvas.grid(row=0, column=0, rowspan=11, columnspan=5)
    
        Label(lframe, text=LEDTEXT).grid(row=1, column=0, rowspan=4,
                                         columnspan=5, sticky=W+E+N+S)
        
        ch=50
        Canvas(lframe, bg='red', height=ch).grid(row=5, column=2, sticky=W+E)
        Button(lframe, bg='red', text='RED LED on D13', width=20,
               command=lambda: self.setLed(0)).grid(row=5, column=2)
        Canvas(lframe, bg='yellow', height=ch).grid(row=7, column=2, sticky=W+E)
        Button(lframe, bg='yellow', text='YELLOW LED on D11', width=20,
               command=lambda: self.setLed(1)).grid(row=7, column=2)
        Canvas(lframe, bg='green', height=ch).grid(row=9, column=2, sticky=W+E)
        Button(lframe, bg='green', text='GREEN LED on D09', width=20,
               command=lambda: self.setLed(2)).grid(row=9, column=2)
    
        rframe = Frame(mframe, name='right')
        rframe.pack(side=RIGHT)
        
        canvas = Canvas(rframe, bd=0, width=(self.widthMain/2)-2,
                        height=self.heightTab-4, highlightthickness=0)
        canvas.grid(row=0, column=0, rowspan=12, columnspan=5)
        
        Label(rframe, text=SCANTEXT).grid(row=1, column=0, rowspan=4,
                                          columnspan=5, sticky=W+E+N+S)
    
    
        Label(rframe, text='Delay', anchor=E).grid(row=5, column=1, sticky=E)
        self.scan['DelayInput'] = Entry(rframe, textvariable=self.scan['Delay'],
                                        width=5, validate='key',
                                        invalidcommand='bell',
                                        validatecommand=self.vint,
                                        justify=CENTER)
        self.scan['DelayInput'].grid(row=5, column=2, sticky=E+W)
        Label(rframe, text='ms', anchor=W).grid(row=5, column=3, sticky=W)
        
        Label(rframe, text='Repeat', anchor=E).grid(row=7, column=1, sticky=E)
        self.scan['RepeatInput'] = Entry(rframe, textvariable=self.scan['Repeat'],
                                         width=5, validate='key',
                                         invalidcommand='bell',
                                         validatecommand=self.vint,
                                         justify=CENTER)
        self.scan['RepeatInput'].grid(row=7, column=2, sticky=E+W)
    

        self.scan['button'] = Button(rframe, text='Go', command=self.scanGo)
        self.scan['button'].grid(row=9, column=1, columnspan=3, sticky=E+W)
    
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
        self.anaLabel['0Correction'].set('1')
        self.correctionInput.config(validate='key')
        self.scan['Repeat'].set('1')
        self.scan['RepeatInput'].config(validate='key')
        self.scan['Delay'].set('500')
        self.scan['DelayInput'].config(validate='key')
    
    def anaRead(self, num):
        self.debugPrint("anaRead: {}".format(num))
        self.sendLLAP(self.devID.get(), "A{0:02d}READ".format(num))
    
    def read(self, num):
        self.debugPrint("read: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}READ".format(num))
    
    def on(self, num):
        self.debugPrint("high: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}HIGH".format(num))
    
    def off(self, num):
        self.debugPrint("low: {}".format(num))
        self.sendLLAP(self.devID.get(), "D{}LOW".format(num))
    
    def pwm(self, num):
        self.debugPrint("pwm: {}".format(num))
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
        self.debugPrint("servo: {}".format(value))
        self.servoVal.set(int(float(value)))
        self.sendLLAP(self.devID.get(), "SERVO{}".format(int(float(value))))
        

    def count(self, mode):
        self.debugPrint("count: {}".format(mode))
        if mode == 'READ':
            self.sendLLAP(self.devID.get(), "COUNT")
        elif mode == 'SET':
            #check we have a number
            if self.digital['04'].get().isdigit():
                self.sendLLAP(self.devID.get(),
                              "COUNT{}".format(self.digital['04'].get()))
            else:
                self.appendText("Setting COUNT requires a number\n")

    def setLed(self, c):
        self.debugPrint("setLED: {}".format(c))
        if c == 0:
            # set D09
            self.sendLLAP(self.devID.get(), "D13HIGH")
            self.sendLLAP(self.devID.get(), "D11LOW")
            self.sendLLAP(self.devID.get(), "D09LOW")
        elif c == 1:
            # set D11
            self.sendLLAP(self.devID.get(), "D13LOW")
            self.sendLLAP(self.devID.get(), "D11HIGH")
            self.sendLLAP(self.devID.get(), "D09LOW")
        elif c == 2:
            # set D13
            self.sendLLAP(self.devID.get(), "D13LOW")
            self.sendLLAP(self.devID.get(), "D11LOW")
            self.sendLLAP(self.devID.get(), "D09HIGH")

    def scanGo(self):
        self.debugPrint("Setup Scan")
        # need to track delay, repeats, position in sequence
        # or just refer to var's?
        
        self.scan['position'] = 0
        self.scan['count'] = 0
        self.scan['forward'] = True
        
        #disable button and entry
        self.scan['DelayInput'].config(state=DISABLED)
        self.scan['RepeatInput'].config(state=DISABLED)
        self.scan['button'].config(state=DISABLED)
        self.scanDo()
                
    def scanDo(self):
        self.debugPrint("Scanning... pos: {} count: {}".format(self.scan['position'],
                                                               self.scan['count']))
        if self.scan['position'] == 0:
            self.sendLLAP(self.devID.get(), "D13HIGH")
            self.sendLLAP(self.devID.get(), "D11LOW")
            self.sendLLAP(self.devID.get(), "D09LOW")
            self.sendLLAP(self.devID.get(), "D06LOW")
            self.scan['position'] = 1
            if self.scan['forward'] == False:
                self.scan['count'] += 1
                self.scan['forward'] = True
        elif self.scan['position'] == 1:
            self.sendLLAP(self.devID.get(), "D13LOW")
            self.sendLLAP(self.devID.get(), "D11HIGH")
            self.sendLLAP(self.devID.get(), "D09LOW")
            self.sendLLAP(self.devID.get(), "D06LOW")
            self.scan['position'] = 2 if self.scan['forward'] == True else 0
        elif self.scan['position'] == 2:
            self.sendLLAP(self.devID.get(), "D13LOW")
            self.sendLLAP(self.devID.get(), "D11LOW")
            self.sendLLAP(self.devID.get(), "D09HIGH")
            self.sendLLAP(self.devID.get(), "D06LOW")
            self.scan['position'] = 3 if self.scan['forward'] == True else 1
        elif self.scan['position'] == 3:
            self.sendLLAP(self.devID.get(), "D13LOW")
            self.sendLLAP(self.devID.get(), "D11LOW")
            self.sendLLAP(self.devID.get(), "D09LOW")
            self.sendLLAP(self.devID.get(), "D06HIGH")
            self.scan['position'] = 2
            self.scan['forward'] = False
        
        if self.scan['count'] < int(self.scan['Repeat'].get()): 
            self.master.after(int(self.scan['Delay'].get()), self.scanDo)
        else: 
            # enable button and entry
            self.scan['DelayInput'].config(state=NORMAL)
            self.scan['RepeatInput'].config(state=NORMAL)
            self.scan['button'].config(state=NORMAL)

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
        self.vpwm = (self.master.register(self.validPWM), '%d', '%P', '%S')
        self.vcount = (self.master.register(self.validCount), '%d', '%P', '%S')
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
                        self.anaLabel[
                                      msg['payload'][2:3]
                                      ].set(msg['payload'][4:])
                        if msg['payload'][2:3] == '0':
                            self.anaLabel['0VOLT'
                                          ].set(self.voltCalc(msg['payload'][4:]))
                            self.anaLabel['0TMP'
                                          ].set(self.tmpCalc(msg['payload'][4:]))
                            self.anaLabel['0LDR'
                                          ].set(self.ldrCalc(msg['payload'][4:]))
                    
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
                            msg['payload'][1:3] == '11'):
                            self.master.nametowidget(".tabFrame.grid.digital{}".format(
                                  msg['payload'][1:3])).config(validate='key')
                            

                self.text.see(END)
                self.text.config(state=DISABLED)
                self.queue.task_done()
            except Queue.Empty:
                pass

    def voltCalc(self, ADCvalue):
        AREF = 5.0
        MAX = 1023
        volt = (float(ADCvalue) / MAX * AREF) * float(self.anaLabel['0Correction'].get())
        return "{:0.2f}V".format(volt)

    def tmpCalc(self, ADCvalue):
        BVAL = 3977              # default beta value for the thermistor; adjust for your thermistor
        RTEMP = 25.0 + 273.15    # reference temperature (25C expressed in Kelvin)
        RNOM = 10000.0           # default reference resistance at reference temperature; adjust to calibrate
        SRES = 10000.0           # default series resister value; adjust as per your implementation
        # calculate the temperature from an ADC value
        if float(ADCvalue) == 0:
            ADCvalue = 0.001        # catch div by zero
        # value of the resistance of the thermistor
        Rtherm = (1023.0/float(ADCvalue) - 1)*10000
        # see http:#en.wikipedia.org/wiki/Thermistor for an explanation of the formula
        T = RTEMP*BVAL/(BVAL+RTEMP*(math.log(Rtherm/RNOM)))
        # convert from Kelvin to Celsius
        T = T - 273.15

        return u"{:0.2f}\u2103".format(T)
    
    def ldrCalc(self, val):
        MAX = 1023
        return "{} %".format(int((float(val)/MAX)*100))


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

if __name__ == "__main__":
    root = Tk()
    client = ThreadedClient(root)
    root.mainloop()