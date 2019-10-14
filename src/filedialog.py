# -*- coding: utf-8 -*-
import json
import os
import sys
import glob
import time
import serial
from PyQt5 import QtCore, QtGui, QtWidgets

import log

ABOUT_TEXT = """
    Serial tool v1.5
    14.10.2019
    Domen Jurkovic @ Damogran Labs
    
    http://damogranlabs.com/
    https://github.com/damogranlabs/serial-tool
    http://sourceforge.net/p/serial-tool
"""

OK = 0
ERROR = 1

# json
STR_TEMPLATE_OUTPUT_REPRESENTATION = 'serial'

STR_TEMPLATE_DATA = "_data"
STR_TEMPLATE_NOTE = "_note"
STR_TEMPLATE_DELAY = "_delay"
STR_TEMPLATE_SEQUENCE = "sequence_"

STR_TEMPLATE_SER_BYTESIZE = "0_bytesize"
STR_TEMPLATE_SER_DATARATE = "0_datarate"
STR_TEMPLATE_SER_PARITY = "0_parity"
STR_TEMPLATE_SER_PORT = "0_port"
STR_TEMPLATE_SER_RTSCTS = "0_rtscts"
STR_TEMPLATE_SER_STOPBITS = "0_stopbits"
STR_TEMPLATE_SER_XONXOFF = "0_xonxoff"


##############################################################################
class FileDialog():
    def __init__(self, gui):  # self=FileDialog
        self.gui = gui

    def new_configuration(self):
        for i in range(1, 9):
            # DATA
            self.gui.data_field[i - 1].clear()
            # NOTE
            self.gui.note_field[i - 1].clear()
            # DELAY
            self.gui.delay_field[i - 1].clear()

        # SEQUENCEs
        for i in range(1, 4):
            for j in range(1, 6):
                self.gui.seq_selector[i - 1][j - 1].setCurrentIndex(0)

        log.log_data(self.gui, "New configuration request.")

    def save_configuration(self):
        file_path = self.get_file_path(self.gui._configuration_file_path)

        data = {}
        for i in range(1, 9):
            # DATA
            field_name = str(i) + STR_TEMPLATE_DATA  # x_data fields
            data[field_name] = self.gui.data_field[i - 1].text()
            # NOTE
            field_name = str(i) + STR_TEMPLATE_NOTE  # x_NOTE fields
            data[field_name] = self.gui.note_field[i - 1].text()
            # DELAY
            field_name = str(i) + STR_TEMPLATE_DELAY  # x_DELAY fields
            data[field_name] = int(self.gui.delay_field[i - 1].text())

        # SEQUENCEs
        for i in range(1, 4):
            field_name = STR_TEMPLATE_SEQUENCE + str(i)

            seq_commands_str = ''
            for j in range(1, 6):
                seq_commands_str += str(self.gui.seq_selector[i - 1][j - 1].currentIndex())
                if j != 5:
                    seq_commands_str += ', '

            data[field_name] = seq_commands_str

        # SERIAL PORT
        self.gui.serial_setup_dialog.get_data()
        data[STR_TEMPLATE_SER_BYTESIZE] = self.gui.serial_setup_dialog.bytesize
        data[STR_TEMPLATE_SER_DATARATE] = self.gui.ui.baud_rate_selector.currentIndex()
        data[STR_TEMPLATE_SER_PARITY] = self.gui.serial_setup_dialog.parity
        data[STR_TEMPLATE_SER_PORT] = self.gui.ui.com_port_selector.currentIndex()
        data[STR_TEMPLATE_SER_RTSCTS] = str(self.gui.serial_setup_dialog.rts_cts)
        data[STR_TEMPLATE_SER_STOPBITS] = self.gui.serial_setup_dialog.stopbits
        data[STR_TEMPLATE_SER_XONXOFF] = str(self.gui.serial_setup_dialog.xon_xoff)

        # output representation
        data[STR_TEMPLATE_OUTPUT_REPRESENTATION] = self.gui.output_representation

        status = self._put(data, file_path)
        if status == OK:
            log.log_data(self.gui, "Save configuration done: %s" % file_path)
        else:
            log.log_data(self.gui, "Save configuration ERROR: %s" % file_path)

    def load_configuration(self):
        file_path = self.get_file_path(self.gui._configuration_file_path)
        status, data = self._get(file_path)

        if status == OK:
            # output representation
            if STR_TEMPLATE_OUTPUT_REPRESENTATION in data:  # backward compatibility
                self.gui.set_output_representation(data[STR_TEMPLATE_OUTPUT_REPRESENTATION])

            # MANUAL DATA SEND
            for i in range(1, 9):
                # DATA
                field_name = str(i) + STR_TEMPLATE_DATA  # x_data fields
                value = data[field_name]
                self.gui.data_field[i - 1].setText(value)
                # NOTE
                field_name = str(i) + STR_TEMPLATE_NOTE  # x_NOTE fields
                value = data[field_name]
                self.gui.note_field[i - 1].setText(value)
                # DELAY
                field_name = str(i) + STR_TEMPLATE_DELAY  # x_DELAY fields
                value = data[field_name]
                self.gui.delay_field[i - 1].setText(str(value))

            # SEQUENCEs
            for i in range(1, 4):
                field_name = STR_TEMPLATE_SEQUENCE + str(i)
                values = data[field_name]

                commands = values.split(',')    # split commands for selected sequence
                commands = [int(x) for x in commands]

                for j in range(1, 6):  # set all commands for chosen sequence
                    self.gui.seq_selector[i - 1][j - 1].setCurrentIndex(commands[j - 1])

            # SERIAL PORT SETUP
            self.gui.serial_setup_dialog.bytesize = data[STR_TEMPLATE_SER_BYTESIZE]
            self.gui.ui.baud_rate_selector.setCurrentIndex(data[STR_TEMPLATE_SER_DATARATE])
            self.gui.serial_setup_dialog.parity = data[STR_TEMPLATE_SER_PARITY]
            self.gui.ui.com_port_selector.setCurrentIndex(data[STR_TEMPLATE_SER_PORT])
            self.gui.serial_setup_dialog.rts_cts = data[STR_TEMPLATE_SER_RTSCTS]
            self.gui.serial_setup_dialog.stopbits = data[STR_TEMPLATE_SER_STOPBITS]
            self.gui.serial_setup_dialog.xon_xoff = data[STR_TEMPLATE_SER_XONXOFF]
            self.gui.serial_setup_dialog.set_gui_data()

            log.log_data(self.gui, "Load configuration: %s" % file_path)
        else:
            log.log_data(self.gui, "Load configuration FAILED: %s" % file_path)

    def _get(self, file_path):
        returndata = {}
        try:
            fd = open(file_path, 'r')
            text = fd.read()
            fd.close()
            returndata = json.loads(text)
            status = OK

        except:
            log.log_data(self.gui, "COULD NOT LOAD FILE: %s" % file_path)
            status = ERROR

        return (status, returndata)

    def _put(self, data, file_path):
        try:
            jsondata = json.dumps(data, indent=4, skipkeys=True, sort_keys=True)
            fd = open(file_path, 'w')
            fd.write(jsondata)
            fd.close()
            status = OK
        except:
            log.log_data(self.gui, "COULD NOT WRITE TO %s" % file_path)
            status = ERROR

        return status

    def get_file_path(self, initial_path=None):
        if initial_path is None:
            initial_path = os.path.normpath(os.path.expanduser('~/'))
        fileQuery = QtWidgets.QFileDialog.getOpenFileName(self.gui, "Open configuration", initial_path, "Configuration files (*.txt)")
        self.gui._configuration_file_path = fileQuery[0]
        return self.gui._configuration_file_path  # first field is filepath/name

    def print_about(self):
        log.clear_log(self.gui)

        log.log_data(self.gui, ABOUT_TEXT)
