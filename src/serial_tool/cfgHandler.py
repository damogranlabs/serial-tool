"""
This file holds all configuration file save/load functions and handlers.
"""
import json

from serial_tool import defines as defs
from serial_tool import dataModel
from serial_tool import serComm

_CFG_VERSION = 2.0  # configuration file version (not main software version)


class ConfigurationHandler:
    def __init__(self, data: dataModel.SerialToolSettings, signals: dataModel.SharedSignalsContainer):
        """
        This class initialize thread that constantly poll RX buffer and store receive data in a list.
        On after data readout, sigRxNotEmpty signal is emitted to notify parent that new data is available.
        """
        self.dataModel: dataModel.SerialToolSettings = data
        self.signals: dataModel.SharedSignalsContainer = signals

    def saveConfiguration(self, filePath: str):
        """
        Overwrite data with current settings in a json format.
            @param filePath: path where file should be created.
        """
        wData = {}
        wData[defs.CFG_TAG_FILE_VERSION] = _CFG_VERSION
        wData[defs.CFG_TAG_SERIAL_CFG] = {}
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT] = self.dataModel.serialSettings.port
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE] = self.dataModel.serialSettings.baudrate
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE] = self.dataModel.serialSettings.dataSize
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS] = self.dataModel.serialSettings.stopbits
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY] = self.dataModel.serialSettings.parity
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL
        ] = self.dataModel.serialSettings.swFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL
        ] = self.dataModel.serialSettings.hwFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS
        ] = self.dataModel.serialSettings.readTimeoutMs
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS
        ] = self.dataModel.serialSettings.writeTimeoutMs

        wData[defs.CFG_TAG_DATA_FIELDS] = {}
        for channelIndex, data in enumerate(self.dataModel.dataFields):
            wData[defs.CFG_TAG_DATA_FIELDS][channelIndex] = data
        wData[defs.CFG_TAG_NOTE_FIELDS] = {}
        for channelIndex, note in enumerate(self.dataModel.noteFields):
            wData[defs.CFG_TAG_NOTE_FIELDS][channelIndex] = note
        wData[defs.CFG_TAG_SEQ_FIELDS] = {}
        for channelIndex, sequence in enumerate(self.dataModel.seqFields):
            wData[defs.CFG_TAG_SEQ_FIELDS][channelIndex] = sequence

        wData[defs.CFG_TAG_RXLOG] = self.dataModel.displayReceivedData
        wData[defs.CFG_TAG_TXLOG] = self.dataModel.displayTransmittedData
        wData[defs.CFG_TAG_OUTPUT_REPRESENTATION] = self.dataModel.outputDataRepresentation
        wData[defs.CFG_TAG_RX_NEW_LINE] = self.dataModel.rxNewLine
        wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT] = self.dataModel.rxNewLineTimeout

        with open(filePath, "w+", encoding="utf-8") as fileHandler:
            json.dump(wData, fileHandler, indent=4)

    def loadConfiguration(self, filePath: str):
        """
        Read (load) given json file and set new configuration.
            @param filePath: path to load file from.
        """
        with open(filePath, "r", encoding="utf-8") as fileHandler:
            wData = json.load(fileHandler)

        if (defs.CFG_TAG_FILE_VERSION not in wData) or (wData[defs.CFG_TAG_FILE_VERSION] != _CFG_VERSION):
            errorMsg = "Configuration file syntax has changed - unable to set configuration."
            errorMsg += f"\nCurrent version: {_CFG_VERSION}, config file version: {wData[defs.CFG_TAG_FILE_VERSION]}"
            raise Exception(errorMsg)

        try:
            serialSettings = serComm.SerialCommSettings()
            serialSettings.port = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT]
            serialSettings.baudrate = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE]
            serialSettings.dataSize = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE]
            serialSettings.stopbits = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS]
            serialSettings.parity = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY]
            serialSettings.swFlowControl = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL]
            serialSettings.hwFlowControl = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL]
            serialSettings.readTimeoutMs = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS]
            serialSettings.writeTimeoutMs = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS]
            self.dataModel.setSerialSettings(serialSettings)
        except Exception as err:
            errorMsg = f"Unable to set serial settings from a configuration file: {err}"
            self.signals.sigWarning.emit(errorMsg, defs.LOG_COLOR_WARNING)

        try:
            for channel, data in wData[defs.CFG_TAG_DATA_FIELDS].items():
                self.dataModel.setDataField(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_NOTE_FIELDS].items():
                self.dataModel.setNoteField(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_SEQ_FIELDS].items():
                self.dataModel.setSeqField(int(channel), data)
        except Exception as err:
            errorMsg = f"Unable to set data/note/sequence settings from a configuration file: {err}"
            self.signals.sigWarning.emit(errorMsg, defs.LOG_COLOR_WARNING)

        try:
            self.dataModel.setRxDisplayMode(wData[defs.CFG_TAG_RXLOG])
            self.dataModel.setTxDisplayMode(wData[defs.CFG_TAG_TXLOG])
            self.dataModel.setOutputRepresentationMode(wData[defs.CFG_TAG_OUTPUT_REPRESENTATION])
            self.dataModel.setRxNewlineMode(wData[defs.CFG_TAG_RX_NEW_LINE])
            self.dataModel.setRxNewlineTimeout(wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT])
        except Exception as err:
            errorMsg = f"Unable to set log settings from a configuration file: {err}"
            self.signals.sigWarning.emit(errorMsg, defs.LOG_COLOR_WARNING)

    def createDefaultConfiguration(self):
        """
        Set instance of data model with default values.
        Will emit signals to update GUI.
        """
        self.dataModel.setSerialSettings(serComm.SerialCommSettings())
        for channel in range(defs.NUM_OF_DATA_CHANNELS):
            self.dataModel.setDataField(channel, "")
            self.dataModel.setNoteField(channel, "")

        for channel in range(defs.NUM_OF_SEQ_CHANNELS):
            self.dataModel.setSeqField(channel, "")

        self.dataModel.setRxDisplayMode(True)
        self.dataModel.setTxDisplayMode(True)
        self.dataModel.setOutputRepresentationMode(defs.OutputRepresentation.STRING)
        self.dataModel.setRxNewlineMode(False)
