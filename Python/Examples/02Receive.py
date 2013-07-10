#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Python Example 02Receive.py
    Ciseco Ltd. Copyright 2013
    
    This basic Python example just open a serial port and send one LLAP message
    and receive a reply and prints it to the console
    
    
    Author: Matt Lloyd
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
"""
#import the PySerial library and sleep from the time library
import serial
from time import sleep

# declare to variables, holding the com port we wish to talk to and the speed
port = '/dev/ttyAMA0'
baud = 9600

# open a serial connection using the variables above
ser = serial.Serial(port=port, baudrate=baud)

# wait for a moment before doing anything else
sleep(0.2)

# write a--D13HIGH-- out to the serial port
# this should turn the XinoRF LED on
# changing this to a--D13LOW--- will turn the LED off
ser.write('a--D13HIGH--')

# wait for a moment before doing anything else
sleep(0.2)

# read 12 characters from the serial port
reply = ser.read(12)

# print the replay
print(reply)

# close the serial port
ser.close

# at the end of the script python automatically exits