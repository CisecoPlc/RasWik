from Tkinter import *

# the constructor syntax is:
# OptionMenu(master, variable, *values)

OPTIONS = [
    "egg",
    "bunny",
    "chicken"
]

master = Tk()

variable = StringVar(master)
variable.set(OPTIONS[0]) # default value

w = apply(OptionMenu, (master, variable) + tuple(OPTIONS))
w.pack()

mainloop()
