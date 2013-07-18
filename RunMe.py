#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Run Me
    Ciseco Ltd. Copyright 2013
    
    Author: Matt Lloyd
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
    Quick Wrapper to move us into the Python/ directory
"""
import os
import sys
args = sys.argv[:]

args.insert(0, sys.executable)
if sys.platform == 'win32':
    args = ['"%s"' % arg for arg in args]

os.chdir('Python/')
os.execv(sys.executable, args)
