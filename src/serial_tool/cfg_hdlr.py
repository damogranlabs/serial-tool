import json

from serial_tool import defines as defs
from serial_tool.base import user_cfg_defs
from serial_tool import models
from serial_tool import serial_hdlr

_CFG_VERSION = 2.0  # configuration file version (not main software version)


class ConfigurationHdlr:
    def __init__(self, data_cache: models.RuntimeDataCache, signals: models.SharedSignalsContainer) -> None:
        """Handler of user config data (channels, notes, sequences) and save/load actions"""
        self.data_cache = data_cache
        self.signals = signals

    def save_cfg(self, path: str) -> None:
        """Overwrite data with current settings in a json format."""
        data = {}
        data[user_cfg_defs.KEY_FILE_VER] = _CFG_VERSION

        ser_cfg_data = {}
        ser_cfg_data[user_cfg_defs.KEY_SER_PORT] = self.data_cache.serial_settings.port
        ser_cfg_data[user_cfg_defs.KEY_SER_BAUDRATE] = self.data_cache.serial_settings.baudrate
        ser_cfg_data[user_cfg_defs.KEY_SER_DATASIZE] = self.data_cache.serial_settings.data_size
        ser_cfg_data[user_cfg_defs.KEY_SER_STOPBITS] = self.data_cache.serial_settings.stop_bits
        ser_cfg_data[user_cfg_defs.KEY_SER_PARITY] = self.data_cache.serial_settings.parity
        ser_cfg_data[user_cfg_defs.KEY_SER_SWFLOWCTRL] = self.data_cache.serial_settings.sw_flow_ctrl
        ser_cfg_data[user_cfg_defs.KEY_SER_HWFLOWCTRL] = self.data_cache.serial_settings.hw_flow_ctrl
        ser_cfg_data[user_cfg_defs.KEY_SER_RX_TIMEOUT_MS] = self.data_cache.serial_settings.rx_timeout_ms
        ser_cfg_data[user_cfg_defs.KEY_SER_TX_TIMEOUT] = self.data_cache.serial_settings.tx_timeout_ms
        data[user_cfg_defs.KEY_SER_CFG] = ser_cfg_data

        data[user_cfg_defs.KEY_GUI_DATA_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.data_fields):
            data[user_cfg_defs.KEY_GUI_DATA_FIELDS][idx] = field
        data[user_cfg_defs.KEY_GUI_NOTE_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.note_fields):
            data[user_cfg_defs.KEY_GUI_NOTE_FIELDS][idx] = field
        data[user_cfg_defs.KEY_GUI_SEQ_FIELDS] = {}
        for idx, field in enumerate(self.data_cache.seq_fields):
            data[user_cfg_defs.KEY_GUI_SEQ_FIELDS][idx] = field

        data[user_cfg_defs.KEY_GUI_RX_LOG] = self.data_cache.display_rx_data
        data[user_cfg_defs.KEY_GUI_TX_LOG] = self.data_cache.display_tx_data
        data[user_cfg_defs.KEY_GUI_OUT_REPRESENTATION] = self.data_cache.output_data_representation
        data[user_cfg_defs.KEY_GUI_RX_NEWLINE] = self.data_cache.new_line_on_rx
        data[user_cfg_defs.KEY_GUI_RX_NEWLINE_TIMEOUT] = self.data_cache.new_line_on_rx_timeout_msec

        with open(path, "w+", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_cfg(self, path: str) -> None:
        """Read (load) given json file and set new configuration."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if (user_cfg_defs.KEY_FILE_VER not in data) or (data[user_cfg_defs.KEY_FILE_VER] != _CFG_VERSION):
            msg = "Configuration file syntax has changed - unable to set configuration."
            msg += f"\nCurrent version: {_CFG_VERSION}, config file version: {data[user_cfg_defs.KEY_FILE_VER]}"
            raise RuntimeError(msg)

        try:
            settings = serial_hdlr.SerialCommSettings()
            ser_cfg_data = data[user_cfg_defs.KEY_SER_CFG]
            settings.port = ser_cfg_data[user_cfg_defs.KEY_SER_PORT]
            cfg_baudrate = ser_cfg_data[user_cfg_defs.KEY_SER_BAUDRATE]
            if cfg_baudrate is None:
                settings.baudrate = defs.DEFAULT_BAUDRATE
            else:
                settings.baudrate = cfg_baudrate
            settings.data_size = ser_cfg_data[user_cfg_defs.KEY_SER_DATASIZE]
            settings.stop_bits = ser_cfg_data[user_cfg_defs.KEY_SER_STOPBITS]
            settings.parity = ser_cfg_data[user_cfg_defs.KEY_SER_PARITY]
            settings.sw_flow_ctrl = ser_cfg_data[user_cfg_defs.KEY_SER_SWFLOWCTRL]
            settings.hw_flow_ctrl = ser_cfg_data[user_cfg_defs.KEY_SER_HWFLOWCTRL]
            settings.rx_timeout_ms = ser_cfg_data[user_cfg_defs.KEY_SER_RX_TIMEOUT_MS]
            settings.tx_timeout_ms = ser_cfg_data[user_cfg_defs.KEY_SER_TX_TIMEOUT]
            self.data_cache.set_serial_settings(settings)
        except KeyError as err:
            msg = f"Unable to set serial settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            for idx, field in data[user_cfg_defs.KEY_GUI_DATA_FIELDS].items():
                self.data_cache.set_data_field(int(idx), field)

            for idx, field in data[user_cfg_defs.KEY_GUI_NOTE_FIELDS].items():
                self.data_cache.set_note_field(int(idx), field)

            for idx, field in data[user_cfg_defs.KEY_GUI_SEQ_FIELDS].items():
                self.data_cache.set_seq_field(int(idx), field)
        except KeyError as err:
            msg = f"Unable to set data/note/sequence settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

        try:
            self.data_cache.set_rx_display_ode(data[user_cfg_defs.KEY_GUI_RX_LOG])
            self.data_cache.set_tx_display_mode(data[user_cfg_defs.KEY_GUI_TX_LOG])
            self.data_cache.set_output_representation_mode(data[user_cfg_defs.KEY_GUI_OUT_REPRESENTATION])
            self.data_cache.set_new_line_on_rx_mode(data[user_cfg_defs.KEY_GUI_RX_NEWLINE])
            self.data_cache.set_new_line_on_rx_timeout(data[user_cfg_defs.KEY_GUI_RX_NEWLINE_TIMEOUT])
        except KeyError as err:
            msg = f"Unable to set log settings from a configuration file: {err}"
            self.signals.warning.emit(msg, defs.LOG_COLOR_WARNING)

    def set_default_cfg(self) -> None:
        """
        Set instance of data model with default values.
        Will emit signals to update GUI.
        """
        self.data_cache.set_serial_settings(self.data_cache.serial_settings)
        for idx in range(defs.NUM_OF_DATA_CHANNELS):
            self.data_cache.set_data_field(idx, "")
            self.data_cache.set_note_field(idx, "")

        for idx in range(defs.NUM_OF_SEQ_CHANNELS):
            self.data_cache.set_seq_field(idx, "")

        self.data_cache.set_rx_display_ode(True)
        self.data_cache.set_tx_display_mode(True)
        self.data_cache.set_output_representation_mode(models.OutputRepresentation.STRING)
        self.data_cache.set_new_line_on_rx_mode(False)
