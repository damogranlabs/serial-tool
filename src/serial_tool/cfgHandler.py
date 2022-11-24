"""
This file holds all configuration file save/load functions and handlers.
"""
import json

from serial_tool import defines as defs
from serial_tool import dataModel
from serial_tool import serial_hdlr

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
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT] = self.dataModel.serial_settings.port
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE] = self.dataModel.serial_settings.baudrate
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE] = self.dataModel.serial_settings.dataSize
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS] = self.dataModel.serial_settings.stopbits
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY] = self.dataModel.serial_settings.parity
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL
        ] = self.dataModel.serial_settings.swFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL
        ] = self.dataModel.serial_settings.hwFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS
        ] = self.dataModel.serial_settings.readTimeoutMs
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS
        ] = self.dataModel.serial_settings.writeTimeoutMs

        wData[defs.CFG_TAG_DATA_FIELDS] = {}
        for channelIndex, data in enumerate(self.dataModel.data_fields):
            wData[defs.CFG_TAG_DATA_FIELDS][channelIndex] = data
        wData[defs.CFG_TAG_NOTE_FIELDS] = {}
        for channelIndex, note in enumerate(self.dataModel.note_fields):
            wData[defs.CFG_TAG_NOTE_FIELDS][channelIndex] = note
        wData[defs.CFG_TAG_SEQ_FIELDS] = {}
        for channelIndex, sequence in enumerate(self.dataModel.seq_fields):
            wData[defs.CFG_TAG_SEQ_FIELDS][channelIndex] = sequence

        wData[defs.CFG_TAG_RXLOG] = self.dataModel.display_rx_data
        wData[defs.CFG_TAG_TXLOG] = self.dataModel.display_tx_data
        wData[defs.CFG_TAG_OUTPUT_REPRESENTATION] = self.dataModel.output_data_representation
        wData[defs.CFG_TAG_RX_NEW_LINE] = self.dataModel.new_line_on_rx
        wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT] = self.dataModel.new_line_on_rx_timeout_msec

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
            msg = "Configuration file syntax has changed - unable to set configuration."
            msg += f"\nCurrent version: {_CFG_VERSION}, config file version: {wData[defs.CFG_TAG_FILE_VERSION]}"
            raise Exception(msg)

        try:
            serialSettings = serial_hdlr.SerialCommSettings()
            serialSettings.port = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT]
            serialSettings.baudrate = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE]
            serialSettings.dataSize = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE]
            serialSettings.stopbits = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS]
            serialSettings.parity = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY]
            serialSettings.swFlowControl = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL]
            serialSettings.hwFlowControl = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL]
            serialSettings.readTimeoutMs = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS]
            serialSettings.writeTimeoutMs = wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS]
            self.dataModel.set_serial_settings(serialSettings)
        except KeyError as err:
            msg = f"Unable to set serial settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            for channel, data in wData[defs.CFG_TAG_DATA_FIELDS].items():
                self.dataModel.set_data_field(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_NOTE_FIELDS].items():
                self.dataModel.set_note_field(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_SEQ_FIELDS].items():
                self.dataModel.set_seq_field(int(channel), data)
        except KeyError as err:
            msg = f"Unable to set data/note/sequence settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            self.dataModel.set_rx_display_ode(wData[defs.CFG_TAG_RXLOG])
            self.dataModel.set_tx_display_mode(wData[defs.CFG_TAG_TXLOG])
            self.dataModel.set_output_representation_mode(wData[defs.CFG_TAG_OUTPUT_REPRESENTATION])
            self.dataModel.set_new_line_on_rx_mode(wData[defs.CFG_TAG_RX_NEW_LINE])
            self.dataModel.set_new_line_on_rx_timeout(wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT])
        except KeyError as err:
            msg = f"Unable to set log settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

    def createDefaultConfiguration(self):
        """
        Set instance of data model with default values.
        Will emit signals to update GUI.
        """
        self.dataModel.set_serial_settings(serial_hdlr.SerialCommSettings())
        for channel in range(defs.NUM_OF_DATA_CHANNELS):
            self.dataModel.set_data_field(channel, "")
            self.dataModel.set_note_field(channel, "")

        for channel in range(defs.NUM_OF_SEQ_CHANNELS):
            self.dataModel.set_seq_field(channel, "")

        self.dataModel.set_rx_display_ode(True)
        self.dataModel.set_tx_display_mode(True)
        self.dataModel.set_output_representation_mode(defs.OutputRepresentation.STRING)
        self.dataModel.set_new_line_on_rx_mode(False)
