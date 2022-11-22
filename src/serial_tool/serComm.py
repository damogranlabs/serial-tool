from typing import List, Optional

import aioserial
import serial
from serial.tools.list_ports import comports
from serial.serialutil import SerialException

from serial_tool import defines as defs


class SerialCommSettings:
    def __init__(self):
        self.port: Optional[str] = None
        self.baudrate: Optional[int] = None
        self.dataSize: int = serial.EIGHTBITS  # serial.SerialBase.BYTESIZES
        self.stopbits: int = serial.STOPBITS_ONE  # serialUtil.SerialBase.STOPBITS
        self.parity: str = serial.PARITY_NONE  # serialUtil.SerialBase.PARITIES
        self.swFlowControl: bool = False  # XON/XOFF
        self.hwFlowControl: bool = False  # RTS/CTS
        self.readTimeoutMs: int = defs.SERIAL_READ_TIMEOUT_MS
        self.writeTimeoutMs: int = defs.SERIAL_WRITE_TIMEOUT_MS

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


class ParityAsNumbers:
    NONE = 0  # serial.PARITY_NONE
    EVEN = 1  # serial.PARITY_EVEN
    ODD = 2  # serial.PARITY_ODD


def parity_as_int(parity: str) -> int:
    if parity == serial.PARITY_NONE:
        return ParityAsNumbers.NONE
    elif parity == serial.PARITY_EVEN:
        return ParityAsNumbers.EVEN
    elif parity == serial.PARITY_ODD:
        return ParityAsNumbers.ODD
    else:
        raise ValueError(f"Unable to convert parity string ({parity}) to a matching number.")


def parity_as_str(parity: int) -> str:
    if parity == ParityAsNumbers.NONE:
        return serial.PARITY_NONE
    elif parity == ParityAsNumbers.EVEN:
        return serial.PARITY_EVEN
    elif parity == ParityAsNumbers.ODD:
        return serial.PARITY_ODD
    else:
        raise ValueError(f"Unable to convert parity string ({parity}) to a matching number.")


###################################################################################################
class SerialPortHandler:
    def __init__(self):
        """
        Non-threaded serial port communication class.
        Holds all needed functions to init, read and write to/from serial port.
        """
        self._port = aioserial.AioSerial()
        self.settings: SerialCommSettings = SerialCommSettings()

    def get_available_ports(self) -> List[str]:
        """
        Get a list of all available  'COMx' or '/dev/ttyX' serial ports.
        """
        return [port.name for port in comports()]

    def init(self, settings: SerialCommSettings, raise_exc: bool = True) -> bool:
        """Initialize serial port with a given settings and return True on success, False otherwise."""
        self.close_port()

        try:
            self._port = aioserial.AioSerial(
                port=settings.port,
                baudrate=settings.baudrate,
                bytesize=settings.dataSize,
                parity=settings.parity,
                stopbits=settings.stopbits,
                xonxoff=settings.swFlowControl,
                rtscts=settings.hwFlowControl,
                dsrdtr=False,  # disable hardware (DSR/DTR) flow control
                timeout=settings.readTimeoutMs / 1000,
                write_timeout=settings.writeTimeoutMs / 1000,
            )

            self.settings = settings

            return True

        except SerialException as err:
            if raise_exc:
                raise RuntimeError(f"Unable to init serial port with following settings: {settings}") from err
            else:
                return False

    def isConnected(self, raise_exc: bool = False) -> bool:
        """Return True if connection to serial port is established, False otherwise."""
        status = self._port.is_open
        if status:
            return True
        elif raise_exc:
            raise RuntimeError("Unable to open serial port.")
        else:
            return False

    def close_port(self, raise_exc: bool = False) -> None:
        """Close port (if open)."""
        if self._port.is_open:
            self._port.close()

            if raise_exc and self._port.is_open:
                raise RuntimeError("Unable to close serial port!")

    def is_data_available(self) -> bool:
        """Return True if there is any data in RX buffer, False otherwise."""
        return self._port.in_waiting > 0

    def flush_read_buff(self) -> None:
        """Try to flush RX buffed (if port is open)."""
        self.isConnected(True)
        self._port.reset_input_buffer()

    def flush_write_buff(self) -> None:
        """Try to flush TX buffer (if port is open)."""
        self.isConnected(True)
        self._port.reset_input_buffer()

    def write_data(self, data: List[int], raise_exc: bool = True) -> int:
        """Write data to port, where each list item is an integer (0 - 255)."""
        num = self._port.write(data)
        if num == len(data):
            return num
        elif raise_exc:
            raise Exception(f"Serial port write data list unsuccessful. {num} sent while len(data) = {len(data)}")
        else:
            return num

    async def async_read_data(self) -> bytes:
        """
        Asynchronously read data from a serial port and return one byte. Might be an empty byte (b''), which indicates no new received data.
        Raise exception on error.
        """
        byte = await self._port.read_async()  # will wait until one byte will not be received.
        return byte

    def read_data(self) -> List[int]:
        """Read data from a serial port and return a list of received data (unsigned integers 0 - 255)."""
        return list(self._port.read(self._port.in_waiting))
