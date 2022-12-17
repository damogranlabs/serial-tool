import time

import unittest
import serComm


class SerialCommunication(unittest.TestCase):
    def __init__(self):
        self.serialSettings = serComm.SerialCommSettings()
        self.serialSettings.port = "COM5"
        self.serialSettings.baudrate = 115200

    def test_simpleTest(self):
        portHandler = serComm.SerialPortHandler()
        if portHandler.initPort(self.serialSettings, raiseException=False):
            print(f"Connected to port with following settings: {self.serialSettings}")

            for i in range(5):
                txData = "asdasdasd"
                sent = portHandler.writeData(txData)
                print(f"Bytes sent: {sent}")

                time.sleep(0.25)

                rxData = portHandler.readData()
                rxDataStr = "".join(rxData)
                print(f"Bytes received: {rxDataStr}")

                if rxDataStr != txData:
                    print(f"!!! RX and TX Data is not the same:\n\tTX: {txData}\n\tRX: {rxDataStr}")
                    # self.assertFalse(False, f"!!! RX and TX Data is not the same:\n\tTX: {txData}\n\tRX: {rxDataStr}")

            portHandler.closePort()
            return
        print(f"!!! Connection to port unsucesfull. Settings: {self.serialSettings}")

    """
    def test_threadedTest(self):
        import random

        portHandler = serComm.SerialPortHandlerThreaded()
        portHandler.initPort(self.serialSettings)
        portHandler.startReceivingData()
        print(f"Connected and receiving data from port with following settings: {self.serialSettings}")

        txData = '.'
        endTime = time.time() + 10
        lastPrintTime = 0
        nextDataSendTime = random.uniform(0.2, 1.5)
        while time.time() < endTime:
            if time.time() > (lastPrintTime + 1):
                lastPrintTime = time.time()
                print(f"All RX data: {portHandler.getAllReceivedData()}")

            if time.time() > nextDataSendTime:
                portHandler.writeData(txData)
                nextDataSendTime = time.time() + random.uniform(0.0, 1.5)

        portHandler.stopReceivingData()
        portHandler.closePort()
    """
