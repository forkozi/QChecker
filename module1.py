import Tkinter as tk
import ttk
import threading
import time

class QaqcApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)


        # start button calls the "initialization" function bar_init, you can pass a variable in here if desired
        self.start_button = ttk.Button(self, text='Start bar', command=lambda: self.bar_init(2500))
        self.start_button.pack()

        # the progress bar will be referenced in the "bar handling" and "work" threads
        self.load_bar = ttk.Progressbar(self)
        self.load_bar.pack()

    def bar_init(self, var):
        # first layer of isolation, note var being passed along to the self.start_bar function
        # target is the function being started on a new thread, so the "bar handler" thread
        self.start_bar_thread = threading.Thread(target=self.start_bar, args=(var,))
        
        # start the bar handling thread
        self.start_bar_thread.start()

    def start_bar(self, var):
        # the load_bar needs to be configured for indeterminate amount of bouncing
        self.load_bar.config(mode='indeterminate', maximum=100, value=0)
        
        # 8 here is for speed of bounce
        self.load_bar.start(1)
        
        # start the work-intensive thread, again a var can be passed in here too if desired
        self.work_thread = threading.Thread(target=self.work_task, args=(var,))
        self.work_thread.start()
       
        # close the work thread
        self.work_thread.join()
        
        # stop the indeterminate bouncing
        self.load_bar.stop()
        
        # reconfigure the bar so it appears reset
        self.load_bar.config(value=0, maximum=0)

    def work_task(self, wait_time):
        for x in range(wait_time):
            print(3 * x)
            time.sleep(0.001)

if __name__ == '__main__':
    app = QaqcApp()
    app.geometry('400x850')
    app.mainloop()  # tk functionality