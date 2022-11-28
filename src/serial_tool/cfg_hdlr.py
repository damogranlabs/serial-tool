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
        data = {}
        data[defs.CFG_TAG_FILE_VERSION] = _CFG_VERSION
        data[defs.CFG_TAG_SERIAL_CFG] = {}
        data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT] = self.data_cache.serial_settings.port
        data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE] = self.data_cache.serial_settings.baudrate
        data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE] = self.data_cache.serial_settings.dataSize
        data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS] = self.data_cache.serial_settings.stopbits
        data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY] = self.data_cache.serial_settings.parity
        data[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL
        ] = self.data_cache.serial_settings.swFlowControl
        data[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL
        ] = self.data_cache.serial_settings.hwFlowControl
        data[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS
        ] = self.data_cache.serial_settings.readTimeoutMs
        data[defs.CFG_TAG_SERIAL_CFG][
            defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS
        ] = self.data_cache.serial_settings.writeTimeoutMs

        data[defs.CFG_TAG_DATA_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.data_fields):
            data[defs.CFG_TAG_DATA_FIELDS][idx] = field
        data[defs.CFG_TAG_NOTE_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.note_fields):
            data[defs.CFG_TAG_NOTE_FIELDS][idx] = field
        data[defs.CFG_TAG_SEQ_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.seq_fields):
            data[defs.CFG_TAG_SEQ_FIELDS][idx] = field

        data[defs.CFG_TAG_RXLOG] = self.data_cache.display_rx_data
        data[defs.CFG_TAG_TXLOG] = self.data_cache.display_tx_data
        data[defs.CFG_TAG_OUTPUT_REPRESENTATION] = self.data_cache.output_data_representation
        data[defs.CFG_TAG_RX_NEW_LINE] = self.data_cache.new_line_on_rx
        data[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT] = self.data_cache.new_line_on_rx_timeout_msec

        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_cfg(self, path: str) -> None:
        """
        Read (load) given json file and set new configuration.
            @param filePath: path to load file from.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if (defs.CFG_TAG_FILE_VERSION not in data) or (data[defs.CFG_TAG_FILE_VERSION] != _CFG_VERSION):
            msg = "Configuration file syntax has changed - unable to set configuration."
            msg += f"\nCurrent version: {_CFG_VERSION}, config file version: {data[defs.CFG_TAG_FILE_VERSION]}"
            raise RuntimeError(msg)

        try:
            settings = serial_hdlr.SerialCommSettings()
            settings.port = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PORT]
            settings.baudrate = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_BAUDRATE]
            settings.dataSize = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_DATASIZE]
            settings.stopbits = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_STOPBITS]
            settings.parity = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_PARITY]
            settings.swFlowControl = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_SWFLOWCONTROL]
            settings.hwFlowControl = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_HWFLOWCONTROL]
            settings.readTimeoutMs = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_READTIMEOUTMS]
            settings.writeTimeoutMs = data[defs.CFG_TAG_SERIAL_CFG][defs.CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS]
            self.data_cache.set_serial_settings(settings)
        except KeyError as err:
            msg = f"Unable to set serial settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            for idx, field in data[defs.CFG_TAG_DATA_FIELDS].items():
                self.data_cache.set_data_field(int(idx), field)

            for idx, field in data[defs.CFG_TAG_NOTE_FIELDS].items():
                self.data_cache.set_note_field(int(idx), field)

            for idx, field in data[defs.CFG_TAG_SEQ_FIELDS].items():
                self.data_cache.set_seq_field(int(idx), field)
        except KeyError as err:
            msg = f"Unable to set data/note/sequence settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            self.data_cache.set_rx_display_ode(data[defs.CFG_TAG_RXLOG])
            self.data_cache.set_tx_display_mode(data[defs.CFG_TAG_TXLOG])
            self.data_cache.set_output_representation_mode(data[defs.CFG_TAG_OUTPUT_REPRESENTATION])
            self.data_cache.set_new_line_on_rx_mode(data[defs.CFG_TAG_RX_NEW_LINE])
            self.data_cache.set_new_line_on_rx_timeout(data[defs.CFG_TAG_RX_NEW_LINE_TIMEOUT])
        except KeyError as err:
            msg = f"Unable to set log settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

    def set_default_cfg(self) -> None:
        """
        Set instance of data model with default values.
        Will emit signals to update GUI.
        """
        self.data_cache.set_serial_settings(serial_hdlr.SerialCommSettings())
        for idx in range(defs.NUM_OF_DATA_CHANNELS):
            self.data_cache.set_data_field(idx, "")
            self.data_cache.set_note_field(idx, "")

        for idx in range(defs.NUM_OF_SEQ_CHANNELS):
            self.data_cache.set_seq_field(idx, "")

        self.data_cache.set_rx_display_ode(True)
        self.data_cache.set_tx_display_mode(True)
        self.data_cache.set_output_representation_mode(models.OutputRepresentation.STRING)
        self.data_cache.set_new_line_on_rx_mode(False)
