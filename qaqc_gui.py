from Tkinter import *
import Tkinter, Tkconstants, tkFileDialog
 
LARGE_FONT = ('Verdanna', 12)
LARGE_FONT_BOLD = ('Verdanna', 12, 'bold')
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')
SMALL_FONT = ('Verdanna', 8)

window = Tk()
window.title("NOAA RSD Lidar QAQC Checks")
window.geometry('300x600')

section_rows = {
    'metadata': 0,
    'files': 1,
    'dirs': 2,
    'checks': 3,
    }

##################################################################### 
'''Metadata'''

meta_frame = Frame(window)
meta_frame.grid(row=section_rows['metadata'], sticky=NSEW)

label = Label(meta_frame, text='Populate Metadata', font=LARGE_FONT_BOLD)
label.grid(row=0, columnspan=3, pady=(10, 0), sticky=W)

check_label = Label(files_frame, text=d)
check_label.grid(column=0, row=i, sticky=W)

lbl = Label(window, text="Project Name")
lbl.grid(column=0, row=0)



#####################################################################
'''Files'''

files_frame = Frame(window)
files_frame.grid(row=section_rows['files'], sticky=NSEW)

label = Label(files_frame, text='Select Files', font=LARGE_FONT_BOLD)
label.grid(row=0, columnspan=3, pady=(10, 0), sticky=W)

def get_file():
    return tkFileDialog.askopenfilename()

def file0_clicked():
    files_to_set['qaqc'][0].configure(text=get_file())
def file1_clicked():
    files_to_set['las_tiles'][0].configure(text=get_file())


files_to_set = {
    'qaqc': [None, file0_clicked],
    'las_tiles': [None, file1_clicked],
    }

for i, d in enumerate(files_to_set, 1):
    check_label = Label(files_frame, text=d)
    check_label.grid(column=0, row=i, sticky=W)

    btn = Button(files_frame, text="...", command=files_to_set[d][1])
    btn.grid(column=1, row=i, sticky=W)

    files_to_set[d][0] = Label(files_frame, text="(Select File)")
    files_to_set[d][0].grid(column=2, row=i, sticky=W)

#####################################################################
'''Directories'''

dirs_frame = Frame(window)
dirs_frame.grid(row=section_rows['dirs'], sticky=NSEW)

label = Label(dirs_frame, text='Select Directories', font=LARGE_FONT_BOLD)
label.grid(row=0, columnspan=3, pady=(10, 0), sticky=W)

def get_dir():
    return tkFileDialog.askdirectory()

def dir0_clicked():
    dirs_to_set['qaqc'][0].configure(text=get_dir())
def dir1_clicked():
    dirs_to_set['las_tiles'][0].configure(text=get_dir())
def dir2_clicked():
    dirs_to_set['qaqc_gdb'][0].configure(text=get_dir())
def dir3_clicked():
    dirs_to_set['contractor_tiles_shp'][0].configure(text=get_dir())

dirs_to_set = {
    'qaqc': [None, dir0_clicked],
    'las_tiles': [None, dir1_clicked],
    'qaqc_gdb': [None, dir2_clicked],
    'contractor_tiles_shp': [None, dir3_clicked],
    }

for i, d in enumerate(dirs_to_set, 1):
    check_label = Label(dirs_frame, text=d)
    check_label.grid(column=0, row=i, sticky=W)

    btn = Button(dirs_frame, text="...", command=dirs_to_set[d][1])
    btn.grid(column=1, row=i, sticky=W)

    dirs_to_set[d][0] = Label(dirs_frame, text="(Select Directory)")
    dirs_to_set[d][0].grid(column=2, row=i, sticky=W)


#####################################################################
'''Checks'''

checks_frame = Frame(window)
checks_frame.grid(row=section_rows['checks'], sticky=NSEW)

label = Label(checks_frame, text='Select Checks', font=LARGE_FONT_BOLD)
label.grid(row=0, columnspan=3, pady=(10, 0), sticky=W)

checks_to_do = {
    'naming_convention': None,
    'version': None,
    'pdrf': None,
    'gps_time_type': None,
    'hor_datum': None,
    'ver_datum': None,
    'point_source_ids': None,
    'unexpected_classes': None,
    'create_dz': None,
    }

for i, c in enumerate(checks_to_do, 1):
    checks_to_do[c] = BooleanVar()
    checks_to_do[c].set(True)
    chk = Checkbutton(checks_frame, text=c, var=checks_to_do[c], 
                      anchor=W, justify=LEFT)
    chk.grid(column=0, row=i, sticky=W)
 

window.mainloop()
