# -*- coding: utf-8 -*-
"""
Date: 8.2.2018
Author: Domen Jurkovic
www.damogranlabs.com

This is a template file to build (freeze) python script to windows executable.
Setup:
1. Copy this script (to_exe.py) and bat file (to_exe.bat) to your project folder
2. Edit to_exe.py. Also, finetune includes & excludes
    Optionally, edit to_exe.bat:
        - change "build" command to bdist_msi or other cx_freeze build options
        - remove pause at the end to close terminal immediately
3. Run/re-run to_exe.bat script everytime build mus be updated

Steps this script does:
1. Create build and executable in \build subfolder of to_exe.py script
2. Remove .zip file in \build folder if it already exists (on re-running)
3. Zip all content in \build subfolder

cx_freeze docs:
https://cx-freeze.readthedocs.io/en/latest/
http://cx-freeze.readthedocs.io/en/latest/distutils.html
"""

import os
import sys
import shutil

from cx_Freeze import Executable, setup

sys.argv.append("build")  # no need to pass script command line arguments

# EDIT according to your project
SCRIPT = "serialTool.pyw"  # main script to build to .exe
APP_NAME = "SerialTool"  # also output name of .exe file
DESCRIPTION = "Serial Port Utility Tool"
VERSION = "2.2"
GUI = True  # if true, this is GUI based app - no console is displayed
ICON = "gui/images/SerialTool.ico"  # your icon or None

CREATE_ZIP = True  # set to True if you wish to create a zip once build is generated

executable_options = {
    "build_exe": {
        # pyqt5 (from official cx_freeze examples)
        "includes": ["atexit"],
        # exclude all other GUIs except Pyqt5
        "excludes": ["wx", "gtk", "PyQt4", "Tkinter"],
        # add your files (like images, ...)
        # 'include_files': [ICON],
        # amount of data displayed while freezing
        "silent": [True],
        # output directory
        "build_exe": "..\\build",
    }
}


##############################################################################
# cx_freeze stuff
##############################################################################
_app_name_exe = APP_NAME + ".exe"
if GUI:
    base = "Win32GUI"
else:
    base = None

# clear directory at the beginning
thisScriptDir = os.path.dirname(os.path.abspath(__file__))
build_path = os.path.normpath(os.path.join(thisScriptDir, "..", "build"))
if os.path.exists(build_path):
    shutil.rmtree(build_path)

# http://cx-freeze.readthedocs.io/en/latest/distutils.html#cx-freeze-executable
exe = Executable(script=SCRIPT, targetName=_app_name_exe, base=base, icon=ICON)

setup(name=APP_NAME, version=VERSION, description=DESCRIPTION, options=executable_options, executables=[exe])

if os.path.exists(build_path):
    items = os.listdir(build_path)
    if items:
        if f"{APP_NAME}.exe" in items:
            print("Distribution created in \\build subfolder")
        else:
            print(f"'build' subfolder exists, but {APP_NAME}.exe can't be found")
            sys.exit(1)
    else:
        print(f"'build' subfolder exists, but is emtpy.")
        sys.exit(1)
else:
    print("Build failed - no 'build' subfolder was created.")
    sys.exit(1)
# end of cx_freeze stuff

##############################################################################
# distribuition created in \build subfolder, create zip
# create zip file in the root folder
if not CREATE_ZIP:
    print("\nBuild finished.")
    sys.exit(0)
else:
    print("\Creating a zip of a project...")

zip_name = APP_NAME + ".zip"
zip_path = os.path.join(build_path, zip_name)

root_zip_path = shutil.make_archive(APP_NAME, "zip", build_path)
print("Zip created")

# move zip to \build subfolder
shutil.move(root_zip_path, build_path)
print("Zip moved to \\build subfolder")

print("\nBuild & zip finished.")
sys.exit(0)
