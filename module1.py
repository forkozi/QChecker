import Tkinter as tk
import ttk
import time
import threading

num_las = 3700


class MonApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.progress_window = tk.Toplevel()

        self.progress_frame = ttk.Frame(self.progress_window)
        self.progress_frame.grid()

        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, maximum=num_las, length=500)  # mode='indeterminate'
        self.progress.grid(column=0, row=0)

        self.progress_label = tk.Label(self.progress_frame)
        self.progress_label.grid(column=1, row=0)

        self.run_qaqc()

    def run_qaqc(self):
        def thread_progress():
            
            for i, l in enumerate(range(1, num_las)):
                self.progress.step(1)
                self.progress_label['text'] = '{} of {}'.format(i+1, num_las)
                #time.sleep(0.0001)
            
            self.progress_label['text'] = r'Done'

            self.progress.grid_forget()

        threading.Thread(target=thread_progress).start()

if __name__ == '__main__':
    app = MonApp()
    app.mainloop()
