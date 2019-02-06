from Tkinter import Button, Tk, HORIZONTAL

from ttk import Progressbar
import time
import threading


class MonApp(Tk):
    def __init__(self):
        Tk.__init__(self)


        self.btn = Button(self, text='Start Progress', command=self.start_progress)
        self.btn.grid(row=0,column=0)
        self.progress = Progressbar(self, orient=HORIZONTAL, maximum=3700, length=500)  # mode='indeterminate'

    def start_progress(self):
        def real_traitement():
            self.progress.grid(row=1,column=0)
            self.progress.step(1)
            #time.sleep(10)
            #self.progress.stop()
            #self.progress.grid_forget()

            self.btn['state']='normal'

        self.btn['state']='disabled'
        threading.Thread(target=real_traitement).start()

if __name__ == '__main__':
    app = MonApp()
    app.mainloop()
