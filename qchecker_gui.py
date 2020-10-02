import sys

#if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
#    import os
#    from pathlib import Path
#    import pyproj
#    # logging.info('running in a PyInstaller bundle')
#    cwd = Path.cwd()
#    os.environ["PATH"] += os.pathsep + str(cwd)
#    gdal_data_path = cwd / 'Library' / 'share' / 'gdal'
#    os.environ["GDAL_DATA"] = str(gdal_data_path)
#    #pyproj.datadir.set_data_dir(str(cwd / "pyproj"))

import logging
import tkinter as tk
from tkinter import ttk, filedialog
import os
from pathlib import Path
import time
import json
import multiprocessing as mp
import pandas as pd
import pyproj

from qchecker import run_qaqc
from listener import listener_process

logger = logging.getLogger(__name__)


def set_env_vars_frozen():
    import os
    from pathlib import Path
    import pyproj
    logging.info('running in a PyInstaller bundle')
    cwd = Path.cwd()
    os.environ["PATH"] += os.pathsep + str(cwd)
    #gdal_data_path = cwd / 'Library' / 'share' / 'gdal'
    #proj_lib_path = cwd / 'Library' / 'share' / 'proj'
    #os.environ["GDAL_DATA"] = str(gdal_data_path)
    #os.environ["PROJ_LIB"] = str(proj_lib_path)
    pyproj.datadir.set_data_dir(str(cwd / "pyproj"))
    #pyproj.datadir.set_data_dir(str(proj_lib_path))


def set_env_vars(env_name):
    user_dir = os.path.expanduser('~')
    path_parts = ('AppData', 'Local', 'Continuum', 'anaconda3')
    conda_dir = Path(user_dir).joinpath(*path_parts)
    env_dir = conda_dir / 'envs' / env_name
    share_dir = env_dir / 'Library' / 'share'
    script_path = conda_dir / 'Scripts'
    gdal_data_path = share_dir / 'gdal'
    proj_lib_path = share_dir / 'proj'

    if script_path.name not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + str(script_path)

    os.environ["GDAL_DATA"] = str(gdal_data_path)
    os.environ["PROJ_LIB"] = str(proj_lib_path)


LARGE_FONT_BOLD = ('Verdanna', 11, 'bold')
NORM_FONT = ('Verdanna', 10)
NORM_FONT_BOLD = ('Verdanna', 10, 'bold')


class QaqcApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.config_file = r'.\assets\config_files\qaqc_config.json'
        self.load_config()
        print(json.dumps(self.config, indent=2))
        self.set_gui_components()

        # show splash screen
        self.withdraw()
        splash = Splash(self)

        version = 'v1.0.1'
        tk.Tk.wm_title(self, 'Q-Checker {}'.format(version))
        tk.Tk.iconbitmap(self, r'.\assets\images\qaqc.ico')

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
        self.components = {}

        self.components.update({'dirs_to_set': {
            'project_dir': ['Project Dir.', None, self.config['project_dir']],
            'qaqc_dir': ['QAQC Root Dir.', None, self.config['qaqc_dir']],
            'las_tile_dir': ['Las Tiles', None, self.config['las_tile_dir']],
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
            'Dz': ['DZ', None, None, Path(self.config['surfaces_to_make']['Dz'][1])],
            'DEM': ['DEM', None, None, Path(self.config['surfaces_to_make']['DEM'][1])],
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
                self.config = json.load(cf)
        else:
           logging.debug('configuration file doesn\'t exist')

    def save_config(self):

        # dirs_to_set
        for k, v in self.components['dirs_to_set'].items():
            self.config[k] = str(v[2])

        # checks_to_do
        for k, v in self.components['checks_to_do'].items():
            self.config['checks_to_do'][k] = v[1].get()

        # check_keys
        for k, v in self.components['check_keys'].items():
            self.config['check_keys'][k] = v[0].get()

        # surfaces_to_make
        for k, v in self.components['surfaces_to_make'].items():
            self.config['surfaces_to_make'][k][0] = v[1].get()
            p = Path(self.config['qaqc_dir'], k)
            self.config['surfaces_to_make'][k][1] = str(p)

        # supp_las_domain
        self.config['supp_las_domain'] = self.components['supp_las_domain'].get()

        logging.debug('saving {}...'.format(self.config_file))
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

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

    def __init__(self, gui, id, frame, info):
        self.gui = gui
        self.id = id
        self.frame = frame
        self.str_var = None
        self.bool_var = None
        self.__dict__.update((k, v) for k, v in info.items())

    def set_string_var(self, check_config):
        self.str_var = tk.StringVar()
        self.str_var.set(check_config)
        self.gui['check_keys'][self.id][0] = self.str_var

    def set_option_menu(self):
        option_menu = tk.OptionMenu(self.frame, self.str_var, 
                                    *self.keys, command=self.cmd)
        self.gui['check_keys'][self.id][1] = option_menu
        if self.status:
            option_menu.config(state=self.status)
        if self.anchor:
            option_menu.configure(anchor=self.anchor)

    def set_bool_var(self, is_checked):
        self.bool_var = tk.BooleanVar()
        self.bool_var.set(is_checked)
        self.gui['checks_to_do'][self.id][1] = self.bool_var

    def set_check_button(self, i):
        chk = tk.Checkbutton(
            self.frame, 
            text=self.gui['checks_to_do'][self.id][0],
            var=self.gui['checks_to_do'][self.id][1], 
            anchor=tk.W, justify=tk.LEFT)
        chk.grid(column=0, row=i, sticky=tk.W)
        self.gui['check_keys'][self.id][1].grid(column=1, row=i, sticky=tk.EW)


class MainGuiPage(ttk.Frame):

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)

        self.parent = parent  # container made in QaqcApp
        self.controller = controller
        self.config = controller.config  # from QaqcApp
        self.gui = controller.components  # from QaqcApp
        self.las_classes_file = self.config['las_classes_json']

        self.section_rows = {
            'dirs': 0,
            'checks': 1,
            'surfaces': 2,
            'run_button': 3,
            }

        #  Build GUI
        self.control_panel_width = 50
        self.label_width = 23
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
        logging.info(self.gui['check_keys']['exp_cls'][0].get())
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
                logging.info(k)
                logging.info(self.get_class_status(k))
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

        prog_frame = ttk.Frame(popup)
        prog_frame.grid(row=0, sticky=tk.EW)
        
        # checks progress
        prog_label1a = tk.Label(prog_frame, text='Tiles', 
                                justify=tk.LEFT, anchor=tk.W)
        prog_label1a.grid(column=0, row=0, sticky=tk.EW)
        prog_bar1 = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL, 
                                    length=500, value=0, 
                                    maximum=100, mode='indeterminate') 
        prog_bar1.grid(column=1, row=0, sticky=tk.EW)
        prog_label1b = tk.Label(prog_frame, justify=tk.LEFT, anchor=tk.W)
        prog_label1b.grid(column=2, row=0, sticky=tk.EW)

        # surfaces progress
        prog_label2a = tk.Label(prog_frame, text='Mosaics', 
                                justify=tk.LEFT, anchor=tk.W)
        prog_label2a.grid(column=0, row=1, sticky=tk.EW)
        progress_bar2 = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL, 
                                        length=500, value=0,
                                       maximum=100, mode='indeterminate') 
        progress_bar2.grid(column=1, row=1, sticky=tk.EW)
        prog_label2b = tk.Label(prog_frame, justify=tk.LEFT, anchor=tk.W)
        prog_label2b.grid(column=2, row=1, sticky=tk.EW)

        popup.update()

        progress = (prog_label1a, prog_bar1, prog_label1b, 
                    prog_label2a, progress_bar2, prog_label2b)

        return progress 

    def check_paths(self):
        default_txt = '(specify path)'
        dir_status = []
        dir_types = ('project_dir', 'qaqc_dir', 'las_tile_dir')
        for d in dir_types:
            if str(self.gui['dirs_to_set'][d][2]) != default_txt:
                dir_status.append(True)
            else:
                dir_status.append(False)
        if all(dir_status):
            self.run_btn['state'] = 'normal'
        else:
            self.run_btn['state'] = 'disabled'

    def build_dirs(self):       
        dirs_frame = ttk.Frame(self)
        dirs_frame.grid(row=self.section_rows['dirs'], sticky=tk.NSEW)
        label = tk.Label(dirs_frame, text='DIRECTORIES', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        def bind_dirs_cmd(d):
            def func():
                dir_str = filedialog.askdirectory()
                display_str = self.build_display_str(dir_str)
                self.gui['dirs_to_set'][d][1].configure(text=display_str, 
                                                        fg='black')
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

            self.gui['dirs_to_set'][d][1] = tk.Label(dirs_frame, 
                                                     text=display_str, 
                                                     fg=font_color)
            self.gui['dirs_to_set'][d][1].grid(column=2, row=i, sticky=tk.W)

            btn = tk.Button(dirs_frame, text='...', command=bind_dirs_cmd(d))
            btn.grid(column=1, row=i, sticky=tk.W)

    def get_wkt_ids(self):
        wkts_file = self.config['srs_wkts']
        wkts_df = pd.read_csv(wkts_file, index_col=1, header=None)
        return tuple(wkts_df.index)

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
        checks_frame = ttk.Frame(self)
        checks_frame.grid(row=self.section_rows['checks'], sticky=tk.NSEW)

        label = tk.Label(checks_frame, text='CHECKS', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        check_info = {
            'naming': {
                'keys': ('yyyy_[easting]e_[northing]n_las'),
                'cmd': None,
                'status': 'disabled',
                'anchor': 'w'
                },
            'version': {
                'keys': ('1.2', '1.4'),
                'cmd': lambda x: self.update_version_affected_info(),
                'status': None,
                'anchor': 'w'
                },
            'pdrf': {
                'keys': tuple(range(11)),
                'cmd': lambda x: self.update_version_affected_info(),
                'status': 'disabled',
                'anchor': 'w'
                },
            'gps_time': {
                'keys': ('Satellite GPS Time', 'GPS Week Seconds'),
                'cmd': None,
                'status': 'disabled',
                'anchor': 'w'
                },
            'hdatum': {
                'keys': self.get_wkt_ids(),
                'cmd': None,
                'status': None,
                'anchor': 'w'
                },
            'vdatum': {
                'keys': ('Ellipsoid (meter)', 'Ellipsoid (metre)'),
                'cmd': None,
                'status': None,
                'anchor': 'w'
                },
            'pt_src_ids': {
                'keys': ('Verify Unique Flight Line IDs'),
                'cmd': None,
                'status': 'disabled',
                'anchor': 'w'
                },
            'exp_cls': {
                'keys': ('open class picker...',),
                'cmd': lambda x: self.pick_classes(),
                'status': None,
                'anchor': 'w'
                },
            }

        self.parent.checks = []
        for i, (id, info) in enumerate(check_info.items(), start=1):
            check = Check(self.gui, id, checks_frame, info)

            # dropdowns
            check.set_string_var(self.config['check_keys'][id])
            check.set_option_menu()

            # checkboxes
            check.set_bool_var(self.config['checks_to_do'][id])
            check.set_check_button(i)

            self.parent.checks.append(check)

        def add_supp_las_domain():
            self.gui['supp_las_domain'] = tk.StringVar()
            self.gui['supp_las_domain'].set(self.config['supp_las_domain'])

        add_supp_las_domain()

    def add_surfaces(self):     

        def add_tile_surface():
            self.gui['surfaces_to_make'][s][1] = tk.BooleanVar()
            is_checked = self.config['surfaces_to_make'][s][0]
            self.gui['surfaces_to_make'][s][1].set(is_checked)
            chk = tk.Checkbutton(
                subframe, 
                text=self.gui['surfaces_to_make'][s][0], 
                var=self.gui['surfaces_to_make'][s][1], 
                anchor=tk.W, justify=tk.LEFT, width=13)
            chk.grid(column=0, row=0, sticky=tk.EW)

        surf_frame = ttk.Frame(self)
        surf_frame.grid(row=self.section_rows['surfaces'], sticky=tk.NSEW)
        label = tk.Label(surf_frame, text='SURFACES', font=LARGE_FONT_BOLD)
        label.grid(row=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        for i, s in enumerate(self.gui['surfaces_to_make'], 1):
            subframe = ttk.Frame(surf_frame)
            subframe.grid(row=i, column=0, sticky=tk.EW)
            add_tile_surface()

    def add_run_panel(self):
        run_frame = ttk.Frame(self)
        run_frame.grid(row=self.section_rows['run_button'], 
                       sticky=tk.NSEW, pady=(10, 0))

        self.run_btn = tk.Button(run_frame, text='Run QAQC', 
                        command=self.run_qaqc_process, 
                        width=50, height=3, bg='#A9A9A9')
        self.run_btn.grid(columnspan=4, row=0, sticky=tk.EW, padx=(10, 0))

        self.check_paths()

    def run_qaqc_process(self):

        def validate_qaqc_dirs(qaqc_dir):
            dirs = [
                qaqc_dir / 'dashboard',
                qaqc_dir / 'dz',
                qaqc_dir / 'dem',
                qaqc_dir / 'tile_results',
                qaqc_dir / 'tile_results' / 'json',
                ]

            for d in dirs:
                if not d.exists():
                    os.mkdir(str(d))
                    logging.info('created {}'.format(d))
                else:
                    logging.info('{} already exists'.format(d))

        self.controller.save_config()                                
        validate_qaqc_dirs(Path(self.gui['dirs_to_set']['qaqc_dir'][2]))
        run_qaqc(self.controller.config_file)  # from qchecker.py


def root_configurer(queue):
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)


if __name__ == '__main__':

    # to create exe, use the following...
    # pyinstaller --distpath=Z:\qchecker\dist --workpath=Z:\qchecker\build qchecker.spec

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        logging.info('running in a PyInstaller bundle')
        #set_env_vars_frozen()
    else:
        logging.info('running in a normal Python process')
        set_env_vars('qchecker')

    # Required for pyinstaller support of multiprocessing
    mp.freeze_support()

    queue = mp.Manager().Queue(-1)
    shared_dict = mp.Manager().dict()
    listener = mp.Process(target=listener_process, args=(queue,))
    listener.start()
    root_configurer(queue)
    logger.info('Starting Q-Checker')

    app = QaqcApp()
    app.resizable(0, 0)
    app.geometry('380x555')
    app.mainloop()

    logger.info('main function ends')
    listener.join()