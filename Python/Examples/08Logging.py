#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Python Example 08Logging.py
    Copyright (c) 2013 Ciseco Ltd.
    
    Logging incomming LLAP messgaes to a text file
    include conversion to temperature
    
    Authors: Matt Lloyd & Rob van der Linden
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
"""
#import the PySerial library and sleep from the time library
import serial
from time import sleep, asctime
# for temperature we also need the math library
import math

# declare to variables, holding the com port we wish to talk to and the speed
port = '/dev/ttyAMA0'
baud = 9600

# open a serial connection using the variables above
ser = serial.Serial(port=port, baudrate=baud)

# wait for a moment before doing anything else
sleep(0.2)

# setup a counter starting at 0
count = 0
# number of times round the loop
maxcount = 20

# open a file to log the data to
file = open('./log.csv', 'w')

# we are going to output data in a csv format so this adds a heading row
file.write("\"Time\",\"LLAP\",\"Temperature\"\n")

# clear out the serial input buffer to ensure there are no old messages lying around
ser.flushInput()

# loop over the block of code while the count is less than maxcount
# when the count = maxcount the loop will break and we carry on with the rest
while count < maxcount:
    # write a--A00READ-- out to the serial port
    # this will return the current ADC reading for Pin A0
    ser.write('a--A00READ--')
    
    # wait for a moment before doing anything else
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
                # if not we skip the section of code
                if data.startswith('A00'):
                    # take just the last part of the message
                    # strip the traling -'s
                    # and convert to an int
                    adc = int(data[4:].strip('-'))
                    
                    # to calculate the temperature we use a more complex formula
                    # here we store some of the fixed numbers in variables
                    BVAL = 3977              # default beta value for the thermistor
                    RTEMP = 25.0 + 273.15    # reference temperature (25C expressed in Kelvin)
                    RNOM = 10000.0           # default reference resistance at reference temperature; adjust to calibrate
                    SRES = 10000.0           # default series resister value; adjust as per your implementation
                    
                    # to catch a divide by zero error we check the value of adc and fake it if needed
                    if adc == 0:
                        adc = 0.001
                    
                    # value of the resistance of the thermistor
                    Rtherm = (1023.0/float(adc) - 1)*10000
                    
                    # see http:#en.wikipedia.org/wiki/Thermistor for an explanation of the formula
                    kelvin = RTEMP*BVAL/(BVAL+RTEMP*(math.log(Rtherm/RNOM)))
                    
                    # convert from Kelvin to Celsius
                    temperature = kelvin - 273.15
                    
                    # now log the time, orignal llap messgae and temperature
                    # to the file in a csv format
                    file.write("\"{}\",\"{}\",\"{:0.2f}\"\n".format(asctime(),
                                                                    llapMsg,
                                                                    temperature
                                                                    )
                               )

                    # little bit of user feed back so we know the script is working
                    print("Logged {}".format(count))

                    # increase the count by 1 at the end of the block
                    count += 1

# close the file
file.close()

# close the serial port
ser.close()

# at the end of the script python automatically exits
