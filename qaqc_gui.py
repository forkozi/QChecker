from qaqc import run_qaqc
import Tkinter as tk
import Tkconstants, tkFileDialog
import ttk
import os
import time
import json
import pandas as pd


LARGE_FONT = ('Verdanna', 12)
LARGE_FONT_BOLD = ('Verdanna', 12, 'bold')
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')
SMALL_FONT = ('Verdanna', 8)


class QaqcApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.config_file = 'Z:\qaqc\qaqc_config.json'
        self.load_config()
        self.set_gui_components()

        # show splash screen
        self.withdraw()
        splash = Splash(self)

        tk.Tk.wm_title(self, 'QAQC Checker')
        tk.Tk.iconbitmap(self, 'qaqc.ico')

        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save settings',
                             command=lambda: self.save_config())
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=quit)
        menubar.add_cascade(label='File', menu=filemenu)

        exchangeChoice = tk.Menu(menubar, tearoff=0)
        exchangeChoice.add_command(label='About', command=self.show_about)
        menubar.add_cascade(label='Help', menu=exchangeChoice)

        tk.Tk.config(self, menu=menubar)

        self.frames = {}
        for F in (MainGuiPage,):  # makes it easy to add "pages" in future
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(MainGuiPage)

        # after splash screen, show main GUI
        time.sleep(1)
        splash.destroy()
        self.deiconify()

    def set_gui_components(self):
        # set GUI section options
        self.components = {}
        

        self.components.update({'metadata': {
            'project_name': ['Project Name', None],
            'hor_datum': ['Horizontal Datum', None],
            'tile_size': ['Tile Size (m)', None],
            'expected_classes': ['Expected Classes (comma sep.)', None],
            }})

        self.components.update({'files_to_set': {
            'contractor_shp': ['Contractor Tile Shapefile', None, 
                               self.configuration['contractor_shp'], '.shp'],
            'dz_classes_template': ['Dz Classes Template', None, 
                                    self.configuration['dz_classes_template'], '.lyr'],
            'dz_export_settings': ['Dz Export Settings', None, 
                                   self.configuration['dz_export_settings'], '.xml'],
            'dz_mxd': ['QAQC ArcGIS Map', None, 
                       self.configuration['dz_mxd'], '.mxd'],
            }})

        self.components.update({'dirs_to_set': {
            'qaqc_dir': ['QAQC Home', None, 
                         self.configuration['qaqc_dir']],
            'qaqc_gdb': ['QAQC GeoDatabase', None, 
                         self.configuration['qaqc_gdb']],
            'las_tile_dir': ['Las Tiles', None, 
                             self.configuration['las_tile_dir']],
            'dz_binary_dir': ['Dz Surfaces', None, 
                              self.configuration['dz_binary_dir']],
            }})

        self.components.update({'checks_to_do': {
            'naming_convention': ['Naming Convention', None],
            'version': ['Version', None],
            'pdrf': ['Point Data Record Format (PDRF)', None],
            'gps_time_type': ['GPS Time Type', None],
            'hor_datum': ['Horizontal Datum', None],
            'ver_datum': ['Vertical Datum', None],
            'point_source_ids': ['Point Source IDs (Flight Line #)', None],
            'unexpected_classes': ['Unexpected Classes', None],
            }})

        self.components.update({'surfaces_to_make': {
            'dz': ['Dz', None],
            'hillshade': ['Hillshade', None],
            }})

        self.components.update({'mosaics_to_make': {
            'dz': ['Dz', None],
            'hillshade': ['Hillshade', None],
            }})

    def load_config(self):
        if os.path.isfile(self.config_file):
            with open(self.config_file) as cf:
                self.configuration = json.load(cf)
        else:
           print("configuration file doesn't exist")

    def save_config(self):

        # metadata
        for k, v in self.components['metadata'].iteritems():
            self.configuration[k] = v[1].get()
            
        # files_to_set
        for k, v in self.components['files_to_set'].iteritems():
            self.configuration[k] = v[2]

        # dirs_to_set
        for k, v in self.components['dirs_to_set'].iteritems():
            self.configuration[k] = v[2]

        # checks_to_do
        for k, v in self.components['checks_to_do'].iteritems():
            self.configuration['checks_to_do'][k] = v[1].get()

        # surfaces_to_make
        for k, v in self.components['surfaces_to_make'].iteritems():
            self.configuration['surfaces_to_make'][k] = v[1].get()

        # mosaics_to_make
        for k, v in self.components['mosaics_to_make'].iteritems():
            self.configuration['mosaics_to_make'][k] = v[1].get()

        config = 'Z:\qaqc\qaqc_config.json'
        print('saving {}...\n{}'.format(config, self.configuration))
        with open(config, 'w') as f:
            json.dump(self.configuration, f)

    @staticmethod
    def show_about():
        about = tk.Toplevel()
        tk.Toplevel.iconbitmap(about, 'qaqc.ico')
        about.wm_title('About QAQC Checker')
        splash_img = tk.PhotoImage(file='qaqc.gif')
        label = tk.Label(about, image=splash_img)
        label.pack()
        b1 = ttk.Button(about, text='Ok', command=about.destroy)
        b1.pack()
        about.mainloop()

    @staticmethod
    def popupmsg(msg):
        popup = tk.Tk()
        popup.wm_title('!')
        label = ttk.Label(popup, text=msg, font=NORM_FONT)
        label.pack(side='top', fill='x', pady=10)
        b1 = ttk.Button(popup, text='Ok', command=popup.destroy)
        b1.pack()
        popup.mainloop()

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class Splash(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        splash_img = tk.PhotoImage(file='Z:\qaqc\qaqc.gif', master=self)
        label = tk.Label(self, image=splash_img)
        label.pack()
        self.update()


class MainGuiPage(ttk.Frame):

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.parent = parent  # container made in QaqcApp
        self.configuration = controller.configuration  # from QaqcApp
        self.components = controller.components  # from QaqcApp
       
        self.section_rows = {
            'metadata': 0,
            'files': 1,
            'dirs': 2,
            'checks': 3,
            'surfaces': 4,
            'run_button': 5,
            }

        #  Build the GUI
        self.control_panel_width = 30
        self.build_gui()

    @staticmethod
    def build_display_str(str):
        str = str.replace('/', '\\')
        return r'...\{}'.format(str.split('\\')[-1])

    def build_gui(self):

        self.build_metadata()
        self.build_files()
        self.build_dirs()
        self.build_checks()
        self.build_surfaces()
        self.build_run_button()
                    
    def build_metadata(self):
        '''Metadata'''

        meta_frame = ttk.Frame(self)
        meta_frame.grid(row=self.section_rows['metadata'], sticky=tk.NSEW)

        label = tk.Label(meta_frame, text='Populate Metadata', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def get_wkt_ids():
            wkts_file = 'Z:\qaqc\wkts_NAD83_2011_UTM.csv'
            wkts_df = pd.read_csv(wkts_file)
            wkt_ids = wkts_df.iloc[:, 1]
            return tuple(wkt_ids)

        def get_proj_names():
            with open('Z:\qaqc\project_list.txt', 'r') as f:
               project_ids = [s.strip() for s in f.readlines()]
            return tuple(project_ids)

        item = 'project_name'
        row = 1
        meta_label = tk.Label(meta_frame, text=self.components['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.components['metadata'][item][1] = tk.StringVar()
        self.components['metadata'][item][1].set(self.configuration[item])
        proj_down_down = tk.OptionMenu(meta_frame, self.components['metadata'][item][1], *get_proj_names())
        proj_down_down.grid(column=1, row=row, sticky=tk.EW)

        item = 'hor_datum'
        row = 2
        meta_label = tk.Label(meta_frame, text=self.components['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.components['metadata'][item][1] = tk.StringVar()
        self.components['metadata'][item][1].set(self.configuration[item])
        wkt_ids_drop_down = tk.OptionMenu(meta_frame, self.components['metadata'][item][1], *get_wkt_ids())
        wkt_ids_drop_down.grid(column=1, row=row, sticky=tk.EW)

        item = 'expected_classes'
        row = 3
        meta_label = tk.Label(meta_frame, text=self.components['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.components['metadata'][item][1] = tk.StringVar(meta_frame, value=self.configuration[item])
        self.components['metadata'][item][1] = tk.Entry(meta_frame, textvariable=self.components['metadata'][item][1], width=30)
        self.components['metadata'][item][1].grid(column=1, row=row, sticky=tk.EW)

        item = 'tile_size'
        row = 4
        meta_label = tk.Label(meta_frame, text=self.components['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.components['metadata'][item][1] = tk.StringVar(meta_frame, value=self.configuration[item])
        self.components['metadata'][item][1] = tk.Entry(meta_frame, textvariable=self.components['metadata'][item][1], width=5)
        self.components['metadata'][item][1].grid(column=1, row=row, sticky=tk.EW)

    def build_files(self):
        '''Files'''

        files_frame = ttk.Frame(self)
        files_frame.grid(row=self.section_rows['files'], sticky=tk.NSEW)

        label = tk.Label(files_frame, text='Select Files', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def bind_files_command(f):
            def func():
                file_str = tkFileDialog.askopenfilename()
                display_str = self.build_display_str(file_str)
                self.components['files_to_set'][f][1].configure(text=display_str)
                self.components['files_to_set'][f][2] = file_str 
            func.__name__ = f
            return func

        for i, f in enumerate(self.components['files_to_set'], 1):
            check_label = tk.Label(files_frame, text=self.components['files_to_set'][f][0])
            check_label.grid(column=0, row=i, sticky=tk.W)

            display_str = self.build_display_str(self.configuration[f])
            self.components['files_to_set'][f][1] = tk.Label(files_frame, text=display_str)
            self.components['files_to_set'][f][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(files_frame, text="...", command=bind_files_command(f))
            btn.grid(column=1, row=i, sticky=tk.W)

    def build_dirs(self):
        '''Directories'''

        dirs_frame = ttk.Frame(self)
        dirs_frame.grid(row=self.section_rows['dirs'], sticky=tk.NSEW)

        label = tk.Label(dirs_frame, text='Select Directories', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def bind_dirs_command(d):
            def func():
                dir_str = tkFileDialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.components['dirs_to_set'][d][1].configure(text=display_str)
                self.components['dirs_to_set'][d][2] = dir_str 
            func.__name__ = d
            return func

        for i, d in enumerate(self.components['dirs_to_set'], 1):
            check_label = tk.Label(dirs_frame, text=self.components['dirs_to_set'][d][0])
            check_label.grid(column=0, row=i, sticky=tk.W)
            
            display_str = self.build_display_str(self.configuration[d])
            self.components['dirs_to_set'][d][1] = tk.Label(dirs_frame, text=display_str)
            self.components['dirs_to_set'][d][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(dirs_frame, text="...", command=bind_dirs_command(d))
            btn.grid(column=1, row=i, sticky=tk.W)

    def build_checks(self):
        '''Checks'''

        checks_frame = ttk.Frame(self)
        checks_frame.grid(row=self.section_rows['checks'], sticky=tk.NSEW)

        label = tk.Label(checks_frame, text='Select Checks', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        for i, c in enumerate(self.components['checks_to_do'], 1):
            self.components['checks_to_do'][c][1] = tk.BooleanVar()
            is_checked = self.configuration['checks_to_do'][c]
            self.components['checks_to_do'][c][1].set(is_checked)
            chk = tk.Checkbutton(
                checks_frame, 
                text=self.components['checks_to_do'][c][0],
                var=self.components['checks_to_do'][c][1], 
                anchor=tk.W, justify=tk.LEFT)
            chk.grid(column=0, row=i, sticky=tk.W)

    def build_surfaces(self):
        '''Surfaces'''

        surf_frame = ttk.Frame(self)
        surf_frame.grid(row=self.section_rows['surfaces'], sticky=tk.NSEW)

        label = tk.Label(surf_frame, text='Select Surfaces', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        for i, s in enumerate(self.components['surfaces_to_make'], 1):
            self.components['surfaces_to_make'][s][1] = tk.BooleanVar()
            is_checked = self.configuration['surfaces_to_make'][s]
            self.components['surfaces_to_make'][s][1].set(is_checked)
            chk = tk.Checkbutton(
                surf_frame, 
                text=self.components['surfaces_to_make'][s][0], 
                var=self.components['surfaces_to_make'][s][1], 
                anchor=tk.W, justify=tk.LEFT)
            chk.grid(column=0, row=i, sticky=tk.W)

    def build_run_button(self):

        run_frame = ttk.Frame(self)
        run_frame.grid(row=self.section_rows['run_button'], sticky=tk.NSEW, pady=(10, 0))

        btn = tk.Button(run_frame, text="Run QAQC Processes", 
             command=self.run_qaqc_process, height=2)
        btn.grid(column=0, row=0, sticky=tk.EW, padx=(120, 0))

    def verify_input():
        pass

    def run_qaqc_process(self):
        pass
        #verify_input()
        run_qaqc() #  from qaqc.py
    

if __name__ == "__main__":
    app = QaqcApp()
    app.geometry('400x850')
    app.mainloop()  # tk functionality
