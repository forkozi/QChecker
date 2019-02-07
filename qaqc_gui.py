from qaqc import run_qaqc
import Tkinter as tk
import Tkconstants, tkFileDialog
import ttk
import os
import time
import json
import pandas as pd
import matplotlib

matplotlib.use('Agg')

LARGE_FONT = ('Verdanna', 12)
LARGE_FONT_BOLD = ('Verdanna', 12, 'bold')
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')
NORM_FONT_ITALIC = ('Verdanna', 10, 'italic')


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
            'tile_size': ['Tile Size (m)', None],
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
            }})

        self.components.update({'checks_to_do': {
            'naming_convention': ['Naming Convention', None],
            'version': ['Version', None],
            'pdrf': ['Point Data Record Format', None],
            'gps_time_type': ['GPS Time Type', None],
            'hor_datum': ['Horizontal Datum', None],
            'ver_datum': ['Vertical Datum', None],
            'point_source_ids': ['Point Source IDs', None],
            'expected_classes': ['Expected Classes', None],
            }})

        self.components.update({'surfaces_to_make': {
            'Dz': ['Dz', None, None, self.configuration['surfaces_to_make']['Dz'][1]],
            'Hillshade': ['Hillshade', None, None, self.configuration['surfaces_to_make']['Hillshade'][1]],
            }})

        self.components.update({'mosaics_to_make': {
            'Dz': ['Dz Mosaic', None, None, self.configuration['mosaics_to_make']['Dz'][1]],
            'Hillshade': ['Hillshade Mosaic', None, None, self.configuration['mosaics_to_make']['Hillshade'][1]],
            }})

        self.components.update({'checks_keys': {
            'naming_convention': [None, None],
            'version': [None, None],
            'pdrf': [None, None],
            'gps_time_type': [None, None],
            'hor_datum': [None, None],
            'ver_datum': [None, None],
            'point_source_ids': [None, None],
            'expected_classes': [None, None],        
            }})

        self.components.update({'supp_las_domain': None})

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

        # checks_keys
        for k, v in self.components['checks_keys'].iteritems():
            self.configuration['checks_keys'][k] = v[0].get()

        # surfaces_to_make
        for k, v in self.components['surfaces_to_make'].iteritems():
            self.configuration['surfaces_to_make'][k][0] = v[1].get()
            self.configuration['surfaces_to_make'][k][1] = v[3]

        # mosaics_to_make
        for k, v in self.components['mosaics_to_make'].iteritems():
            self.configuration['mosaics_to_make'][k][0] = v[1].get()
            self.configuration['mosaics_to_make'][k][1] = v[3]

        # supp_las_domain
        self.configuration['supp_las_domain'] = self.components['supp_las_domain'].get()

        config = 'Z:\qaqc\qaqc_config.json'
        print('saving {}...\n{}'.format(config, self.configuration))
        with open(config, 'w') as f:
            json.dump(self.configuration, f)

    @staticmethod
    def show_about():
        about = tk.Toplevel()
        tk.Toplevel.iconbitmap(about, 'qaqc.ico')
        about.wm_title('About QAQC Checker')
        splash_img = tk.PhotoImage(file='Z:\qaqc\SplashScreen.gif')
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
        splash_img = tk.PhotoImage(file='Z:\qaqc\SplashScreen.gif', master=self)
        label = tk.Label(self, image=splash_img)
        label.pack()
        self.update()


class MainGuiPage(ttk.Frame):

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.parent = parent  # container made in QaqcApp
        self.config = controller.configuration  # from QaqcApp
        self.gui = controller.components  # from QaqcApp
        self.las_classes_file = 'Z:\qaqc\las_classes.json'

       
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
        print(str)
        str = str.replace('/', '\\')
        return r'...\{}'.format(os.path.join(*str.split('\\')[-1:]))

    def get_checked_classes(self, popup, vars):
        checked_classes = []
        for k, v in vars.iteritems():
            if v.get():
                checked_classes.append(k)
        print checked_classes
        self.gui['checks_keys']['expected_classes'][0].set(','.join(checked_classes))
        popup.destroy()

    def get_class_status(self, c):
        if c in self.gui['checks_keys']['expected_classes'][0].get().split(','):
            return True
        else:
            return False

    def pick_classes(self):

        with open(self.las_classes_file) as cf:
            las_classes = json.load(cf)

        las_version = self.gui['checks_keys']['version'][0].get()

        def get_domains():
            domains = las_classes[las_version]['supplemental'].keys()
            return tuple(domains)

        popup = tk.Toplevel()
        popup.wm_title('Pick Expected Classes')
        vars = {}

        label = tk.Label(popup, text='LAS {} Classes'.format(las_version), font=NORM_FONT_BOLD)
        label.pack(side='top', fill='x', pady=(0, 0))
        
        # core Las spec classes
        for k, v in sorted(las_classes[las_version]['classes'].iteritems()):
            vars.update({k: tk.BooleanVar()})
            vars[k].set(self.get_class_status(k))
            class_check = tk.Checkbutton(popup, text='{}: {}'.format(k, v), 
                                         var=vars[k], anchor=tk.W, 
                                         justify=tk.LEFT, width=40)
            class_check.pack(side='top', fill='x', pady=(0, 0))


        # supplemental Las classes
        label = tk.Label(popup, text='Supplemental {} Classes'.format(las_version), font=NORM_FONT_BOLD)
        label.pack(side='top', fill='x', pady=(0, 0))

        supp_classes_domain = tk.OptionMenu(popup, self.gui['supp_las_domain'], *get_domains())
        supp_classes_domain.pack(side='top', fill='x', pady=(0, 0))

        for k, v in sorted(las_classes[las_version]['supplemental'][self.gui['supp_las_domain'].get()]['classes'].iteritems()):
            vars.update({k: tk.BooleanVar()})
            vars[k].set(self.get_class_status(k))
            class_check = tk.Checkbutton(popup, text='{}: {}'.format(k, v), 
                                         var=vars[k], anchor=tk.W, 
                                         justify=tk.LEFT, width=40)
            class_check.pack(side='top', fill='x', pady=(0, 0))


        b1 = tk.Button(popup, text='Ok', command=lambda: self.get_checked_classes(popup, vars))
        b1.pack(side='top', fill='x', pady=(0, 0))
        popup.mainloop()

    def build_gui(self):
        self.build_metadata()
        self.build_files()
        self.build_dirs()
        self.add_checks()
        self.add_surfaces()
        self.add_run_button()                 

    def build_metadata(self):
        '''Metadata'''

        meta_frame = ttk.Frame(self)
        meta_frame.grid(row=self.section_rows['metadata'], sticky=tk.NSEW)

        label = tk.Label(meta_frame, text='Metadata', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def get_proj_names():
            with open('Z:\qaqc\project_list.txt', 'r') as f:
               project_ids = [s.strip() for s in f.readlines()]
            return tuple(project_ids)

        item = 'project_name'
        row = 1
        meta_label = tk.Label(meta_frame, text=self.gui['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.gui['metadata'][item][1] = tk.StringVar()
        self.gui['metadata'][item][1].set(self.config[item])
        proj_down_down = tk.OptionMenu(meta_frame, self.gui['metadata'][item][1], *get_proj_names())
        proj_down_down.grid(column=1, row=row, sticky=tk.EW)

        item = 'tile_size'
        row = 2
        meta_label = tk.Label(meta_frame, text=self.gui['metadata'][item][0])
        meta_label.grid(column=0, row=row, sticky=tk.W)
        self.gui['metadata'][item][1] = tk.StringVar(meta_frame, value=self.config[item])
        self.gui['metadata'][item][1] = tk.Entry(
            meta_frame, 
            textvariable=self.gui['metadata'][item][1], 
             state='disabled', 
            width=5)
        self.gui['metadata'][item][1].grid(column=1, row=row, sticky=tk.EW)

    def build_files(self):
        '''Files'''

        files_frame = ttk.Frame(self)
        files_frame.grid(row=self.section_rows['files'], sticky=tk.NSEW)

        label = tk.Label(files_frame, text='Files', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def bind_files_command(f):
            def func():
                file_str = tkFileDialog.askopenfilename()
                display_str = self.build_display_str(file_str)
                self.gui['files_to_set'][f][1].configure(text=display_str)
                self.gui['files_to_set'][f][2] = file_str 
            func.__name__ = f
            return func

        for i, f in enumerate(self.gui['files_to_set'], 1):
            check_label = tk.Label(files_frame, text=self.gui['files_to_set'][f][0])
            check_label.grid(column=0, row=i, sticky=tk.W)

            display_str = self.build_display_str(self.config[f])
            self.gui['files_to_set'][f][1] = tk.Label(files_frame, text=display_str)
            self.gui['files_to_set'][f][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(files_frame, text="...", command=bind_files_command(f))
            btn.grid(column=1, row=i, sticky=tk.W)

    def build_dirs(self):
        '''Directories'''

        dirs_frame = ttk.Frame(self)
        dirs_frame.grid(row=self.section_rows['dirs'], sticky=tk.NSEW)

        label = tk.Label(dirs_frame, text='Directories', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def bind_dirs_command(d):
            def func():
                dir_str = tkFileDialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.gui['dirs_to_set'][d][1].configure(text=display_str)
                self.gui['dirs_to_set'][d][2] = dir_str 
            func.__name__ = d
            return func

        for i, d in enumerate(self.gui['dirs_to_set'], 1):
            dir_label = tk.Label(dirs_frame, text=self.gui['dirs_to_set'][d][0])
            dir_label.grid(column=0, row=i, sticky=tk.W)
            
            display_str = self.build_display_str(self.config[d])
            self.gui['dirs_to_set'][d][1] = tk.Label(dirs_frame, text=display_str)
            self.gui['dirs_to_set'][d][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(dirs_frame, text="...", command=bind_dirs_command(d))
            btn.grid(column=1, row=i, sticky=tk.W)

    @staticmethod
    def get_wkt_ids():
        wkts_file = 'Z:\qaqc\wkts_NAD83_2011_UTM.csv'
        wkts_df = pd.read_csv(wkts_file)
        wkt_ids = wkts_df.iloc[:, 1]
        return tuple(wkt_ids)

    @staticmethod
    def get_gps_time_types():
        return ('Satellite GPS Time', 'GPS Week Seconds')  # TODO: verify names

    @staticmethod
    def get_versions():
        return ('1.2', '1.4')

    @staticmethod
    def get_ver_datums():
        return ('MHW', 'MLLW', 'GRS80', 'WGS84')

    def update_version_affected_info(self):
        version = self.gui['checks_keys']['version'][0].get()
        if version == '1.2':
            pdrf = '3'
            exp_classes = '02,26'
            supp_las_domain = 'RSD Supplemental Classes'
        elif version == '1.4':
            pdrf = '6'
            exp_classes = '02,40'
            supp_las_domain = 'Topo-Bathy Lidar Domain Profile'
        else:
            pdrf = None
                    
        self.gui['checks_keys']['pdrf'][0].set(pdrf)
        self.gui['checks_keys']['expected_classes'][0].set(exp_classes)
        self.gui['supp_las_domain'].set(supp_las_domain)

    def add_checks(self):

        def add_naming_convention_key():
            # naming_convention
            self.gui['checks_keys']['naming_convention'][0] = tk.StringVar()
            self.gui['checks_keys']['naming_convention'][0].set(
                self.config['checks_keys']['naming_convention'])
            self.gui['checks_keys']['naming_convention'][1] = tk.Entry(
                checks_frame, 
                state='disabled', 
                textvariable=self.gui['checks_keys']['naming_convention'][0], width=30)

        def add_version_key():
            self.gui['checks_keys']['version'][0] = tk.StringVar()
            self.gui['checks_keys']['version'][0].set(
                self.config['checks_keys']['version'])
            self.gui['checks_keys']['version'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['checks_keys']['version'][0], 
                *self.get_versions(), 
                command=lambda x: self.update_version_affected_info())
            self.gui['checks_keys']['version'][1].configure(anchor='w')

        def add_pdrf_key():
            # pdrf
            self.gui['checks_keys']['pdrf'][0] = tk.StringVar()
            self.gui['checks_keys']['pdrf'][0].set(
                self.config['checks_keys']['pdrf'])
            self.gui['checks_keys']['pdrf'][1] = tk.Entry(
                checks_frame, 
                state='disabled', 
                textvariable=self.gui['checks_keys']['pdrf'][0], width=30)

        def add_gps_time_type_key():
            # gps_time_type
            self.gui['checks_keys']['gps_time_type'][0] = tk.StringVar()
            self.gui['checks_keys']['gps_time_type'][0].set(
                self.config['checks_keys']['gps_time_type'])
            self.gui['checks_keys']['gps_time_type'][1] = tk.OptionMenu(
                checks_frame,
                self.gui['checks_keys']['gps_time_type'][0], 
                *self.get_gps_time_types())
            self.gui['checks_keys']['gps_time_type'][1].config(state='disabled')
            self.gui['checks_keys']['gps_time_type'][1].configure(anchor='w')

        def add_hor_datum_key():
            # hor_datum
            self.gui['checks_keys']['hor_datum'][0] = tk.StringVar()
            self.gui['checks_keys']['hor_datum'][0].set(
                self.config['checks_keys']['hor_datum'])
            self.gui['checks_keys']['hor_datum'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['checks_keys']['hor_datum'][0], 
                *self.get_wkt_ids())
            self.gui['checks_keys']['hor_datum'][1].configure(anchor='w')

        def add_ver_datum_key():
            # ver_datum
            self.gui['checks_keys']['ver_datum'][0] = tk.StringVar()
            self.gui['checks_keys']['ver_datum'][0].set(
                self.config['checks_keys']['ver_datum'])
            self.gui['checks_keys']['ver_datum'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['checks_keys']['ver_datum'][0], 
                *self.get_ver_datums())
            self.gui['checks_keys']['ver_datum'][1].configure(anchor='w')
            self.gui['checks_keys']['ver_datum'][1].config(state='disabled')

        def add_point_source_ids_key():
            # point_source_ids
            self.gui['checks_keys']['point_source_ids'][0] = tk.StringVar()
            self.gui['checks_keys']['point_source_ids'][0].set(
                self.config['checks_keys']['point_source_ids'])
            self.gui['checks_keys']['point_source_ids'][1] = tk.Entry(
                checks_frame, 
                state='disabled', 
                textvariable=self.gui['checks_keys']['point_source_ids'][0], width=30)

        def add_expected_classes_key():
            # unexpected_classes
            self.gui['checks_keys']['expected_classes'][0] = tk.StringVar()
            self.gui['checks_keys']['expected_classes'][0].set(
                self.config['checks_keys']['expected_classes'])
            self.gui['checks_keys']['expected_classes'][1] = tk.Button(
                checks_frame,
                textvariable=self.gui['checks_keys']['expected_classes'][0],
                command=self.pick_classes,
                justify=tk.LEFT, anchor=tk.W)

        def add_supp_las_domain():
            self.gui['supp_las_domain'] = tk.StringVar()
            self.gui['supp_las_domain'].set(self.config['supp_las_domain'])

        '''Checks'''
        checks_frame = ttk.Frame(self)
        checks_frame.grid(row=self.section_rows['checks'], sticky=tk.NSEW)

        label = tk.Label(checks_frame, text='Checks', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        add_naming_convention_key()
        add_version_key()
        add_pdrf_key()
        add_gps_time_type_key()
        add_hor_datum_key()
        add_ver_datum_key()
        add_point_source_ids_key()
        add_expected_classes_key()
        add_supp_las_domain()

        for i, c in enumerate(self.gui['checks_to_do'], 1):
            self.gui['checks_to_do'][c][1] = tk.BooleanVar()
            is_checked = self.config['checks_to_do'][c]
            self.gui['checks_to_do'][c][1].set(is_checked)
            chk = tk.Checkbutton(
                checks_frame, 
                text=self.gui['checks_to_do'][c][0],
                var=self.gui['checks_to_do'][c][1], 
                anchor=tk.W, justify=tk.LEFT)
            chk.grid(column=0, row=i, sticky=tk.W)
            self.gui['checks_keys'][c][1].grid(column=1, row=i, sticky=tk.EW)


    def add_surfaces(self):
        
        def bind_dirs_command(s):
            def func():
                dir_str = tkFileDialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.gui['surfaces_to_make'][s][2].configure(text=display_str)
                self.gui['surfaces_to_make'][s][3] = dir_str 
            func.__name__ = s
            return func

        def bind_file_command(s):
            def func():
                file_str = tkFileDialog.askopenfilename()
                display_str = self.build_display_str(file_str)
                self.gui['mosaics_to_make'][s][2].configure(text=display_str)
                self.gui['mosaics_to_make'][s][3] = file_str 
            func.__name__ = s
            return func

        def add_tile_surface():
            # checkbox
            self.gui['surfaces_to_make'][s][1] = tk.BooleanVar()
            is_checked = self.config['surfaces_to_make'][s][0]
            self.gui['surfaces_to_make'][s][1].set(is_checked)
            chk = tk.Checkbutton(
                subframe, 
                text=self.gui['surfaces_to_make'][s][0], 
                var=self.gui['surfaces_to_make'][s][1], 
                anchor=tk.W, justify=tk.LEFT, width=13)
            chk.grid(column=0, row=0, sticky=tk.EW)

            # Directory
            surface_label = tk.Label(subframe, text='Diretory'.format(s))
            surface_label.grid(column=1, row=0, sticky=tk.EW, padx=(20, 0))

            btn = tk.Button(subframe, text="...", command=bind_dirs_command(s))
            btn.grid(column=2, row=0, sticky=tk.EW)

            display_str = self.build_display_str(self.config['surfaces_to_make'][s][1])
            self.gui['surfaces_to_make'][s][2] = tk.Label(
                subframe, text=display_str, width=22, justify=tk.LEFT, anchor=tk.W)
            self.gui['surfaces_to_make'][s][2].grid(column=3, row=0, sticky=tk.EW)

        def add_mosaic_surface():
            # checkbox
            self.gui['mosaics_to_make'][s][1] = tk.BooleanVar()
            is_checked = self.config['mosaics_to_make'][s][0]
            self.gui['mosaics_to_make'][s][1].set(is_checked)
            chk = tk.Checkbutton(
                subframe, 
                text=self.gui['mosaics_to_make'][s][0], 
                var=self.gui['mosaics_to_make'][s][1], 
                anchor=tk.W, justify=tk.LEFT, width=13)
            chk.grid(column=0, row=1, sticky=tk.EW)

            # Path
            surface_label = tk.Label(subframe, text='Path'.format(s))
            surface_label.grid(column=1, row=1, sticky=tk.EW, padx=(20, 0))

            btn = tk.Button(subframe, text="...", command=bind_file_command(s))
            btn.grid(column=2, row=1, sticky=tk.EW)

            display_str = self.build_display_str(self.config['mosaics_to_make'][s][1])
            self.gui['mosaics_to_make'][s][2] = tk.Label(
                subframe, text=display_str, width=22, justify=tk.LEFT, anchor=tk.W)
            self.gui['mosaics_to_make'][s][2].grid(column=3, row=1, sticky=tk.EW)

        '''Surfaces'''
        surf_frame = ttk.Frame(self)
        surf_frame.grid(row=self.section_rows['surfaces'], sticky=tk.NSEW)

        label = tk.Label(surf_frame, text='Surfaces', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        for i, s in enumerate(self.gui['surfaces_to_make'], 1):
            subframe = ttk.Frame(surf_frame)
            subframe.grid(row=i, column=0, sticky=tk.EW)

            add_tile_surface()
            add_mosaic_surface()
            
            sep = ttk.Separator(subframe, orient=tk.HORIZONTAL)
            sep.grid(row=2, columnspan=4, padx=(10, 0), pady=(5, 5), sticky=tk.EW)
            
    def add_run_button(self):
        run_frame = ttk.Frame(self)
        run_frame.grid(row=self.section_rows['run_button'], sticky=tk.NSEW, pady=(10, 0))

        btn = tk.Button(run_frame, text="Run QAQC Processes", 
             command=self.run_qaqc_process, height=2)
        btn.grid(column=0, row=0, sticky=tk.EW, padx=(120, 0))

    def verify_input():
        pass

    def run_qaqc_process(self):
        #verify_input()
        run_qaqc() #  from qaqc.py
    

if __name__ == "__main__":
    app = QaqcApp()
    app.geometry('400x850')
    app.mainloop()  # tk functionality
