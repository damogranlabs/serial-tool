@echo off
echo Changin cd to project root dir...
cd ..

echo Activating venv...
CALL "venv_py311/Scripts/activate"

echo Generating GUI objects...
SET SRC_DIR=./ui/
SET DST_DIR=./src/serial_tool/gui/
pyuic5 --import-from=serial_tool.gui -o %DST_DIR%gui.py %SRC_DIR%gui.ui
pyuic5 --import-from=serial_tool.gui -o %DST_DIR%serialSetupDialog.py %SRC_DIR%serialSetupDialog.ui

echo Generating resources...
pyrcc5  -o %DST_DIR%icons_rc.py ./resources/icons.qrc

echo Done.
pause