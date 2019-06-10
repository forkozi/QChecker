from qchecker import run_qaqc
import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
import time
import json
import pandas as pd
import logging


#matplotlib.use('Agg')

LARGE_FONT = ('Verdanna', 12)
LARGE_FONT_BOLD = ('Verdanna', 12, 'bold')
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')
NORM_FONT_ITALIC = ('Verdanna', 10, 'italic')


class QaqcApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.config_file = r'.\assets\config_files\qaqc_config.json'
        self.load_config()
        self.set_gui_components()

        # show splash screen
        self.withdraw()
        splash = Splash(self)

        version = 'v1.0.1-beta'
        tk.Tk.wm_title(self, 'Q-Checker {}'.format(version))
        tk.Tk.iconbitmap(self, r'.\assets\images\qaqc.ico')

        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Save settings', command=lambda: self.save_config())
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

        self.components.update({'options': {
            'project_name': ['Project', None],
            #'tile_size': ['Tile Size (m)', None],
            'to_pyramid': ['Build LAS Pyramids', None],
            #'make_contact_centroids': ['Make Contr. Tile Centroid shp', None],
            'multiprocess': ['Use Multiprocessing', None],  # hard-coded False for now
            }})

        self.components.update({'dirs_to_set': {
            'qaqc_dir': ['QAQC Root Dir.', None, Path(self.configuration['qaqc_dir'])],
            'las_tile_dir': ['Las Tiles', None, Path(self.configuration['las_tile_dir'])],
            }})

        self.components.update({'checks_to_do': {
            'naming': ['Naming Convention', None],
            'version': ['Version', None],
            'pdrf': ['Point Data Record Format', None],
            'gps_time': ['GPS Time Type', None],
            'hdatum': ['Horizontal Datum', None],
            'vdatum': ['Vertical Datum', None],
            'pt_src_ids': ['Point Source IDs', None],
            'exp_cls': ['Expected Classes', None],
            }})

        self.components.update({'surfaces_to_make': {
            'Dz': ['Dz', None, None, Path(self.configuration['surfaces_to_make']['Dz'][1])],
            'Hillshade': ['Hillshade', None, None, Path(self.configuration['surfaces_to_make']['Hillshade'][1])],
            }})

        self.components.update({'mosaics_to_make': {
            'Dz': ['Dz Mosaic', None, None, Path(self.configuration['mosaics_to_make']['Dz'][1])],
            'Hillshade': ['Hillshade Mosaic', None, None, Path(self.configuration['mosaics_to_make']['Dz'][1])],
            }})

        self.components.update({'check_keys': {
            'naming': [None, None],
            'version': [None, None],
            'pdrf': [None, None],
            'gps_time': [None, None],
            'hdatum': [None, None],
            'vdatum': [None, None],
            'pt_src_ids': [None, None],
            'exp_cls': [None, None],        
            }})

        self.components.update({'supp_las_domain': None})

    def load_config(self):
        if os.path.isfile(self.config_file):
            with open(self.config_file) as cf:
                self.configuration = json.load(cf)
        else:
           logging.debug('configuration file doesn\'t exist')

    def save_config(self):

        # options
        for k, v in self.components['options'].items():
            self.configuration[k] = v[1].get()

        # dirs_to_set
        for k, v in self.components['dirs_to_set'].items():
            self.configuration[k] = str(v[2])

        # checks_to_do
        for k, v in self.components['checks_to_do'].items():
            self.configuration['checks_to_do'][k] = v[1].get()

        # check_keys
        for k, v in self.components['check_keys'].items():
            self.configuration['check_keys'][k] = v[0].get()

        # surfaces_to_make
        for k, v in self.components['surfaces_to_make'].items():
            self.configuration['surfaces_to_make'][k][0] = v[1].get()
            self.configuration['surfaces_to_make'][k][1] = str(v[3])

        # mosaics_to_make
        for k, v in self.components['mosaics_to_make'].items():
            self.configuration['mosaics_to_make'][k][0] = v[1].get()
            self.configuration['mosaics_to_make'][k][1] = str(v[3])

        # supp_las_domain
        self.configuration['supp_las_domain'] = self.components['supp_las_domain'].get()

        logging.debug('saving {}...'.format(self.config_file))
        with open(self.config_file, 'w') as f:
            json.dump(self.configuration, f)

    @staticmethod
    def show_about():
        about = tk.Toplevel()
        tk.Toplevel.iconbitmap(about, 'qaqc.ico')
        about.wm_title('About Q-Checker')
        splash_img = tk.PhotoImage(file=r'.\assets\images\SplashScreen.gif')
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
        splash_img = tk.PhotoImage(file=r'.\assets\images\SplashScreen.gif', master=self)
        label = tk.Label(self, image=splash_img)
        label.pack()
        self.update()


class MainGuiPage(ttk.Frame):

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.parent = parent  # container made in QaqcApp
        self.controller = controller
        self.config = controller.configuration  # from QaqcApp
        self.gui = controller.components  # from QaqcApp
        self.las_classes_file = self.config['las_classes_json']

        self.section_rows = {
            'options': 0,
            'dirs': 1,
            'checks': 2,
            'surfaces': 3,
            'run_button': 4,
            }

        #  Build the GUI
        self.control_panel_width = 50
        self.label_width = 23

        self.build_options()
        self.build_dirs()
        self.add_checks()
        self.add_surfaces()
        self.add_run_panel()  

    @staticmethod
    def build_display_str(str):
        return r'...\{}'.format(Path(str).parts[-1])

    def get_checked_classes(self, popup, vars):
        checked_classes = []
        for k, v in vars.items():
            if v.get():
                checked_classes.append(k)
        self.gui['check_keys']['exp_cls'][0].set(','.join(checked_classes))
        popup.destroy()

    def get_class_status(self, c):
        if c in self.gui['check_keys']['exp_cls'][0].get().split(','):
            return True
        else:
            return False

    def pick_classes(self):
        def get_domains():
            domains = las_classes[las_version]['supplemental'].keys()
            return tuple(domains)

        def add_core_classes():
            label = tk.Label(core_classes_frame, 
                             text='LAS {} Classes'.format(las_version), 
                             font=NORM_FONT_BOLD)
            label.grid(row=0, sticky=tk.EW)
            core_classes = las_classes[las_version]['classes']
            for i, (k, v) in enumerate(sorted(core_classes.items()), 1):
                vars.update({k: tk.BooleanVar()})
                vars[k].set(self.get_class_status(k))
                class_check = tk.Checkbutton(core_classes_frame, text='{}: {}'.format(k, v), 
                                             var=vars[k], anchor=tk.W, 
                                             justify=tk.LEFT, width=40)
                class_check.grid(row=i, sticky=tk.EW)

        def add_domain_profile_selector():
            label = tk.Label(supp_classes_frame, 
                             text='Supplemental LAS {} Classes'.format(las_version), 
                             font=NORM_FONT_BOLD)
            label.grid(row=0, sticky=tk.EW)
            supp_classes_domain = tk.OptionMenu(supp_classes_frame, 
                                                self.gui['supp_las_domain'], 
                                                *get_domains(),
                                                command=lambda x: add_supp_classes())
            supp_classes_domain.grid(row=1, sticky=tk.EW)

        def add_supp_classes():
            avail_domains = las_classes[las_version]['supplemental']
            curr_domain_classes = avail_domains[self.gui['supp_las_domain'].get()]['classes']
            for i, (k, v) in enumerate(sorted(curr_domain_classes.items()), 2):
                vars.update({k: tk.BooleanVar()})
                vars[k].set(self.get_class_status(k))
                class_check = tk.Checkbutton(supp_classes_frame, 
                                             text='{}: {}'.format(k, v), 
                                             var=vars[k], anchor=tk.W, 
                                             justify=tk.LEFT, width=40)
                class_check.grid(row=i, sticky=tk.EW)

        with open(self.las_classes_file) as cf:
            las_classes = json.load(cf)

        self.gui['check_keys']['exp_cls'][0].set('picking classes...')

        las_version = self.gui['check_keys']['version'][0].get()

        popup = tk.Toplevel()
        popup.wm_title('Pick Expected Classes')
        vars = {}

        core_classes_frame = ttk.Frame(popup)
        core_classes_frame.grid(row=0, sticky=tk.EW)
        supp_classes_frame = ttk.Frame(popup)
        supp_classes_frame.grid(row=1, sticky=tk.EW)

        add_core_classes()
        add_domain_profile_selector()
        add_supp_classes()

        b1 = tk.Button(popup, text='Ok', command=lambda: self.get_checked_classes(popup, vars))
        b1.grid(row=2, sticky=tk.EW)
        
        # prevent user form opening multiple class-picker windows
        popup.transient(self)
        popup.grab_set()
        self.wait_window(popup)

    def add_progress_bar(self):
        popup = tk.Toplevel()
        popup.wm_title('QAQC Progress')

        progress_frame = ttk.Frame(popup)
        progress_frame.grid(row=0, sticky=tk.EW)
        
        # checks progress
        progress_label1a = tk.Label(progress_frame, text='Tiles', justify=tk.LEFT, anchor=tk.W)
        progress_label1a.grid(column=0, row=0, sticky=tk.EW)
        progress_bar1 = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=500, 
                                        value=0, maximum=100, mode='indeterminate') 
        progress_bar1.grid(column=1, row=0, sticky=tk.EW)
        progress_label1b = tk.Label(progress_frame, justify=tk.LEFT, anchor=tk.W)
        progress_label1b.grid(column=2, row=0, sticky=tk.EW)

        # surfaces progress
        progress_label2a = tk.Label(progress_frame, text='Mosaics', justify=tk.LEFT, anchor=tk.W)
        progress_label2a.grid(column=0, row=1, sticky=tk.EW)
        progress_bar2 = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=500, 
                                        value=0, maximum=100, mode='indeterminate') 
        progress_bar2.grid(column=1, row=1, sticky=tk.EW)
        progress_label2b = tk.Label(progress_frame, justify=tk.LEFT, anchor=tk.W)
        progress_label2b.grid(column=2, row=1, sticky=tk.EW)

        popup.update()

        progress = (progress_label1a, progress_bar1, progress_label1b, 
                    progress_label2a, progress_bar2, progress_label2b)

        return progress 

    def clear_paths(self):
        not_specified_text = '(specify path)'

        self.gui['dirs_to_set']['qaqc_dir'][1].configure(text=not_specified_text, fg='red')
        self.gui['dirs_to_set']['qaqc_dir'][2] = not_specified_text

        self.gui['dirs_to_set']['las_tile_dir'][1].configure(text=not_specified_text, fg='red')
        self.gui['dirs_to_set']['las_tile_dir'][2] = not_specified_text

        self.run_btn['state'] = 'disabled'

        self.controller.save_config()

    def check_paths(self):
        not_specified_text = '(specify path)'
        path1 = True if str(self.gui['dirs_to_set']['qaqc_dir'][2]) != not_specified_text else False
        path2 = True if str(self.gui['dirs_to_set']['las_tile_dir'][2]) != not_specified_text else False

        if path1 and path2:
            self.run_btn['state'] = 'normal'
        else:
            self.run_btn['state'] = 'disabled'

    def build_options(self):
        '''options'''

        options_frame = ttk.Frame(self)
        options_frame.grid(row=self.section_rows['options'], sticky=tk.NSEW)

        label = tk.Label(options_frame, text='SETTINGS', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def get_proj_names():
            #with open(self.config['project_list'], 'r') as f:
            #   project_ids = [s.strip() for s in f.readlines()]

            project_unc = r'\\ngs-s-rsd\Lidar_Contract00'
            project_ids = os.listdir(project_unc)

            return tuple(project_ids)

        # -----------------------------------------------------
        item = 'project_name'
        row = 1
        option_label = tk.Label(options_frame, 
                                text=self.gui['options'][item][0], 
                                width=self.label_width, 
                                anchor=tk.W, 
                                justify=tk.LEFT)

        option_label.grid(column=0, row=row, sticky=tk.W)
        self.gui['options'][item][1] = tk.StringVar()
        self.gui['options'][item][1].set(self.config[item])
        proj_down_down = tk.OptionMenu(options_frame, 
                                       self.gui['options'][item][1], 
                                       *get_proj_names(),
                                       command=lambda x: self.clear_paths())

        proj_down_down.grid(column=1, row=row, sticky=tk.EW)

        # -----------------------------------------------------
        item = 'to_pyramid'
        row = 3
        option_label = tk.Label(options_frame, 
                                text=self.gui['options'][item][0], 
                                width=self.label_width, 
                                anchor=tk.W, 
                                justify=tk.LEFT)

        option_label.grid(column=0, row=row, sticky=tk.W)
        self.gui['options'][item][1] = tk.BooleanVar()
        is_checked = self.config[item]
        self.gui['options'][item][1].set(is_checked)
        chk = tk.Checkbutton(
            options_frame, 
            text='',
            var=self.gui['options'][item][1], 
            anchor=tk.W, justify=tk.LEFT)
        chk.grid(column=1, row=row, sticky=tk.W)

        # -----------------------------------------------------
        item = 'multiprocess'
        row = 4
        option_label = tk.Label(options_frame, 
                                text=self.gui['options'][item][0], 
                                width=self.label_width, 
                                anchor=tk.W, 
                                justify=tk.LEFT)

        option_label.grid(column=0, row=row, sticky=tk.W)
        self.gui['options'][item][1] = tk.BooleanVar()
        is_checked = self.config[item]
        self.gui['options'][item][1].set(is_checked)
        chk = tk.Checkbutton(
            options_frame, 
            text='(deferred to future version)',
            var=self.gui['options'][item][1], 
            anchor=tk.W, justify=tk.LEFT, state='disabled')
        chk.grid(column=1, row=row, sticky=tk.W)

    def build_dirs(self):
        '''Directories'''

        dirs_frame = ttk.Frame(self)
        dirs_frame.grid(row=self.section_rows['dirs'], sticky=tk.NSEW)

        def bind_dirs_command(d):
            def func():
                dir_str = filedialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.gui['dirs_to_set'][d][1].configure(text=display_str, fg='black')
                self.gui['dirs_to_set'][d][2] = dir_str
                self.check_paths()
            func.__name__ = d
            return func

        for i, d in enumerate(self.gui['dirs_to_set'], 1):
            dir_label = tk.Label(dirs_frame, 
                                 text=self.gui['dirs_to_set'][d][0], 
                                 width=self.label_width, 
                                 anchor=tk.W, 
                                 justify=tk.LEFT)

            dir_label.grid(column=0, row=i, sticky=tk.W)
            
            if self.config[d] == '(specify path)':
                display_str = self.config[d]
                font_color = 'red'
            else:
                display_str = self.build_display_str(self.config[d])
                font_color = 'black'

            self.gui['dirs_to_set'][d][1] = tk.Label(dirs_frame, text=display_str, fg=font_color)
            self.gui['dirs_to_set'][d][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(dirs_frame, text='...', command=bind_dirs_command(d))
            btn.grid(column=1, row=i, sticky=tk.W)

    def get_wkt_ids(self):
        wkts_file = self.config['srs_wkts']
        wkts_df = pd.read_csv(wkts_file, index_col=1, header=None)
        return tuple(wkts_df.index)

    @staticmethod
    def get_gps_times():
        return ('Satellite GPS Time', 'GPS Week Seconds')  # TODO: verify names

    @staticmethod
    def get_naming_types():
        naming_types = ('yyyy_[easting]e_[northing]n_las')
        return naming_types

    @staticmethod
    def get_versions():
        return ('1.2', '1.4')

    @staticmethod
    def get_vdatums():
        return ('MHW', 'MLLW', 'GRS80', 'WGS84')

    @staticmethod
    def get_pdrfs():
        return tuple(range(11))

    @staticmethod
    def get_class_picker_msg():
        return ('open class picker...',)

    @staticmethod
    def get_pt_src_id_logic():
        pt_src_id_logic = ('Verify Unique Flight Line IDs')
        return pt_src_id_logic

    def update_version_affected_info(self):
        version = self.gui['check_keys']['version'][0].get()
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
                    
        self.gui['check_keys']['pdrf'][0].set(pdrf)
        self.gui['check_keys']['exp_cls'][0].set(exp_classes)
        self.gui['supp_las_domain'].set(supp_las_domain)

    def add_checks(self):
        check = 'naming'
        get_key_options_def = self.get_naming_types()
        state = 'disabled'
        command = None
        def add_check_key(check, get_key_options_def, state):
            self.gui['check_keys'][check][0] = tk.StringVar()
            self.gui['check_keys'][check][0].set(
                self.config['check_keys'][check])
            self.gui['check_keys'][check][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['check_keys'][check][0],
                *get_key_options_def,
                command=None)
            self.gui['check_keys'][check][1].config(state=state)
            self.gui['check_keys'][check][1].configure(anchor='w')

        def add_naming_key():
            self.gui['check_keys']['naming'][0] = tk.StringVar()
            self.gui['check_keys']['naming'][0].set(
                self.config['check_keys']['naming'])
            self.gui['check_keys']['naming'][1] = tk.OptionMenu(
                checks_frame,
                self.gui['check_keys']['naming'][0], 
                *self.get_naming_types())
            self.gui['check_keys']['naming'][1].config(state='disabled')
            self.gui['check_keys']['naming'][1].configure(anchor='w')

        def add_version_key():
            self.gui['check_keys']['version'][0] = tk.StringVar()
            self.gui['check_keys']['version'][0].set(
                self.config['check_keys']['version'])
            self.gui['check_keys']['version'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['check_keys']['version'][0], 
                *self.get_versions(), 
                command=lambda x: self.update_version_affected_info())
            self.gui['check_keys']['version'][1].configure(anchor='w')

        def add_pdrf_key():
            self.gui['check_keys']['pdrf'][0] = tk.StringVar()
            self.gui['check_keys']['pdrf'][0].set(
                self.config['check_keys']['pdrf'])
            self.gui['check_keys']['pdrf'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['check_keys']['pdrf'][0], 
                *self.get_pdrfs(), 
                command=lambda x: self.update_version_affected_info())
            self.gui['check_keys']['pdrf'][1].config(state='disabled')
            self.gui['check_keys']['pdrf'][1].configure(anchor='w')

        def add_gps_time_key():
            self.gui['check_keys']['gps_time'][0] = tk.StringVar()
            self.gui['check_keys']['gps_time'][0].set(
                self.config['check_keys']['gps_time'])
            self.gui['check_keys']['gps_time'][1] = tk.OptionMenu(
                checks_frame,
                self.gui['check_keys']['gps_time'][0], 
                *self.get_gps_times())
            self.gui['check_keys']['gps_time'][1].config(state='disabled')
            self.gui['check_keys']['gps_time'][1].configure(anchor='w')

        def add_hdatum_key():
            self.gui['check_keys']['hdatum'][0] = tk.StringVar()
            self.gui['check_keys']['hdatum'][0].set(
                self.config['check_keys']['hdatum'])
            self.gui['check_keys']['hdatum'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['check_keys']['hdatum'][0], 
                *self.get_wkt_ids())
            self.gui['check_keys']['hdatum'][1].configure(anchor='w')

        def add_vdatum_key():
            self.gui['check_keys']['vdatum'][0] = tk.StringVar()
            self.gui['check_keys']['vdatum'][0].set(
                self.config['check_keys']['vdatum'])
            self.gui['check_keys']['vdatum'][1] = tk.OptionMenu(
                checks_frame, 
                self.gui['check_keys']['vdatum'][0], 
                *self.get_vdatums())
            self.gui['check_keys']['vdatum'][1].configure(anchor='w')
            self.gui['check_keys']['vdatum'][1].config(state='disabled')

        def add_pt_src_ids_key():
            self.gui['check_keys']['pt_src_ids'][0] = tk.StringVar()
            self.gui['check_keys']['pt_src_ids'][0].set(
                self.config['check_keys']['pt_src_ids'])
            self.gui['check_keys']['pt_src_ids'][1] = tk.OptionMenu(
                checks_frame,
                self.gui['check_keys']['pt_src_ids'][0], 
                *self.get_pt_src_id_logic())
            self.gui['check_keys']['pt_src_ids'][1].config(state='disabled')
            self.gui['check_keys']['pt_src_ids'][1].configure(anchor='w')

        def add_exp_cls_key():
            self.gui['check_keys']['exp_cls'][0] = tk.StringVar()
            self.gui['check_keys']['exp_cls'][0].set(
                self.config['check_keys']['exp_cls'])
            self.gui['check_keys']['exp_cls'][1] = tk.OptionMenu(
                checks_frame,
                self.gui['check_keys']['exp_cls'][0], 
                *self.get_class_picker_msg(),
                command=lambda x: self.pick_classes())
            #self.gui['check_keys']['exp_cls'][1].config(state='disabled')
            self.gui['check_keys']['exp_cls'][1].configure(anchor='w')

        def add_supp_las_domain():
            self.gui['supp_las_domain'] = tk.StringVar()
            self.gui['supp_las_domain'].set(self.config['supp_las_domain'])

        '''Checks'''
        checks_frame = ttk.Frame(self)
        checks_frame.grid(row=self.section_rows['checks'], sticky=tk.NSEW)

        label = tk.Label(checks_frame, text='CHECKS', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        add_naming_key()
        add_version_key()
        add_pdrf_key()
        add_gps_time_key()
        add_hdatum_key()
        add_vdatum_key()
        add_pt_src_ids_key()
        add_exp_cls_key()
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
            self.gui['check_keys'][c][1].grid(column=1, row=i, sticky=tk.EW)

    def add_surfaces(self):
        
        def bind_dirs_command(s):
            def func():
                dir_str = filedialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.gui['surfaces_to_make'][s][2].configure(text=display_str)
                self.gui['surfaces_to_make'][s][3] = dir_str 
            func.__name__ = s
            return func

        def bind_file_command(s):
            def func():
                file_str = filedialog.askdirectory()
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
            chk.grid(column=1, row=0, sticky=tk.EW)

        '''Surfaces'''
        surf_frame = ttk.Frame(self)
        surf_frame.grid(row=self.section_rows['surfaces'], sticky=tk.NSEW)

        label = tk.Label(surf_frame, text='SURFACES', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        for i, s in enumerate(self.gui['surfaces_to_make'], 1):
            subframe = ttk.Frame(surf_frame)
            subframe.grid(row=i, column=0, sticky=tk.EW)

            add_tile_surface()
            add_mosaic_surface()

    def add_run_panel(self):
        run_frame = ttk.Frame(self)
        run_frame.grid(row=self.section_rows['run_button'], 
                       sticky=tk.NSEW, pady=(10, 0))

        self.run_btn = tk.Button(run_frame, text='Run QAQC Processes', 
                        command=self.run_qaqc_process, 
                        width=25, height=3)
        self.run_btn.grid(columnspan=4, row=0, sticky=tk.EW, padx=(100, 0))

        self.check_paths()

    def run_qaqc_process(self):
        self.controller.save_config()
        #progress = self.add_progress_bar()
        
        run_qaqc(self.controller.config_file) #  from qaqc.py
    

if __name__ == '__main__':
    qchecker_path = os.path.dirname(os.path.realpath(__file__))
    os.chdir(qchecker_path)

    now = datetime.datetime.now()
    date_time_now_str = '{}{}{}_{}{}{}'.format(now.year, 
                                               str(now.month).zfill(2), 
                                               str(now.day).zfill(2),
                                               str(now.hour).zfill(2),
                                               str(now.minute).zfill(2),
                                               str(now.second).zfill(2))

    log_file = os.path.join(qchecker_path, 'QChecker_{}.log'.format(date_time_now_str))
    #logging.basicConfig(filename=log_file,
    #                    format='%(asctime)s:%(message)s',
    #                    level=logging.DEBUG)

    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.ERROR)

    app = QaqcApp()
    app.resizable(0, 0)
    app.geometry('400x610')
    app.mainloop()  # tk functionality
