"""
This file holds all serial communication utility functions and handlers.
"""
import glob
import sys
import threading
import time

import serial
import serial.serialutil as serialUtil

from defines import *


class SerialCommSettings:
    def __init__(self):
        self.port: str = None
        self.baudrate: int = None
        self.dataSize: serialUtil.SerialBase.BYTESIZES = serial.EIGHTBITS
        self.stopbits: serialUtil.SerialBase.STOPBITS = serial.STOPBITS_ONE
        self.parity: serialUtil.SerialBase.PARITIES = serial.PARITY_NONE
        self.swFlowControl: bool = False  # XON/XOFF
        self.hwFlowControl: bool = False  # RTS/CTS
        self.readTimeoutMs: int = SERIAL_READ_TIMEOUT_MS
        self.writeTimeoutMs: int = SERIAL_WRITE_TIMEOUT_MS

    def __str__(self):
        """
        Overwrite default __str__method and return a string of all arguments.
        """
        settings = f"Data size: {self.dataSize}, "
        settings += f"Stop bits: {self.stopbits}, "
        settings += f"Parity: {serial.PARITY_NAMES[self.parity]}, "
        settings += f"HW Flow Ctrl: {self.hwFlowControl}, "
        settings += f"SW Flow Ctrl: {self.swFlowControl}, "
        settings += f"RX timeout: {self.readTimeoutMs} ms, "
        settings += f"TX timeout: {self.writeTimeoutMs} ms"

        if self.port is not None:
            portSettings = f"{self.port}"
            if self.baudrate is not None:
                portSettings = f"{portSettings} @ {self.baudrate}"
            settings = f"{portSettings}, {settings}"

        return settings


class ParityAsNumbers():
    NONE = 0  # serial.PARITY_NONE
    EVEN = 1  # serial.PARITY_EVEN
    ODD = 2  # serial.PARITY_ODD


def parityToNumber(parity: str) -> int:
    if parity == serial.PARITY_NONE:
        return ParityAsNumbers.NONE
    elif parity == serial.PARITY_EVEN:
        return ParityAsNumbers.EVEN
    elif parity == serial.PARITY_ODD:
        return ParityAsNumbers.ODD
    else:
        errorMsg = f"Unable to convert parity string ({parity}) to a matching number."
        raise Exception(errorMsg)


def parityToString(parity: int) -> str:
    if parity == ParityAsNumbers.NONE:
        return serial.PARITY_NONE
    elif parity == ParityAsNumbers.EVEN:
        return serial.PARITY_EVEN
    elif parity == ParityAsNumbers.ODD:
        return serial.PARITY_ODD
    else:
        errorMsg = f"Unable to convert parity string ({parity}) to a matching number."
        raise Exception(errorMsg)


###################################################################################################
class SerialPortHandler():
    def __init__(self):
        """
        Non-threaded serial port communication class. Holds all needed functions to init, read and write to/from serial port.
        """
        self._portHandle = serial.Serial()
        self.portSettings: SerialCommSettings = SerialCommSettings()

    def getAvailablePorts(self, scanRange: int = 40) -> list:
        """
        Get a list of all available 'COMx' or '/dev/ttyX' serial ports.
            @param scanRange: applicable for windows for COMx, where x is in range from 0 to scanRange
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(scanRange)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        else:
            raise EnvironmentError('Unsupported platform')

        # list all available ports
        availablePorts = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                availablePorts.append(port)
            except (OSError, serial.SerialException):
                pass

        return availablePorts

    def initPort(self, serialSettings: SerialCommSettings, raiseException: bool = True) -> bool:
        """
        Initialize serial port with a given settings and return True on success, False otherwise.
            @param raiseException: if True, raise exception if port is not open.
        """
        try:
            self.closePort()

            self._portHandle.port = serialSettings.port
            self._portHandle.baudrate = serialSettings.baudrate
            self._portHandle.bytesize = serialSettings.dataSize
            self._portHandle.parity = serialSettings.parity
            self._portHandle.stopbits = serialSettings.stopbits
            self._portHandle.xonxoff = serialSettings.swFlowControl
            self._portHandle.rtscts = serialSettings.hwFlowControl
            self._portHandle.dsrdtr = False  # disable hardware (DSR/DTR) flow control
            self._portHandle.timeout = serialSettings.readTimeoutMs / 1000
            self._portHandle.write_timeout = serialSettings.writeTimeoutMs / 1000
            self.portSettings = serialSettings

            self._portHandle.open()

            return True
        except Exception as err:
            if raiseException:
                errorMsg = f"Unable to init serial port with following settings: {serialSettings}"
                errorMsg += f"\nError:\n{err}"
                raise Exception

        return False

    def isConnected(self, raiseException: bool = False) -> bool:
        """
        Return True if connection to serial port is established, False otherwise.
            @param raiseException: if True, raise exception if port is not open.
        """
        status = self._portHandle.is_open
        if not status:
            if raiseException:
                errorMsg = "Serial port is not open."
                raise Exception(errorMsg)

        return status

    def closePort(self, raiseException: bool = False):
        """
        Close port (if open).
            @param raiseException: if True, raise exception if port is not closed at the end.
        """
        if self._portHandle.is_open:
            self._portHandle.close()

        if raiseException and self._portHandle.is_open:
            errorMsg = "Serial port was not closed."
            raise Exception(errorMsg)

    def isReceivedDataAvailable(self) -> bool:
        """
        Return True if there is any data in RX buffer, False otherwise.
        """
        if self._portHandle.in_waiting > 0:
            return True
        else:
            return False

    def flushReceiveBuffer(self):
        """
        Try to flush RX buffed (if port is open).
        Raise exception on error.
        """
        self.isConnected(True)
        self._portHandle.reset_input_buffer()

    def flushWriteBuffer(self):
        """
        Try to flush TX buffer (if port is open).
        Raise exception on error.
        """
        self.isConnected(True)
        self._portHandle.reset_input_buffer()

    def writeData(self, data: str, raiseException: bool = True) -> int:
        """
        Write data to serial port and return number of written bytes.
        Optionally raise exception on error or if not all data bytes were written.
            @param data: string representation of a data to send.
            @param raiseException: if True, raise exception if write was not successfull, False otherwise.
        """
        byteArrayEncodedData = data.encode('utf-8')
        numOfBytesWritten = self._portHandle.write(byteArrayEncodedData)
        if numOfBytesWritten == len(data):
            return numOfBytesWritten
        else:
            if raiseException:
                errorMsg = f"Serial port write data unsuccessfull. {numOfBytesWritten} sent while len(data) = {len(data)}"
                raise Exception(errorMsg)
            else:
                return numOfBytesWritten

    def writeDataList(self, data: [int], raiseException: bool = True) -> int:
        """
        Same as writeData, except 'data' is formatted as a list of integers.
            @param data: list of integers to send (0 - 255).
            @param raiseException: if True, raise exception if write was not successfull, False otherwise.
        """
        numOfBytesWritten = self._portHandle.write(data)
        if numOfBytesWritten == len(data):
            return numOfBytesWritten
        else:
            if raiseException:
                errorMsg = f"Serial port write data list unsuccessfull. {numOfBytesWritten} sent while len(data) = {len(data)}"
                raise Exception(errorMsg)
            else:
                return numOfBytesWritten

    def readData(self) -> [int]:
        """
        Read data from a serial port and return a list of received data (unsigned integers 0 - 255).
        Raise exception on error.
        """
        data = self._portHandle.read(self._portHandle.in_waiting)
        dataAsList = []
        for byteData in data:
            dataAsList.append(byteData)

        return dataAsList
