from cx_Freeze import setup, Executable
import sys
import matplotlib

base = None

if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [cx_Freeze.Executable('qaqc.py', base=base, icon='qaqc.ico')]

cx_Freeze.setup(
    name='QAQC_Checker',
    options={
        'build_exe': {'packages': ['tkinter', 'matplotlib', 'arcpy'], 
                      'include_files': ['qaqc.ico']}
        },
    version='1.0.0alpha',
    description='RSD QAQC tool for contract surveys',
    executables=executables
    )
