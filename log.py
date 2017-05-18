# -*- coding: utf-8 -*-

import sys
import datetime
import datetime
import logging

from PyQt4 import QtCore, QtGui
from gui import Ui_root

import os

LOG_FOLDER_NAME = 'Serial Tool LOG'

##############################################################################
def log_file_init():
    dateTag = datetime.datetime.now().strftime("%d-%b-%Y")
    #filename and destination
    cwd = os.getcwd() #current working directory
    
    if sys.platform.startswith('win'):
        log_wd = cwd + '\\' + LOG_FOLDER_NAME + '\\'
        log_filename = log_wd +'%s.log' %dateTag
        
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        log_wd = cwd + '//' + LOG_FOLDER_NAME + '//'
        log_filename = log_wd + '%s.log' %dateTag
    else:
        raise EnvironmentError('Unsupported platform')
        
    if not os.path.exists(log_wd):
        os.makedirs(log_wd)
    
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s.%(msecs)03d: %(message)s",
                        datefmt="%H:%M:%S",
                        filename=log_filename, 
                        filemode='w')

    logging.info('--------- Log started ---------\n')
    
    
##############################################################################
def log_data(gui, msg):
    gui.ui.data_log.append(msg)
    gui.ui.data_log.ensureCursorVisible()
    gui.ui.data_log.moveCursor(QtGui.QTextCursor.End)
    
    logging.info(msg)
    print msg


##############################################################################        
def log_error(gui, msg):
    logging.info(msg)
    print msg

    msg_html = ('<p style="color:red;">' + msg + '</p>' + ' ')  #' ' so text is blacked out. bug?
    gui.ui.data_log.append(msg_html)
    gui.ui.data_log.ensureCursorVisible()
    gui.ui.data_log.moveCursor(QtGui.QTextCursor.End)
        

##############################################################################
def clear_log(gui):
    gui.ui.data_log.clear()
    
    print "Log clear request."
