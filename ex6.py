from Tkinter import *
import os
root = Tk()

def buttonPressed():
    # this is the problem in the program.
    # it keeps returning [''] in the print statement and doesn't quit
    # any applications
    listOfApps = form.get().split(',')
    # the print is just so i can see the output
    print(listOfApps)
    # goes through each item in list and kills them(yes i know there are much easier
    # ways to do this, i'm just trying to learn a bit about GUI and the os module
    for i in listOfApps:
        try:
            os.system("killall " + i)
        except:
            pass
def buttonPressed2():
    filesToOpen = form2.get().split(', ')
    for i in filesToOpen:
        try:
            os.system("open " + i)
        except:
            pass

container = Frame(root)
form = Entry(container)
button = Button(container)
root['background'] = 'red'
container['background'] = 'red'
button['text'] = 'kill matching processes'
button['command'] = buttonPressed
form['background'] = 'red'
form['border'] = '5'
form['highlightthickness'] = '0'


container2 = Frame(root)
form2 = Entry(container2)
button2 = Button(container2)
root['background'] = 'blue'
container2['background'] = 'blue'
button2['text'] = 'Open desired files'
button2['command'] = buttonPressed2
form2['background'] = 'blue'
form2['border'] = '5'
form2['highlightthickness'] = '0'

container.pack()
form.pack()
button.pack()

container2.pack()
form2.pack()
button2.pack()

#starts up window
root.mainloop()
