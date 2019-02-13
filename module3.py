from Tkinter import *
import threading

class FakeConsole(Frame):
    def __init__(self, root, *args, **kargs):
        Frame.__init__(self, root, *args, **kargs)

        #white text on black background,
        #for extra versimilitude
        self.text = Text(self, bg="black", fg="white")
        self.text.pack()

        #list of things not yet printed
        self.printQueue = []

        #one thread will be adding to the print queue, 
        #and another will be iterating through it.
        #better make sure one doesn't interfere with the other.
        self.printQueueLock = threading.Lock()

        self.after(5, self.on_idle)

    #check for new messages every five milliseconds
    def on_idle(self):
        with self.printQueueLock:
            for msg in self.printQueue:
                self.text.insert(END, msg)            
                self.text.see(END)
            self.printQueue = []
        self.after(5, self.on_idle)

    #print msg to the console
    def show(self, msg, sep="\n"):
        with self.printQueueLock:
            self.printQueue.append(str(msg) + sep)

#warning! Calling this more than once per program is a bad idea.
#Tkinter throws a fit when two roots each have a mainloop in different threads.
def makeConsoles(amount):
    root = Tk()
    consoles = [FakeConsole(root) for n in range(amount)]
    for c in consoles:
        c.pack()
    threading.Thread(target=root.mainloop).start()
    return consoles

a,b = makeConsoles(2)

a.show("This is Console 1")
b.show("This is Console 2")

a.show("I've got a lovely bunch of cocounts")
a.show("Here they are standing in a row")

b.show("Lorem ipsum dolor sit amet")
b.show("consectetur adipisicing elit")