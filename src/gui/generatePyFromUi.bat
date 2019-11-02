@echo off
echo Generating GUI objects
pyuic5 --import-from=gui ui/gui.ui -o gui.py
pyuic5 --import-from=gui ui/serialSetupDialog.ui -o serialSetupDialog.py

echo Generating resources
pyrcc5 images/icons.qrc -o icons_rc.py

echo Done.