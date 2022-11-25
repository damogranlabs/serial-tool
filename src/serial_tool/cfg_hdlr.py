"""
This file holds all configuration file save/load functions and handlers.
"""
import json

from serial_tool import defines as defs
from serial_tool import models
from serial_tool import serial_hdlr

_CFG_VERSION = 2.0  # configuration file version (not main software version)


class ConfigurationHdlr:
    def __init__(self, data_cache: models.RuntimeDataCache, signals: models.SharedSignalsContainer) -> None:
        """
        This class initialize thread that constantly poll RX buffer and store receive data in a list.
        On after data readout, sigRxNotEmpty signal is emitted to notify parent that new data is available.
        """
        self.data_cache = data_cache
        self.signals = signals

    def save_cfg(self, path: str) -> None:
        """Overwrite data with current settings in a json format."""
        wData = {}
        wData[defs.CFG_TAG_FILE_VERSION] = _CFG_VERSION
        wData[defs.CFG_TAG_SERIAL_CFG] = {}
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT] = self.data_cache.serial_settings.port
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE] = self.data_cache.serial_settings.baudrate
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE] = self.data_cache.serial_settings.dataSize
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS] = self.data_cache.serial_settings.stopbits
        wData[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY] = self.data_cache.serial_settings.parity
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL
        ] = self.data_cache.serial_settings.swFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL
        ] = self.data_cache.serial_settings.hwFlowControl
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS
        ] = self.data_cache.serial_settings.readTimeoutMs
        wData[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS
        ] = self.data_cache.serial_settings.writeTimeoutMs

        wData[defs.CFG_TAG_DATA_FIELDS] = {}
        for channelIndex, data in enumerate(self.data_cache.data_fields):
            wData[defs.CFG_TAG_DATA_FIELDS][channelIndex] = data
        wData[defs.CFG_TAG_NOTE_FIELDS] = {}
        for channelIndex, note in enumerate(self.data_cache.note_fields):
            wData[defs.CFG_TAG_NOTE_FIELDS][channelIndex] = note
        wData[defs.CFG_TAG_SEQ_FIELDS] = {}
        for channelIndex, sequence in enumerate(self.data_cache.seq_fields):
            wData[defs.CFG_TAG_SEQ_FIELDS][channelIndex] = sequence

        wData[defs.CFG_TAG_RXLOG] = self.data_cache.display_rx_data
        wData[defs.CFG_TAG_TXLOG] = self.data_cache.display_tx_data
        wData[defs.CFG_TAG_OUTPUT_REPRESENTATION] = self.data_cache.output_data_representation
        wData[defs.CFG_TAG_RX_NEW_LINE] = self.data_cache.new_line_on_rx
        wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT] = self.data_cache.new_line_on_rx_timeout_msec

        with open(path, "w+", encoding="utf-8") as f:
            json.dump(wData, f, indent=4)

    def load_cfg(self, path: str) -> None:
        """
        Read (load) given json file and set new configuration.
            @param filePath: path to load file from.
        """
        with open(path, "r", encoding="utf-8") as f:
            wData = json.load(f)

        if (defs.CFG_TAG_FILE_VERSION not in wData) or (wData[defs.CFG_TAG_FILE_VERSION] != _CFG_VERSION):
            msg = "Configuration file syntax has changed - unable to set configuration."
            msg += f"\nCurrent version: {_CFG_VERSION}, config file version: {wData[defs.CFG_TAG_FILE_VERSION]}"
            raise RuntimeError(msg)

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
            self.data_cache.set_serial_settings(serialSettings)
        except KeyError as err:
            msg = f"Unable to set serial settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            for channel, data in wData[defs.CFG_TAG_DATA_FIELDS].items():
                self.data_cache.set_data_field(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_NOTE_FIELDS].items():
                self.data_cache.set_note_field(int(channel), data)

            for channel, data in wData[defs.CFG_TAG_SEQ_FIELDS].items():
                self.data_cache.set_seq_field(int(channel), data)
        except KeyError as err:
            msg = f"Unable to set data/note/sequence settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            self.data_cache.set_rx_display_ode(wData[defs.CFG_TAG_RXLOG])
            self.data_cache.set_tx_display_mode(wData[defs.CFG_TAG_TXLOG])
            self.data_cache.set_output_representation_mode(wData[defs.CFG_TAG_OUTPUT_REPRESENTATION])
            self.data_cache.set_new_line_on_rx_mode(wData[defs.CFG_TAG_RX_NEW_LINE])
            self.data_cache.set_new_line_on_rx_timeout(wData[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT])
        except KeyError as err:
            msg = f"Unable to set log settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

    def set_default_cfg(self) -> None:
        """
        Set instance of data model with default values.
        Will emit signals to update GUI.
        """
        self.data_cache.set_serial_settings(serial_hdlr.SerialCommSettings())
        for channel in range(defs.NUM_OF_DATA_CHANNELS):
            self.data_cache.set_data_field(channel, "")
            self.data_cache.set_note_field(channel, "")

        for channel in range(defs.NUM_OF_SEQ_CHANNELS):
            self.data_cache.set_seq_field(channel, "")

        self.data_cache.set_rx_display_ode(True)
        self.data_cache.set_tx_display_mode(True)
        self.data_cache.set_output_representation_mode(defs.OutputRepresentation.STRING)
        self.data_cache.set_new_line_on_rx_mode(False)
