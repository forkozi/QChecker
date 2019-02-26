from cx_Freeze import setup, Executable
import sys
import matplotlib

sys.argv.append("build")

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {'packages': ['tkinter', 'matplotlib', 'arcpy'], 
                      'include_files': ['qaqc.ico']}
# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "QAQC_Checker",
        version = "1.0.0alpha",
        description = "SD QAQC tool for contract surveys",
        options = {"build_exe": build_exe_options},
        executables = [Executable("qaqc.py", base=base)])


