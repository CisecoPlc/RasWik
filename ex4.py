import Tkinter as tk

class MyApp():
    def __init__(self):
        self.root = tk.Tk()

        # valid percent substitutions (from the Tk entry man page)
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed
        # %s = value of entry prior to editing
        # %S = the text string being inserted or deleted, if any
        # %v = the type of validation that is currently set
        # %V = the type of validation that triggered the callback
        #      (key, focusin, focusout, forced)
        # %W = the tk name of the widget
        vcmd = (self.root.register(self.OnValidate), 
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.entry = tk.Entry(self.root, validate="key", 
                              validatecommand=vcmd)
        self.entry.pack()
        self.root.mainloop()

    def OnValidate(self, d, i, P, s, S, v, V, W):
        print "OnValidate:"
        print "d='%s'" % d
        print "i='%s'" % i
        print "P='%s'" % P
        print "s='%s'" % s
        print "S='%s'" % S
        print "v='%s'" % v
        print "V='%s'" % V
        print "W='%s'" % W
        # only allow if the string is lowercase
        return (S.lower() == S)

app=MyApp()
