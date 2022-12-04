import asyncio
import logging
import time
import threading
from typing import List, Optional

from PyQt5 import QtCore

from serial_tool import models
from serial_tool import serial_hdlr


class _RxDataHdlr(QtCore.QObject):
    sig_rx_not_empty = QtCore.pyqtSignal()

    def __init__(self, port_hdlr: serial_hdlr.SerialPortHandler) -> None:
        """
        This class initialize thread that read available data with asyncio read and store receive data in a list.
        On data readout, sigRxNotEmpty signal is emitted to notify parent that new data is available.
        """
        super().__init__()

        self._port_hdlr: serial_hdlr.SerialPortHandler = port_hdlr

        self.rx_data: List[int] = []
        self._rx_data_lock = threading.Lock()
        self._rx_not_empty_notified = False

        self._rx_thread_stop_flag = False

    def run(self) -> None:
        """Wait and receive data in async mode. It is run as a thread."""
        try:
            self._port_hdlr.isConnected(True)

            # clear RX data list
            with self._rx_data_lock:
                self.rx_data.clear()

            # start actual thread
            self._rx_thread_stop_flag = False
            while not self._rx_thread_stop_flag:
                try:
                    byte = asyncio.run(self._port_hdlr.async_read_data())  # asynchronously receive 1 byte
                    if byte == b"":
                        continue  # nothing received
                    else:
                        if not self._rx_thread_stop_flag:
                            return
                        # receive data available, read all
                        rx_data = self._port_hdlr.read_data()
                        with self._rx_data_lock:
                            self.rx_data.append(ord(byte))  # first received byte (async)
                            self.rx_data.extend(rx_data)  # other data

                        if not self._rx_not_empty_notified:
                            self._rx_not_empty_notified = True  # prevent notifying multiple times for new data
                            self.sig_rx_not_empty.emit()
                except Exception as err:
                    raise Exception(f"Exception caught in receive thread read_data() function:\n{err}") from err

        except Exception as err:
            logging.error(f"Exception in data receiving thread:\n{err}")
            raise

    def request_stop(self) -> None:
        """Request to stop RX thread. On exit, thread might still be running."""
        self._rx_thread_stop_flag = True

    def get_rx_data(self) -> List[int]:
        """Return all currently received data as a copy."""
        with self._rx_data_lock:
            rx_data = self.rx_data.copy()
            self.rx_data.clear()

        self._rx_not_empty_notified = False  # data is read, new "notify" callback can be generated on next data
        return rx_data


class TxDataSequenceHdlr(QtCore.QObject):
    sig_data_send_event = QtCore.pyqtSignal(int, int)
    sig_seq_tx_finished = QtCore.pyqtSignal(int)
    sig_seq_stop_request = QtCore.pyqtSignal()

    def __init__(
        self,
        port_hdlr: serial_hdlr.SerialPortHandler,
        seq_idx: int,
        parsed_data_fields: List[Optional[List[int]]],
        parsed_seq_data: List[models.SequenceInfo],
    ) -> None:
        """
        This class initialize thread that sends specified sequence over given serial port.

        Args:
            port_hdlr: Initialized serial port handler.
            seq_idx: Index of sequence field that needs to be transmitted.
            parsed_data_fields: list of parsed data fields.
            parsed_seq_data: parsed sequence field info.
        """
        super().__init__()

        self._port_hdlr = port_hdlr
        self.seq_idx = seq_idx
        self.parsed_data_fields = parsed_data_fields
        self.parsed_seq_data = parsed_seq_data

        self._stop_seq_request = False

        # https://doc.qt.io/qt-5/qt.html#ConnectionType-enum
        self.sig_seq_stop_request.connect(self.on_stop_seq_request, type=QtCore.Qt.DirectConnection)

    @QtCore.pyqtSlot()
    def on_stop_seq_request(self) -> None:
        self._stop_seq_request = True

    def run(self) -> None:
        """Execute transmission of sequence data. It is run as a thread."""
        self._port_hdlr.isConnected(True)

        try:
            while not self._stop_seq_request:
                for seq_info in self.parsed_seq_data:
                    if self._stop_seq_request:
                        break

                    data = self.parsed_data_fields[seq_info.channel_idx]
                    assert data is not None

                    for _ in range(seq_info.repeat):
                        if self._stop_seq_request:
                            break

                        self._port_hdlr.write_data(data)
                        self.sig_data_send_event.emit(self.seq_idx, seq_info.channel_idx)

                        if self._stop_seq_request:
                            break
                        time.sleep(seq_info.delay_msec / 1000)
                break
        except Exception as err:
            logging.error(f"Exception while transmitting sequence {self.seq_idx+1}:\n{err}")
            raise

        finally:
            self.sig_seq_tx_finished.emit(self.seq_idx)


class PortHdlr(QtCore.QObject):
    sig_init_request = QtCore.pyqtSignal()
    sig_deinit_request = QtCore.pyqtSignal()

    sig_write = QtCore.pyqtSignal(list)
    sig_data_received = QtCore.pyqtSignal(list)

    sig_connection_successful = QtCore.pyqtSignal()
    sig_connection_closed = QtCore.pyqtSignal()

    def __init__(
        self, serial_settings: serial_hdlr.SerialCommSettings, port_hdlr: serial_hdlr.SerialPortHandler
    ) -> None:
        """Main wrapper around low level serial port handler. This class also holds instances of RX/TX threads."""
        super().__init__()
        self.serial_settings = serial_settings
        self.port_hdlr = port_hdlr

        self._rx_data_hdlr: Optional[_RxDataHdlr] = None
        self._rx_watcher_thread: Optional[QtCore.QThread] = None

        self.connect_signals_to_slots()

    def connect_signals_to_slots(self) -> None:
        self.sig_init_request.connect(self.init_port_and_rx_thread)
        self.sig_deinit_request.connect(self.deinit_port)

        self.sig_write.connect(self.write_data)

    def is_connected(self) -> bool:
        return self.port_hdlr.isConnected()

    def init_port_and_rx_thread(self) -> None:
        if self.port_hdlr.init(self.serial_settings):
            self._rx_data_hdlr = _RxDataHdlr(self.port_hdlr)
            self._rx_data_hdlr.sig_rx_not_empty.connect(self.get_rx_data)

            self._rx_watcher_thread = QtCore.QThread()
            self._rx_data_hdlr.moveToThread(self._rx_watcher_thread)
            self._rx_watcher_thread.started.connect(self._rx_data_hdlr.run)
            self._rx_watcher_thread.start()

            self.sig_connection_successful.emit()
        else:
            self.sig_connection_closed.emit()

    def deinit_port(self) -> None:
        if self._rx_watcher_thread is not None:
            if self._rx_data_hdlr is not None:
                self._rx_data_hdlr.request_stop()
            self._rx_watcher_thread.quit()
            self._rx_watcher_thread.wait()

            self._rx_watcher_thread = None
            self._rx_data_hdlr = None

        self.port_hdlr.close_port()

        self.sig_connection_closed.emit()

    def write_data(self, data: List[int]) -> None:
        self.port_hdlr.write_data(data)

    def get_rx_data(self) -> None:
        assert self._rx_data_hdlr is not None

        data = self._rx_data_hdlr.get_rx_data()
        self.sig_data_received.emit(data)
