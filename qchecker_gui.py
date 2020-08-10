from qchecker import run_qaqc
import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
import time
import json
import pandas as pd
import logging


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

        version = 'v1.0.0-rc1'
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
            'DEM': ['DEM', None, None, Path(self.configuration['surfaces_to_make']['DEM'][1])],
            }})

        self.components.update({'mosaics_to_make': {
            'Dz': ['Dz Mosaic', None, None, Path(self.configuration['mosaics_to_make']['Dz'][1])],
            'DEM': ['DEM Mosaic', None, None, Path(self.configuration['mosaics_to_make']['DEM'][1])],
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
            self.configuration['surfaces_to_make'][k][1] = str(Path(self.configuration['qaqc_dir'], k, '{}_tiles'.format(k)))

        # mosaics_to_make
        for k, v in self.components['mosaics_to_make'].items():
            self.configuration['mosaics_to_make'][k][0] = v[1].get()
            self.configuration['mosaics_to_make'][k][1] = str(Path(
                self.configuration['qaqc_dir'], k.lower()))

        # supp_las_domain
        self.configuration['supp_las_domain'] = self.components['supp_las_domain'].get()

        logging.debug('saving {}...'.format(self.config_file))
        with open(self.config_file, 'w') as f:
            json.dump(self.configuration, f)

    @staticmethod
    def show_about():
        about = tk.Toplevel()
        tk.Toplevel.iconbitmap(about, r'.\assets\images\qaqc.ico')
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


class Check:

    def __init__(self):
        self.gui = gui
        self.key = key

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
        print(self.gui['check_keys']['exp_cls'][0].get())
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
                print(k)
                print(self.get_class_status(k))
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
        
        self.gui['check_keys']['exp_cls'][0].set('picking classes...')

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

    def validate_qaqc_dirs(self):

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
            project_ids = next(os.walk(self.config['projects_unc']))[1]
            return tuple(project_ids)

        # -----------------------------------------------------
        # currently only one option (project name)
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
                                       command=lambda x: self.validate_qaqc_dirs())

        proj_down_down.grid(column=1, row=row, sticky=tk.EW)

    def build_dirs(self):
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
        return ('Ellipsoid (meter)', 'Ellipsoid (metre)')

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
        #check = 'naming'
        #get_key_options_def = self.get_naming_types()
        #state = 'disabled'
        #command = None

        def set_string_var(var):
            self.gui['check_keys'][var][0] = tk.StringVar()
            self.gui['check_keys'][var][0].set(self.config['check_keys'][var])
            return self.gui['check_keys'][var][0]

        def set_option_menu(var, parms, cmd, state, anchor):
            option_menu = tk.OptionMenu(*parms, command=cmd)
            self.gui['check_keys'][var][1] = option_menu
            if state:
                option_menu.config(state=state)
            if anchor:
                option_menu.configure(anchor=anchor)




        def add_naming_key():
            string_var = set_string_var('naming')
            parms = (checks_frame, string_var, *self.get_naming_types())
            cmd = None
            set_option_menu('naming', parms, cmd, 'disabled', 'w')

        def add_version_key():
            string_var = set_string_var('version')
            parms = (checks_frame, string_var, *self.get_versions())
            cmd = lambda x: self.update_version_affected_info()
            set_option_menu('version', parms, cmd, None, 'w')

        def add_pdrf_key():
            string_var = set_string_var('pdrf')
            parms = (checks_frame, string_var, *self.get_pdrfs())
            cmd = lambda x: self.update_version_affected_info()
            set_option_menu('pdrf', parms, cmd, 'disabled', 'w')

        def add_gps_time_key():
            string_var = set_string_var('gps_time')
            parms = (checks_frame, string_var, *self.get_gps_times())
            cmd = None
            set_option_menu('gps_time', parms, cmd, 'disabled', 'w')

        def add_hdatum_key():
            string_var = set_string_var('hdatum')
            parms = (checks_frame, string_var, *self.get_wkt_ids())
            cmd = None
            set_option_menu('hdatum', parms, cmd, None, 'w')

        def add_vdatum_key():
            string_var = set_string_var('vdatum')
            parms = (checks_frame, string_var, *self.get_vdatums())
            cmd = None
            set_option_menu('vdatum', parms, cmd, None, 'w')

        def add_pt_src_ids_key():
            string_var = set_string_var('pt_src_ids')
            parms = (checks_frame, string_var, *self.get_pt_src_id_logic())
            cmd = None
            set_option_menu('pt_src_ids', parms, cmd, 'disabled', 'w')

        def add_exp_cls_key():
            string_var = set_string_var('exp_cls')
            parms = (checks_frame, string_var, *self.get_class_picker_msg())
            cmd = lambda x: self.pick_classes()
            set_option_menu('exp_cls', parms, cmd, None, 'w')




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
        
        #def bind_dirs_command(s):
        #    def func():
        #        dir_str = filedialog.askdirectory()
        #        display_str = self.build_display_str(dir_str)
        #        self.gui['surfaces_to_make'][s][2].configure(text=display_str)
        #        self.gui['surfaces_to_make'][s][3] = dir_str 
        #    func.__name__ = s
        #    return func

        #def bind_file_command(s):
        #    def func():
        #        file_str = filedialog.askdirectory()
        #        display_str = self.build_display_str(file_str)
        #        self.gui['mosaics_to_make'][s][2].configure(text=display_str)
        #        self.gui['mosaics_to_make'][s][3] = file_str 
        #    func.__name__ = s
        #    return func

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

        def validate_qaqc_directories(qaqc_dir):
            dirs = [
                qaqc_dir / 'dashboard',
                qaqc_dir / 'dz',
                qaqc_dir / 'dz' / 'dz_tiles',
                qaqc_dir / 'dem',
                qaqc_dir / 'dem' / 'dem_tiles',
                qaqc_dir / 'tile_results',
                qaqc_dir / 'tile_results' / 'json',
                ]

            for d in dirs:
                if not d.exists():
                    os.mkdir(str(d))
                    print('created {}'.format(d))
                else:
                    print('{} already exists'.format(d))

        self.controller.save_config()                                
        validate_qaqc_directories(Path(self.gui['dirs_to_set']['qaqc_dir'][2]))
        run_qaqc(self.controller.config_file)


def set_env_vars(env_name):
    user_dir = os.path.expanduser('~')
    conda_dir = Path(user_dir).joinpath('AppData', 'Local', 'Continuum', 'anaconda3')
    env_dir = conda_dir / 'envs' / env_name
    share_dir = env_dir / 'Library' / 'share'
    script_path = conda_dir / 'Scripts'
    gdal_data_path = share_dir / 'gdal'
    proj_lib_path = share_dir

    if script_path.name not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + str(script_path)
    os.environ["GDAL_DATA"] = str(gdal_data_path)
    os.environ["PROJ_LIB"] = str(proj_lib_path)
    #C:\Users\Nick.Forfinski-Sarko\AppData\Local\Continuum\anaconda3\pkgs\proj4-6.1.1-hc2d0af5_1\Library\share\proj

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.INFO)

    set_env_vars('qchecker')

    app = QaqcApp()
    app.resizable(0, 0)
    app.geometry('400x570')
    app.mainloop()
