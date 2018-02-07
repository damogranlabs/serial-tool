# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 09:49:05 2016

@author: domen
"""

import sys
import glob
import time
import serial
import string
from PyQt5 import QtCore, QtGui

import log

COM_PORT_NOT_CONNECTED = "not connected"
COM_PORT_CONNECTED = "CONNECTED"

SERIAL_READ_WRITE_TIMEOUT = 300

OK = 0
ERROR = 1

##############################################################################
class Communication():
    def __init__(self, gui):   #self=Communication
        self.gui = gui
        
        self.serial_port=serial.Serial()
        self.is_connected = False
        
        self.refresh_comm_port_list()
        
    
##############################################################################
    #refresh serial port  list       
    def refresh_comm_port_list(self):
        self.serial_port_close()
        self.gui.ui.com_port_selector.clear()
        
        if sys.platform.startswith('win'):
            ports = ['COM%s' %(i + 1) for i in range(256)]
        
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        
        else:
            raise EnvironmentError('Unsupported platform')
        
        #list all available ports
        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        
        #set combo box (list) items (list available SERIAL PORTs)
        self.gui.ui.com_port_selector.addItems(list(reversed(result)))
        log.log_data(self.gui, "Serial port refresh request.")
        
                
##############################################################################
    #configure the serial connections 
    def serial_init(self, bytesize=None, parity=None, stopbits=None, xonxoff=None, rtscts=None):
        self.serial_port.port = self.gui.ui.com_port_selector.currentText()
        self.serial_port.baudrate = self.gui.ui.baud_rate_selector.currentText()

        if bytesize is not  None:
                self.serial_port.bytesize = bytesize
        else:
            self.serial_port.bytesize = serial.EIGHTBITS
        
        if parity is not None:
            self.serial_port.parity = parity
        else:
            self.serial_port.parity = serial.PARITY_NONE
        
        if stopbits is not None:
            self.serial_port.stopbits = stopbits
        else:
            self.serial_port.stopbits = serial.STOPBITS_ONE
        
        if xonxoff is not None:
            self.serial_port.xonxoff = xonxoff
        else:
            self.serial_port.xonxoff = False     #disable software flow control
            
        if rtscts is not None:
            self.serial_port.rtscts = rtscts
        else:
            self.serial_port.rtscts = False      #disable hardware (RTS/CTS) flow control
        
        self.serial_port.timeout = SERIAL_READ_WRITE_TIMEOUT         #timeout for read [s]
        self.serial_port.write_timeout = SERIAL_READ_WRITE_TIMEOUT   #timeout for write [s]
        
        self.serial_port.dsrdtr = False      #disable hardware (DSR/DTR) flow control
        
        try:
            self.serial_port.close()
            self.serial_port.open()
            
            if self.serial_port.is_open:
                self.serial_port.reset_input_buffer() #flush input buffer, discarding all its contents
                self.serial_port.reset_output_buffer() #flush output buffer, aborting current output 
                self.clear_serial_buffer()
                
                self.is_connected = True
                self.gui.ui.com_port_selector.setEnabled(False)
                self.gui.ui.baud_rate_selector.setEnabled(False)
                
                self.gui.ui.connection_state.setText(COM_PORT_CONNECTED)
                log.log_data(self.gui, "Serial port connected.")
            else:
                self.is_connected = False
                self.gui.ui.com_port_selector.setEnabled(True)
                self.gui.ui.baud_rate_selector.setEnabled(True)
                
                self.gui.ui.connection_state.setText(COM_PORT_NOT_CONNECTED)
                log.log_data(self.gui, "Serial port not connected.")
                                
        except:
            log.log_data(self.gui, "Serial try...except error!")


##############################################################################    
    def serial_port_close(self):
        if self.serial_port.is_open:
            self.serial_port.close()
        
        self.is_connected  = False
        self.gui.ui.com_port_selector.setEnabled(True)
        self.gui.ui.baud_rate_selector.setEnabled(True)
        self.gui.ui.connection_state.setText(COM_PORT_NOT_CONNECTED)
        log.log_data(self.gui, "Serial port closed.")

        
##############################################################################    
    def serial_flush_input(self):
        if self.is_connected:
            try:    
                self.serial_port.reset_input_buffer()
            except:
                log.log_data(self.gui, "Serial port flush input error!")
            

##############################################################################    
    def serial_flush_output(self):
        if self.is_connected:
            try:
                self.serial_port.reset_output_buffer()
                
            except:
                log.log_data(self.gui, "Serial port flush output error!")
            

##############################################################################
    # read from serial device as long as anything is in control units output buffer
    def clear_serial_buffer(self):
        try:
            while self.serial_port.in_waiting > 0:
                self.serial_port.read(1)
            
        except Exception as e:
            log.log_data(self.gui, "Serial port clear buffer error! %s" %e)
                    

##############################################################################    
    def serial_write(self, data, ch):
        if self.is_connected:
            try:
                num_of_bytes = self.serial_port.write(data)
                if num_of_bytes == len(data):
                    data_hex = ', '.join(("0x%0.2X" %b) for b in data)
                    log.log_data(self.gui, "Send CH %s: [%s]" %(ch, data_hex))
                    
                    return OK
                
                else:   # wrong number of bytes written to serial port
                    log.log_data(self.gui, '! serial_write() number of written data error!')
                    log.log_data(self.gui, '%s instead of %s bytes written.' %(num_of_bytes, len(data)))
                    self.gui.ui.statusbar.showMessage('!!! SERIAL WRITE ERROR - wrong number of bytes written !!!')
                    return ERROR
                
            except Exception as e:
                log.log_data(self.gui, '!!! SERIAL WRITE ERROR: %s' %e)
                
                self.serial_flush_input()
                self.serial_flush_output()
                self.clear_serial_buffer()
                                    
                self.serial_port_close()
                
                return ERROR
            
        else:   #no connection or no connect request
            log.log_data(self.gui, 'Ignored (write-retry) - no connection.')    
            return ERROR

##############################################################################
    def serial_read(self, hex_or_ascii):
        try:
            if self.is_connected:
                data = self.serial_port.read_all()
                
                if len(data) > 0:
                    if hex_or_ascii == False:  #HEX
                        data_hex = ', '.join(hex(d) for d in data)
                        log.log_data(self.gui, '\tRX: [%s]\n' %data_hex)
                    
                    else: #ASCII
                        data_ascii = []
                        for d in data:
                            if d < 128:
                                data_ascii.append(chr(d))
                            
                            else:
                                data_ascii.append(str(d))
                                                
                        data_ascii = ', '.join(data_ascii)

                        log.log_data(self.gui, "\tRX (ASCII): [%s]\n" %data_ascii)
            
        except Exception as e:
            log.log_error(self.gui, "!!! !!! !!! SERIAL READ ERROR:")
            log.log_error(self.gui, "%s" %str(e))

            self.gui.ui.statusbar.showMessage('!!! SERIAL READ ERROR!')

            self.serial_flush_output()
            
            self.serial_port_close()
            
            return (ERROR, 0)        
        


