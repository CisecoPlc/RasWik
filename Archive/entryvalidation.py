# File: entryvalidation.py
# References:
#    http://stackoverflow.com/questions/4140437/python-tkinter-interactively-validating-entry-widget-content
#    http://infohost.nmt.edu/tcc/help/pubs/tkinter//entry.html
#    http://infohost.nmt.edu/tcc/help/pubs/tkinter//events.html
#    http://www.tcl.tk/man/tcl8.5/TkCmd/ttk_entry.htm
#
#     valid percent substitutions (see first link above)
#         %d = Type of action (1=insert, 0=delete, -1 for others)
#         %i = index of char string to be inserted/deleted, or -1
#         %P = value of the entry if the edit is allowed
#         %s = value of entry prior to editing
#         %S = the text string being inserted or deleted, if any
#         %v = the type of validation that is currently set
#         %V = the type of validation that triggered the callback
#              (key, focusin, focusout, forced)
#         %W = the tk name of the widget
 
 
from tkinter import *
from tkinter import ttk
 
from demopanels import MsgPanel, SeeDismissPanel
 
class EntryValidationDemo(ttk.Frame):
     
    def __init__(self, isapp=True, name='entryvalidationdemo'):
        ttk.Frame.__init__(self, name=name)
        self.pack(expand=Y, fill=BOTH)
        self.master.title('Entry Validation Demo')
        self.isapp = isapp
        self._create_widgets()
         
    def _create_widgets(self):
        if self.isapp:
            MsgPanel(self,
                     ["Four different entries are displayed below.  ",
                      "You can add characters by pointing, ",
                      "clicking and typing, though each is constrained ",
                      "in what it will accept.\n\n",
                      "    The first only accepts 32-bit integers or an empty ",
                      " string (validation on leaving the field).\n",
                      "    The second only accepts strings with fewer than ten ",
                      "characters and sounds the bell when an attempt to go ",
                      "over the limit is made (checks each keystroke).\n",
                      "    The third accepts 10 digit phone numbers and formats",
                      "them during entry. Only digits are accepted as input. ",
                      "Left and Right arrow keys skip over format characters. ",
                      "A 'backspace' is handled as a left arrow. A bell sounds ",
                      "if illegal characters are attempted.\n",
                      "     The fourth is a password ",
                      "field that accepts up to eight characters (silently ",
                      "ignoring further ones), and displaying them as ",
                      "asterisk characters."])
             
            SeeDismissPanel(self)
         
        self._create_demo_panel()
         
    def _create_demo_panel(self):
        demoPanel = ttk.Frame(self)
        demoPanel.pack(side=TOP)
         
        # create entry panels
        integer = self._create_int_panel()
        constraint = self._create_constrained_panel() 
        phone = self._create_phone_panel()
        pwd = self._create_pwd_panel()
         
        # position panels
        integer.grid(in_=demoPanel, row=0, column=0, padx='3m', pady='1m', sticky=EW)
        constraint.grid(in_=demoPanel, row=0, column=1, padx='3m', pady='1m', sticky=EW)    
        phone.grid(in_=demoPanel, row=1, column=0, padx='3m', pady='1m', sticky=EW)
        pwd.grid(in_=demoPanel, row=1, column=1, padx='3m', pady='1m', sticky=EW)
         
        # configure resize constraints
        demoPanel.columnconfigure((0,1), uniform=True)
     
    # =====================================================================
    # Integer Entry
    # =====================================================================
    def _create_int_panel(self):
        # the entry is validated when focus is lost
        # if it does not contain a valid integer or
        # an empty string, it is cleared, given back
        # the focus and a beep is heard
        lf = ttk.Labelframe(text='Integer Entry')
        e = ttk.Entry(lf, validate='focusout')
         
        # register the validation/invalid methods
        # %W - entry widget name
        # %P - entry string
        e['validatecommand'] = (self.register(self._is_valid_int), '%P')
        e['invalidcommand'] = (self.register(self._invalid_int), '%W')
         
        e.pack(fill=X, expand=Y, padx='1m', pady='1m')
        e.focus_set()
         
        return lf
     
    def _is_valid_int(self, txt):
        # txt - value in %P
         
        if not txt:         # accept empty string
            return True
         
        try:
            int(txt)       
            return True     # accept integer
         
        except ValueError:  # not an integer
            return False   
 
    def _invalid_int(self, widgetName):
            # called automatically when the
            # validation command returns 'False'
             
            # get entry widget
            widget = self.nametowidget(widgetName)
             
            # clear entry
            widget.delete(0, END)
             
            # return focus to integer entry
            widget.focus_set()
            widget.bell()
 
    # =====================================================================
    # Constrained Entry
    # =====================================================================
 
    def _create_constrained_panel(self):
        # the length of the entry is constrained to 10 chars
        lf = ttk.Labelframe(text='Constrained Entry')
        var = StringVar()
        e = ttk.Entry(lf, validate='key', textvariable= var,
                      invalidcommand='bell',
                      validatecommand = lambda var=var: len(var.get()) < 10)
         
        e.pack(fill=X, expand=Y, padx='1m', pady='1m')
         
        return lf
     
    # =====================================================================
    # Phone Number Entry
    # =====================================================================
     
    def _create_phone_panel(self):
        # phone number entry field
        # accepts a 10 digit phone number
        # and formats it as it's entered
         
        lf = ttk.Labelframe(text='Phone Entry')
     
        e = ttk.Entry(lf)
         
        # capture edits 'before' the entry
        # text is updated
        e.bind('<KeyPress>', self._format_phonenum)
                 
        e.pack(fill=X, expand=Y, padx='1m', pady='1m')
         
        return lf           
     
    def _format_phonenum(self, event):
        # formats the entry text as it's being
        # entered; format is '1-(ddd)-ddd-dddd'
         
        if event.keysym == 'Tab':   # allow tab to next field
            return
         
        widget = event.widget       # get the entry widget
        entry = widget.get()        # get the text content
        idx = widget.index(INSERT)  # current cursor position
                 
        if event.keysym == 'Left':  # skip format chars
            if idx == 3:
                return 'break'      # block edit
            elif idx == 8:
                widget.icursor(6)
            elif idx == 12:
                widget.icursor(11)
         
        elif event.keysym == 'Right':   # skip format chars
            if idx == 5:
                widget.icursor(7)
            elif idx == 10:
                widget.icursor(11)
         
        elif event.keysym == 'BackSpace':
            # convert a backspace to a 'Left' event
            widget.event_generate('<Left>')
            return 'break'
         
        else:       
            # block if char not a digit
            # or phone number will be to long
            if not event.char.isdigit() or idx > 15:
                widget.bell()
                return 'break'  # block edit
             
            if idx == widget.index(END):
                # allow adding a new digit,
                # inserting format characters
                # where necessary
                if idx == 0:    # insert format chars
                    widget.insert(idx, '1-(' + event.char)
                    return 'break'
                 
                if idx == 6:    # insert format chars
                    widget.insert(idx,')-' + event.char)
                    return 'break'
                 
                if idx == 7 or idx == 11:   # insert format char
                    widget.insert(idx,'-' + event.char)
                    return 'break'
             
            else:  # replacing a digit
                if idx in [0,1,2,6,7,11]:
                    # disallow if overwriting
                    # format chars
                    widget.bell()
                    return 'break'
                 
                else:  # ok to replace
                    widget.delete(idx)
                 
    # =====================================================================
    # Password Entry
    # =====================================================================
     
    def _create_pwd_panel(self):
        # masks entered characters with an asterisk
        # constrains the length of the entry to 8 chars
        lf = ttk.Labelframe(text='Password Entry')
        var = StringVar()
        e = ttk.Entry(lf, validate='key', show='*',
                      textvariable = var,
                      validatecommand = lambda v=var: len(v.get()) < 8)
         
        e.pack(fill=X, expand=Y, padx='1m', pady='1m')
         
        return lf   
 
if __name__ == '__main__':
    EntryValidationDemo().mainloop()
