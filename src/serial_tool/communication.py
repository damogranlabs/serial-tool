"""
This file holds all serial communication utility functions and handlers.
"""
import asyncio
import logging
import time
import threading
from typing import List

from PyQt5 import QtCore

from serial_tool import defines as defs
from serial_tool import serComm


###################################################################################################
class SerialDataReceiverThread(QtCore.QObject):
    sigRxNotEmpty = QtCore.pyqtSignal()

    def __init__(self, portHandler: serComm.SerialPortHandler):
        """
        This class initialize thread that read available data with asyncio read and store receive data in a list.
        On data readout, sigRxNotEmpty signal is emitted to notify parent that new data is available.
        """
        super().__init__()

        self._portHandler: serComm.SerialPortHandler = portHandler

        self._receivedData: list = []
        self._rxDataListLock = threading.Lock()
        self._rxNotEmptyNotified = False

        self._receiveThreadStopFlag = False

    def run(self):
        """
        This is the main Receive Data function that is run when thread is started.
        """
        try:
            self._portHandler.isConnected(True)

            # clear RX data list
            with self._rxDataListLock:
                self._receivedData = []

            # start actual thread
            self._receiveThreadStopFlag = False
            while not self._receiveThreadStopFlag:
                try:
                    byte = asyncio.run(self._portHandler.asyncReadData())  # asynchronously receive 1 byte
                    if byte == b"":
                        continue  # nothing received
                    else:
                        # receive data available, read all
                        receivedData = self._portHandler.readData()
                        with self._rxDataListLock:
                            self._receivedData.append(ord(byte))  # first received byte (async)
                            self._receivedData.extend(receivedData)  # other data

                        if not self._rxNotEmptyNotified:
                            self._rxNotEmptyNotified = True  # prevent notifying multiple times for new data
                            self.sigRxNotEmpty.emit()
                except Exception as err:
                    errorMsg = f"Exception caught in receive thread readData() function:\n{err}"
                    raise Exception(errorMsg)
        except Exception as err:
            logging.error(f"Exception in data receiving thread:\n{err}")
            raise

    def stopReceivingData(self):
        """
        Stop thread by setting self._receiveThreadStopFlag to True. Application must manually wait for
        """
        self._receiveThreadStopFlag = True

    def getAllReceivedData(self) -> list:
        """
        Return all currently received data as a copy.
        """
        with self._rxDataListLock:
            receivedData = self._receivedData.copy()
            self._receivedData = []

        self._rxNotEmptyNotified = False  # data is read, new "notify" callback can be generated on next data
        return receivedData


class SerialDataSequenceTransmitterThread(QtCore.QObject):
    sigSequenceTransmittFinished = QtCore.pyqtSignal(int)
    sigDataSendEvent = QtCore.pyqtSignal(int, int)

    sigSequenceStopRequest = QtCore.pyqtSignal()

    def __init__(
        self,
        portHandler: serComm.SerialPortHandler,
        seqChannel: int,
        parsedDataFields: List[int],
        parsedSeqBlocks: List[defs.SequenceData],
    ):
        """
        This class initialize thread that sends sequence (block of data and delay) over given serial port.
            @param portHandler: must be already existing port handler.
            @param seqChannel: sequence field index
            @param parsedDataFields: list of parsed data fields.
            @param parsedSeqBlocks: list of parsed sequence blocks.
        """
        super().__init__()

        self._portHandler: serComm.SerialPortHandler = portHandler
        self.seqChannel: int = seqChannel
        self.parsedDataFields: List[int] = parsedDataFields
        self.parsedSeqBlocks: List[defs.SequenceData] = parsedSeqBlocks

        self._stopSequenceRequest = False

        # https://doc.qt.io/qt-5/qt.html#ConnectionType-enum
        self.sigSequenceStopRequest.connect(self.onStopSequenceRequest, type=QtCore.Qt.DirectConnection)

    @QtCore.pyqtSlot()
    def onStopSequenceRequest(self):
        self._stopSequenceRequest = True

    def run(self):
        """
        This is the main send sequence function that is run when thread is started.
        """
        self._portHandler.isConnected(True)

        try:
            while not self._stopSequenceRequest:
                for block in self.parsedSeqBlocks[self.seqChannel]:
                    if self._stopSequenceRequest:
                        break

                    data = self.parsedDataFields[block.channelIndex]
                    delay = block.delayMS / 1000

                    for take in range(block.repeat):
                        if self._stopSequenceRequest:
                            break

                        self._portHandler.writeDataList(data)
                        self.sigDataSendEvent.emit(self.seqChannel, block.channelIndex)

                        if self._stopSequenceRequest:
                            break
                        time.sleep(delay)
                break
        except Exception as err:
            logging.error(f"Exception while transmitting sequence {self.seqChannel+1}:\n{err}")
            raise

        finally:
            self.sigSequenceTransmittFinished.emit(self.seqChannel)


class SerialToolPortHandler(QtCore.QObject):
    sigInitRequest = QtCore.pyqtSignal()
    sigDeinitRequest = QtCore.pyqtSignal()

    sigWrite = QtCore.pyqtSignal(list)
    sigDataReceived = QtCore.pyqtSignal(list)

    sigConnectionSuccessfull = QtCore.pyqtSignal()
    sigConnectionClosed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.serialSettings = None
        self.portHandler: serComm.SerialPortHandler = None
        self._rxWatcher: SerialDataReceiverThread = None
        self._rxWatcherThread = None

        self.connectSignalsToSlots()

    def connectSignalsToSlots(self):
        self.sigInitRequest.connect(self.initPortAndReceiveThread)
        self.sigDeinitRequest.connect(self.deinitPort)

        self.sigWrite.connect(self.writeData)

    def isConnected(self) -> bool:
        if self.portHandler is not None:
            if self.portHandler.isConnected():
                return True

        return False

    def initPortAndReceiveThread(self):
        self.portHandler = serComm.SerialPortHandler()
        if self.portHandler.initPort(self.serialSettings):
            self._rxWatcher = SerialDataReceiverThread(self.portHandler)
            self._rxWatcher.sigRxNotEmpty.connect(self.getReceivedData)  # TODO

            self._rxWatcherThread = QtCore.QThread()
            self._rxWatcher.moveToThread(self._rxWatcherThread)
            self._rxWatcherThread.started.connect(self._rxWatcher.run)
            self._rxWatcherThread.start()

            self.sigConnectionSuccessfull.emit()
        else:
            self.sigConnectionClosed.emit()

    def deinitPort(self):
        if self._rxWatcherThread is not None:
            self._rxWatcher.stopReceivingData()
            self._rxWatcherThread.quit()
            self._rxWatcherThread.wait()

            self._rxWatcherThread = None
            self._rxWatcher = None

        if self.portHandler is not None:
            self.portHandler.closePort()
            self.portHandler = None

        self.sigConnectionClosed.emit()

    def writeData(self, data: str):
        self.portHandler.writeDataList(data)

    def getReceivedData(self) -> list:
        receivedData = self._rxWatcher.getAllReceivedData()
        self.sigDataReceived.emit(receivedData)
