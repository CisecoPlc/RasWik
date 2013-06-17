#!/usr/bin/env python
"""
    Some text
    hello
"""

from Tkinter import *
from Tkconstants import RIGHT, LEFT, Y, BOTH
from tkFont import Font
from ScrolledText import ScrolledText

def example():
    import __main__
    from Tkconstants import END
    
    stext = ScrolledText(bg='white', height=10)
    stext.insert(END, __main__.__doc__)
    
    f = Font(family="times", size=30, weight="bold")
    stext.tag_config("font", font=f)
    
    stext.insert(END, "Hello", "font")
    stext.pack(fill=BOTH, side=LEFT, expand=True)
    stext.focus_set()
    stext.mainloop()

if __name__ == "__main__":
    example()