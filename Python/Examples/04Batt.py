#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Python Example 04Batt.py
    Ciseco Ltd. Copyright 2013
   
    Polled (or repeated) send and receive of LLAP messages, measuring voltage on A0 and setting red/yellow/green charge light    
    
    Authors: Matt Lloyd & Rob van der Linden
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
    """
#import the PySerial library and sleep from the time library
import serial
from time import sleep

# declare to variables, holding the com port we wish to talk to and the speed
port = '/dev/ttyACM0'  #AMA0
baud = 9600

# open a serial connection using the variables above
ser = serial.Serial(port=port, baudrate=baud)

# wait for a moment before doing anything else
sleep(0.2)

# setup a counter starting at 0
count = 0
maxcount = 20    # number of times round the loop

# loop over the block of code while the count is less than maxcount
# when the count = maxcount the loop will break and we carry on with the rest
while count < maxcount:

    # clear out the serial input buffer to ensure there are no old messages lying around
    ser.flushInput()

    # then wait a while till this completes
    sleep(0.2)

    # write a--A00READ-- out to the serial port
    # this will return the current ADC reading for Pin A0
    ser.write('a--A00READ--')

    # wait for a moment before doing anything else
    sleep(0.2)

    # read 12 characters from the serial port
    
    reply = ser.read(12)

    # print (reply)   # for debugging uncomment this command

    # at this point reply should contain something like 'a--A01+532--'
    # the numbers after the + are the ADC reading we interested in

    # check the message contains the data from A0
    # if not, ignore it
    if "a--A0" in reply:
        # take just the last part of the message
        value = reply[7:]
    
        # strip the trailing '-'
        value = value.strip('-')

        # convert the string in value to an integer
        v = int(value)

        # dividing the range of the ADC (1024) into 3 areas:
        # if v lies below 342 light up the red LED only
        # if v is between 342 and 684 light up the yellow LED
        # if v is above 684 light up the green LED
             
        if v < 342:
            # print("RED")
            ser.write("a--D09LOW---")
            sleep(0.2)
            ser.write("a--D11LOW---")
            sleep(0.2)
            ser.write("a--D13HIGH--")
        elif v >=342 and v <= 685:
            # print("YELLOW")
            ser.write("a--D09LOW---")
            sleep(0.2)
            ser.write("a--D11HIGH--")
            sleep(0.2)
            ser.write("a--D13LOW---")
        elif v > 685:
            # print("GREEN")
            ser.write("a--D09HIGH--")
            sleep(0.2)
            ser.write("a--D11LOW---")
            sleep(0.2)
            ser.write("a--D13LOW---")
         
        # print the ADC Value
        # here we are doing a little formatting of the output
        # the {} inside the quotes is replaced with the contents of value
        print("ADC: {}".format(value))
        
        # increase the count by 1 at the end of the block
        count += 1

# close the serial port
ser.close

# at the end of the script python automatically exits
