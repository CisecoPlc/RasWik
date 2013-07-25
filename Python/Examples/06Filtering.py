#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Python Example 06Filtering.py
    Copyright (c) 2013 Ciseco Ltd.
    
    Filtering incoming LLAP messages
    In this example we will filter incoming messages for a set devID
    Then filter different replies to be handled differently
    
    
    Author: Matt Lloyd
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
"""
#import the PySerial library and sleep from the time library
import serial
from time import sleep
# for temperature we also need the math library
import math

# declare to variables, holding the com port we wish to talk to and the speed
port = '/dev/ttyAMA0'
baud = 9600

# open a serial connection using the variables above
ser = serial.Serial(port=port, baudrate=baud)

# wait for a moment before doing anything else
sleep(0.2)

# this time we are going to send 4 commands one after the other
# the replies will get buffered by Python until
# we later call ser.read()
# after each ser.write() we print to the console and sleep() to give the
# XinoRF time to reply before sending the next
ser.write('a--D13HIGH--')
print("Sent a--D13HIGH--")
sleep(1)
ser.write('a--A00READ--')
print("Sent a--A00READ--")
sleep(1)
ser.write('a--A01READ--')
print("Sent a--A01READ--")
sleep(1)
ser.write('a--D02READ--')
print("Sent a--D02READ--")
sleep(0.2)

# loop until the serial buffer is empty
while ser.inWaiting():
    # read a single character
    char = ser.read()
    
    # check we have the start of a LLAP message
    if char == 'a':
        # start building the full llap message by adding the 'a' we have
        llapMsg = 'a'
        
        # read in the next 11 characters form the serial buffer
        # into the llap message
        llapMsg += ser.read(11)
        
        # now we split the llap message apart into devID and data
        devID = llapMsg[1:3]
        data = llapMsg[3:]
        
        # check the devID is correct for our device
        # (WIK ships as -- be default)
        if devID == '--':
            # check to see if the message is about A00
            if data.startswith('A00'):
                # split out the pin & the return value and print to the console
                print("Got Analog reading for {} of {}".format(data[0:3],
                                                               data[4:].strip('-')))
            
            # check to see if the message relates to a digital pin
            elif data.startswith('D'):
                # split out the pin & the return value and print to the console
                print("Got digital reading for {} of {}".format(data[0:3],
                                                                data[3:].strip('-')))


# close the serial port
ser.close()

# at the end of the script python automatically exits
