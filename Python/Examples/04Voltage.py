#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Python Example 04Voltage.py
    Ciseco Ltd. Copyright 2013
    
    Conversion of a ADC Value to Voltage
    
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

# setup a counter starting at 0
count = 0

# loop over the block of code while the count is less than 4
# when the count = 4 the loop will break and we carry on with the rest
while count < 4:
    # write a--A00READ-- out to the serial port
    # this will return the current ADC reading for Pin A0
    ser.write('a--A00READ--')
    
    # wait for a moment before doing anything else
    sleep(0.2)
    
    # read 12 characters from the serial port
    reply = ser.read(12)
    
    # at this point reply should contain something like 'a--A01+532--'
    # the numbers after the + are the ADC reading we interested in
    
    # take just the last part of the message
    adc = reply[7:]
    
    # strip the trailing '-'
    adc = adc.strip('-')
    
    # adc is currently a string, we need to convert this to an integer
    # before we can do any maths
    adc = int(adc)
    
    # to calculate the voltage we use the following formula
    volts = (adc / 1023.0 * 5.0)
    
    # print the ADC Value and the Volts value
    # here we are doing a little formatting of the output
    # the first {} inside the quotes is replaced with the contents of value
    # the second {} is replaced with our calculated Volts
    # the :0.2f inside the second {} limits the
    # floating point number to two decimal places
    print("ADC: {} Volts: {:0.2f}V".format(adc, volts))
    
    # increase the count by 1 at the end of the block
    count += 1

# close the serial port
ser.close()

# at the end of the script python automatically exits