@echo off
cd ..
echo Activating venv...
CALL "venv_py311/Scripts/activate"

SET SRC_DIR=./ui/
SET DST_DIR=./src/serial_tool/gui/

echo Generating GUI objects
pyuic5 --import-from=serial_tool.gui -o %DST_DIR%gui.py %SRC_DIR%gui.ui
pyuic5 --import-from=serial_tool.gui -o %DST_DIR%serialSetupDialog.py %SRC_DIR%serialSetupDialog.ui

echo Generating resources
pyrcc5 -root /serial_tool/gui/images -o %DST_DIR%/icons_rc.py %SRC_DIR%icons.qrc

echo Done.
pause