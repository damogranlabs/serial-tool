# -*- coding:utf-8 -*-
"""
Created on Mon Mar 06 22:30:20 2017

@author: domen
"""

import sys
import time
import string
import serial

import sip
sip.setapi('QString', 2)
from PyQt4 import QtCore, QtGui

from gui import Ui_root
from serial_setup_dialog import Ui_SerialSetupDialog

import communication
import filedialog
import log


RECEIVE_DATA_CHECKOUT = 400 #ms
MAX_BUFF_LEN = 1000


OK = 0
ERROR = 1
NUM_OF_COMMANDS_PER_SEQUENCE = 5

##############################################################################
class SerialSetupDialog(QtGui.QDialog):
    def __init__(self, gui):
        QtGui.QDialog.__init__(self)
        
        self.ui = Ui_SerialSetupDialog()
        self.ui.setupUi(self)
        self.gui = gui
        
        QtCore.QObject.connect(self.ui.confirm, QtCore.SIGNAL("clicked()"), self.confirm_configuration)
                
        self.xon_xoff = False
        self.rts_cts = False
        self.bytesize = 0
        self.stopbits = 1
        self.parity_id = 0
        self.parity = 'N'
        
        
        self.bytesize_arr = [self.ui.bytesize_fivebits,
                             self.ui.bytesize_sixbits,
                             self.ui.bytesize_sevenbits,
                             self.ui.bytesize_eightbits]        
        self.ui.bytesize_group.setId(self.ui.bytesize_fivebits, serial.FIVEBITS)
        self.ui.bytesize_group.setId(self.ui.bytesize_sixbits, serial.SIXBITS)
        self.ui.bytesize_group.setId(self.ui.bytesize_sevenbits, serial.SEVENBITS)
        self.ui.bytesize_group.setId(self.ui.bytesize_eightbits, serial.EIGHTBITS)
        
        self.parity_arr = [self.ui.parity_none,
                           self.ui.parity_even,
                           self.ui.parity_odd]
        self.ui.parity_group.setId(self.ui.parity_none, 0)
        self.ui.parity_group.setId(self.ui.parity_even, 1)
        self.ui.parity_group.setId(self.ui.parity_odd, 2)
        
        self.stopbits_arr = [self.ui.stopbits_one, 
                             self.ui.stopbits_two]
        self.ui.stopbits_group.setId(self.ui.stopbits_one, serial.STOPBITS_ONE)
        self.ui.stopbits_group.setId(self.ui.stopbits_two, serial.STOPBITS_TWO)
        
        self.get_data()
                        
#############################################################################
    def get_data(self):
        self.xon_xoff = self.ui.flow_xon_xoff.isChecked()
        self.rts_cts = self.ui.flow_rts_cts.isChecked()
        
        self.bytesize = self.ui.bytesize_group.checkedId()
        self.stopbits = self.ui.stopbits_group.checkedId()
        
        self.parity_id = self.ui.parity_group.checkedId()
        if self.parity_id == 0:
            self.parity = serial.PARITY_NONE
        elif self.parity_id == 1:
            self.parity = serial.PARITY_EVEN
        elif self.parity_id == 2:
            self.parity = serial.PARITY_ODD
        else:
            self.parity = serial.PARITY_NONE
            self.parity_id == 0
        

#############################################################################
    def set_gui_data(self):
        self.ui.flow_xon_xoff.setChecked(eval(self.xon_xoff))
        self.ui.flow_rts_cts.setChecked(eval(self.rts_cts))
        
        bytesize_id = self.bytesize -5  # starts with BYTESIZEFIVE, index starts with 0
        self.bytesize_arr[bytesize_id].setChecked(True)
        
        stopbits_id = self.stopbits -1  # starts with STOPBITONE, index starts with 0
        self.stopbits_arr[stopbits_id].setChecked(True)
                
        self.parity_arr[self.parity_id].setChecked(True)
                
    
############################################################################   
    def confirm_configuration(self):
        self.get_data()
        
        self.close()
        
        log.log_data(self.gui, """Serial setup finished:
    byte size: %s    parity: %s    stop bits: %s    xon/xoff: %s    rts/cts: %s\n
            """ %(self.bytesize, self.parity, self.stopbits, self.xon_xoff, self.rts_cts))
    

#############################################################################   
#############################################################################
class Gui(QtGui.QMainWindow):  #self = gui
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_root()
        self.ui.setupUi(self)
        
        self.serial_setup_dialog = SerialSetupDialog(self)
        
        self.data_field = [self.ui.data_1, 
                           self.ui.data_2,
                           self.ui.data_3,
                           self.ui.data_4,
                           self.ui.data_5,
                           self.ui.data_6,
                           self.ui.data_7,
                           self.ui.data_8]
        
        self.note_field = [self.ui.note_1,
                          self.ui.note_2,
                          self.ui.note_3,
                          self.ui.note_4,
                          self.ui.note_5,
                          self.ui.note_6,
                          self.ui.note_7,
                          self.ui.note_8]
        
        self.delay_field = [self.ui.delay_1,
                           self.ui.delay_2,
                           self.ui.delay_3,
                           self.ui.delay_4,
                           self.ui.delay_5,
                           self.ui.delay_6,
                           self.ui.delay_7,
                           self.ui.delay_8]
        
        self.seq_1_commands = [self.ui.command_1_1,
                               self.ui.command_1_2,
                               self.ui.command_1_3,
                               self.ui.command_1_4,
                               self.ui.command_1_5]
        self.seq_2_commands = [self.ui.command_2_1,
                               self.ui.command_2_2,
                               self.ui.command_2_3,
                               self.ui.command_2_4,
                               self.ui.command_2_5]
        self.seq_3_commands = [self.ui.command_3_1,
                               self.ui.command_3_2,
                               self.ui.command_3_3,
                               self.ui.command_3_4,
                               self.ui.command_3_5]
        self.seq_selector = [self.seq_1_commands,
                             self.seq_2_commands,
                             self.seq_3_commands]
        
        self.next_time = 0
        
        self.command_selector_seq_1 = [self.ui.command_1_1, self.ui.command_1_2, self.ui.command_1_3, self.ui.command_1_4, self.ui.command_1_5]
        self.command_selector_seq_2 = [self.ui.command_2_1, self.ui.command_2_2, self.ui.command_2_3, self.ui.command_2_4, self.ui.command_2_5]
        self.command_selector_seq_3 = [self.ui.command_3_1, self.ui.command_3_2, self.ui.command_3_3, self.ui.command_3_4, self.ui.command_3_5]
        self.sequence_selector = [self.command_selector_seq_1,
                                  self.command_selector_seq_2,
                                  self.command_selector_seq_3]
        
        self.data_out_buff = []
        self._next_data_out_time = 0
        
        self.hex_ascii = False # False = HEX, True = ASCII
        
        log.log_file_init()
        
        self.comm = communication.Communication(self)
        self.filedialog = filedialog.FileDialog(self)
        
        self._set_hex_output()
        self.connect_to_gui()
        
        
##############################################################################
    def connect_to_gui(self):
        #save/load dialog
        QtCore.QObject.connect(self.ui.file_new_configuration, QtCore.SIGNAL("triggered()"), self.show_serial_setup_dialog)
        QtCore.QObject.connect(self.ui.file_save_configuration, QtCore.SIGNAL("triggered()"), self.filedialog.save_configuration)
        QtCore.QObject.connect(self.ui.file_load_configuration, QtCore.SIGNAL("triggered()"), self.filedialog.load_configuration)
        QtCore.QObject.connect(self.ui.file_about, QtCore.SIGNAL("triggered()"), self.filedialog.print_about)
        
        QtCore.QObject.connect(self.ui.setup_serial, QtCore.SIGNAL("triggered()"),self.serial_setup_dialog.show)
        QtCore.QObject.connect(self.ui.setup_clear_log, QtCore.SIGNAL("triggered()"), lambda: log.clear_log(self))
        QtCore.QObject.connect(self.ui.setup_hex_output, QtCore.SIGNAL("triggered()"),self._set_hex_output)
        QtCore.QObject.connect(self.ui.setup_ascii_output, QtCore.SIGNAL("triggered()"), self._set_ascii_output)
        
        # SERIAL PORT setup
        QtCore.QObject.connect(self.ui.com_port_refresh, QtCore.SIGNAL("clicked()"), self.refresh_ports)
        QtCore.QObject.connect(self.ui.com_port_connect, QtCore.SIGNAL("clicked()"), self.connect)
        
        QtCore.QObject.connect(self.ui.send_1, QtCore.SIGNAL("clicked()"), lambda: self.send_data(1))
        QtCore.QObject.connect(self.ui.send_2, QtCore.SIGNAL("clicked()"), lambda: self.send_data(2))
        QtCore.QObject.connect(self.ui.send_3, QtCore.SIGNAL("clicked()"), lambda: self.send_data(3))
        QtCore.QObject.connect(self.ui.send_4, QtCore.SIGNAL("clicked()"), lambda: self.send_data(4))
        QtCore.QObject.connect(self.ui.send_5, QtCore.SIGNAL("clicked()"), lambda: self.send_data(5))
        QtCore.QObject.connect(self.ui.send_6, QtCore.SIGNAL("clicked()"), lambda: self.send_data(6))
        QtCore.QObject.connect(self.ui.send_7, QtCore.SIGNAL("clicked()"), lambda: self.send_data(7))
        QtCore.QObject.connect(self.ui.send_8, QtCore.SIGNAL("clicked()"), lambda: self.send_data(8))
        
        QtCore.QObject.connect(self.ui.send_sequence_1, QtCore.SIGNAL("clicked()"), lambda: self.send_data_sequence(1))
        QtCore.QObject.connect(self.ui.send_sequence_2, QtCore.SIGNAL("clicked()"), lambda: self.send_data_sequence(2))
        QtCore.QObject.connect(self.ui.send_sequence_3, QtCore.SIGNAL("clicked()"), lambda: self.send_data_sequence(3))
        
        self.receive_data_timer = QtCore.QTimer(self)
        self.receive_data_timer.setInterval(RECEIVE_DATA_CHECKOUT)
        QtCore.QObject.connect(self.receive_data_timer,  QtCore.SIGNAL("timeout()"), self.receive_data)
        self.receive_data_timer.start()
 

##############################################################################        
    def show_serial_setup_dialog(self):
        self.serial_setup_dialog.show()
        

##############################################################################        
    def refresh_ports(self):        
        self.comm.refresh_comm_port_list()
        self.next_time = 0

##############################################################################        
    def connect(self):
        self.serial_setup_dialog.get_data()
        
        self.comm.serial_init(self.serial_setup_dialog.bytesize, self.serial_setup_dialog.parity, self.serial_setup_dialog.stopbits, self.serial_setup_dialog.xon_xoff, self.serial_setup_dialog.rts_cts)
        
##############################################################################        
    def send_data(self, ch):
        status, data = self._get_channel_data(ch)
        if status == OK:
            self.comm.serial_write(data, ch)


##############################################################################    
    def send_data_sequence(self, ch):
        for index in range(NUM_OF_COMMANDS_PER_SEQUENCE):
            selected_channel = self.sequence_selector[ch-1][index].currentText()
            if selected_channel != '':
                selected_channel = int(selected_channel)
                status, data = self._get_channel_data(selected_channel)
                if status == OK:
                    self.data_out_buff.append(data) #data first
    
                    delay_time = self._get_channel_delay(selected_channel)
                    self.data_out_buff.append(delay_time)  # than delay
                    
                    self.data_out_buff.append(selected_channel)  # lastly channel number
                else:
                    log.log_error(self, "SEQ: invalid channel data.")
                    return
            else:
                break
        if len(self.data_out_buff) > 0:
            log.log_data(self, "SEQ %s:" %ch)
            self._send_waiting_data()
        else:
            log.log_error(self, "SEQ ignored: no valid setup.")

##############################################################################    
    def _send_waiting_data(self):
        self.next_time = 0  # send first byte immediately
        data = [0]
        
        if time.time() >= self.next_time: #is it time to send byte?
            if len(self.data_out_buff): #is buffer not empty?
                selected_channel = self.data_out_buff[2] #data, delay, CH
                delay_time = self.data_out_buff[1]
                
                if type(self.data_out_buff[0]) == 'list': #channel has multiple bytes to send
                    self.comm.serial_write(self.data_out_buff[0], selected_channel)    #current data == list
                else: # channel has a single byte to send
                    data[0] = self.data_out_buff[0]
                    self.comm.serial_write(data[0], selected_channel)    #current data == int
                
                del self.data_out_buff[:3]   #delete data, delay, channel
                                
                if delay_time > 0:
                    delay_time_f = (float(delay_time) / 1000) #ms resolution
                    self.next_time = float(time.time() + delay_time_f) #delay after this data is sent
                    QtCore.QTimer.singleShot(delay_time, self._send_waiting_data)
                else:
                    self.next_time = 0 #no delay - send next byte immediately
                    self._send_waiting_data() #recursively send out data while buffer is not empty

        return #no waiting data to send

##############################################################################    
    def receive_data(self):
        if self.comm.is_connected:
            data_to_read = self.comm.data_to_read()
            
            if data_to_read > 0:
                data = []
                for i in range(data_to_read):
                    b = ord(self.comm.serial_port.read())
                    data.append(b)
                
                if self.hex_ascii == False:  #HEX
                    data_hex = ', '.join(hex(b) for b in data)
                    log.log_data(self, '\tRX: [%s]\n' %data_hex)
                
                else: #ASCII
                    data_ascii = []
                    for d in data:
                        if d == 0:
                            data_ascii.append('\'' + '0' + '\'')
                        else:
                            data_ascii.append('\'' + chr(d) + '\'')
                    data_ascii = ', '.join(data_ascii)
                    log.log_data(self, '\tRX (ASCII): [%s]\n' %data_ascii)


##############################################################################    
    def _get_channel_data(self, ch):
        #get data from the right text input 
        data = self.data_field[ch-1].text()
                
        #split string into list
        data = data.split(',')
        #strip spaces from list
        data = [d.strip(' ') for d in data]
        
        index = 0
        for d in data:
            if d.isdigit():
                num = int(d)
                if num > 255:
                    log.log_error(self, "To large value for 1 byte: %s" %num)
                    return ERROR, 0
                else:
                    data[index] = num
            else:
                if len(d) > 1:
                    log.log_error(self, "Invalid data lenght: %s" %d)
                    return ERROR, 0
                
                elif len(d) == 0:
                    log.log_error(self, "Invalid data length = 0")
                    return ERROR, 0
                else:
                    data[index] = ord(d)
            index += 1
        
        return OK, data

##############################################################################            
    def _get_channel_note(self, ch):
        ch_note = self.note_field[ch-1].text()
        return ch_note

##############################################################################    
    def _get_channel_delay(self, ch):
        ch_delay = self.delay_field[ch-1].text()
        
        try:
            time_delay = int(ch_delay)
        except:
            log.log_data(self, "SEQ: invalid delay length != number!")
            return 0
        return time_delay
    
##############################################################################    
    def _set_hex_output(self):
        self.hex_ascii = False
        
        self.ui.setup_hex_output.setChecked(True)
        self.ui.setup_ascii_output.setChecked(False)
  
    def _set_ascii_output(self):
        self.hex_ascii = True
        
        self.ui.setup_hex_output.setChecked(False)
        self.ui.setup_ascii_output.setChecked(True)

##############################################################################    
##############################################################################    
def main():
    
    app = QtGui.QApplication(sys.argv)
    
    gui = Gui()    #self = gui
    
    gui.show()
    gui.raise_()

    ret = app.exec_()
    
    gui.comm.serial_port_close()
    
    sys.exit(ret)    

if __name__ == "__main__":
    main()    
    
    
            
