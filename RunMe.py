#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Wireless Inventors Kit Run Me
    Copyright (c) 2013 Ciseco Ltd.
    
    Author: Matt Lloyd
    
    This code is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    
    Quick Wrapper to move us into the Python/ directory
"""
import os
import sys
import inspect
args = sys.argv[:]
args[0] = 'WIKLauncher.py'
args.insert(0, sys.executable)
if sys.platform == 'win32':
    args = ['"%s"' % arg for arg in args]

os.chdir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/Python/')
os.execv(sys.executable, args)
