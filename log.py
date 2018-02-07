# -*- coding: utf-8 -*-

import sys
import datetime
import datetime
import logging

from PyQt5 import QtCore, QtGui
from gui import Ui_root

import os

LOG_FOLDER_NAME = 'Serial Tool LOG'

##############################################################################
def log_file_init():
    
    # get folder/file absolute path
    cwd = os.getcwd()
    abs_log_file_path = os.path.join(cwd, LOG_FOLDER_NAME)

    if not os.path.exists(abs_log_file_path):
        os.makedirs(abs_log_file_path)

    dateTag = datetime.datetime.now().strftime("%b-%d-%Y")
    log_filename = "%s.log" % dateTag
    abs_file_path = os.path.join(abs_log_file_path, log_filename)
    
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s.%(msecs)03d: %(message)s",
                        datefmt="%H:%M:%S",
                        filename=abs_file_path, 
                        filemode='w')

    logging.info('--------- Log started ---------\n')
    
    
##############################################################################
def log_data(gui, msg):
    msg = str(msg)

    gui.ui.data_log.append(msg)
    gui.ui.data_log.ensureCursorVisible()
    gui.ui.data_log.moveCursor(QtGui.QTextCursor.End)
    
    logging.info(msg)
    print(msg)


##############################################################################        
def log_error(gui, msg):
    logging.info(msg)
    
    msg = str(msg)
    print(msg)

    gui.ui.data_log.setTextColor(QtCore.Qt.red)
    gui.ui.data_log.append(msg)
    gui.ui.data_log.ensureCursorVisible()
    gui.ui.data_log.moveCursor(QtGui.QTextCursor.End)
    gui.ui.data_log.setTextColor(QtCore.Qt.black)
        

##############################################################################
def clear_log(gui):
    gui.ui.data_log.clear()
    
    print('Log clear request.')
