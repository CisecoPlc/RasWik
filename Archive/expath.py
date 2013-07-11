#!/usr/bin/env python
import sys,os
import Tkinter as tk

root = tk.Tk()

a = " name and separator {} {}".format(os.name, os.sep)
b = "os.getcwd() -  CWD {} ".format(os.getcwd())
c = "sys.path[0] -  location of code: code {}".format(sys.path[0])
d = "os.getenv('HOME') -  user home dir {}".format(os.getenv('HOME'))
e = "os.path.expanduser('~') -  user home dir {}".format(os.path.expanduser('~'))

os.chdir('Python/')
f = os.getcwd()

tk.Label(root, text=a).pack()
tk.Label(root, text=b).pack()
tk.Label(root, text=c).pack()
tk.Label(root, text=d).pack()
tk.Label(root, text=e).pack()
tk.Label(root, text=f).pack()


root.mainloop()