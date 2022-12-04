import enum
from typing import Generic, List, Optional, TypeVar

from PyQt5 import QtCore

from serial_tool import defines as defs
from serial_tool.base import colors
from serial_tool import serial_hdlr


class OutputRepresentation(enum.IntEnum):
    STRING = 0
    INT_LIST = 1
    HEX_LIST = 2
    ASCII_LIST = 3


class SequenceInfo:
    def __init__(self, channel_idx: int, delay_msec: int = 0, repeat: int = 1):
        """
        Each item in sequence field list is of this type and holds
            @param channel_idx: index of data channel index as described in GUI fields
            @param delay_msec: delay after this channel data is sent in milliseconds.
            @param repeat: number of times this channel is sent with given data and delay
        """
        self.channel_idx: int = channel_idx
        self.delay_msec: int = delay_msec
        self.repeat: int = repeat

    def __str__(self):
        return f"({self.channel_idx}{defs.SEQ_BLOCK_DATA_SEPARATOR}{self.delay_msec}{defs.SEQ_BLOCK_DATA_SEPARATOR}{self.repeat})"


class TextFieldStatus(enum.Enum):
    OK = "valid"
    BAD = "invalid"
    EMPTY = "no content"

    @staticmethod
    def get_color(status: "TextFieldStatus") -> str:
        if status == TextFieldStatus.OK:
            return colors.INPUT_VALID
        elif status == TextFieldStatus.BAD:
            return colors.INPUT_ERROR
        elif status == TextFieldStatus.EMPTY:
            return colors.INPUT_NONE
        else:
            raise ValueError(f"Unable to determine color for status: {status}")


T_DATA_TYPE = TypeVar("T_DATA_TYPE")


class _TextFieldParserResult(Generic[T_DATA_TYPE]):
    def __init__(self, status: TextFieldStatus, msg: str = "", data: Optional[T_DATA_TYPE] = None) -> None:
        self.status = status
        self.msg = msg

        self._data = data

    @property
    def data(self) -> T_DATA_TYPE:
        assert self._data is not None

        return self._data


class ChannelTextFieldParserResult(_TextFieldParserResult[List[int]]):
    def __init__(self, status: TextFieldStatus, msg: str = "", data: Optional[List[int]] = None) -> None:
        super().__init__(status, msg, data)


class SequenceTextFieldParserResult(_TextFieldParserResult[List[SequenceInfo]]):
    def __init__(self, status: TextFieldStatus, msg: str = "", data: Optional[List[SequenceInfo]] = None) -> None:
        super().__init__(status, msg, data)


class SharedSignalsContainer:
    def __init__(
        self, write: QtCore.pyqtBoundSignal, warning: QtCore.pyqtBoundSignal, error: QtCore.pyqtBoundSignal
    ) -> None:
        self.write = write
        self.warning = warning
        self.sigError = error


class RuntimeDataCache(QtCore.QObject):
    sig_serial_settings_update = QtCore.pyqtSignal()
    sigDataFieldUpdate = QtCore.pyqtSignal(int)
    sigNoteFieldUpdate = QtCore.pyqtSignal(int)
    sigSeqFieldUpdate = QtCore.pyqtSignal(int)
    sigRxDisplayModeUpdate = QtCore.pyqtSignal()
    sigTxDisplayModeUpdate = QtCore.pyqtSignal()
    sigOutputRepresentationModeUpdate = QtCore.pyqtSignal()
    sigRxNewLineUpdate = QtCore.pyqtSignal()
    sigRxNewLineTimeoutUpdate = QtCore.pyqtSignal()

    def __init__(self) -> None:
        """Main shared data object."""
        super().__init__()

        self.serial_settings = serial_hdlr.SerialCommSettings()

        self.cfg_file_path: Optional[str] = None

        self.data_fields: List[str] = [""] * defs.NUM_OF_DATA_CHANNELS
        self.parsed_data_fields: List[Optional[List[int]]] = [None] * defs.NUM_OF_DATA_CHANNELS
        self.note_fields: List[str] = [""] * defs.NUM_OF_DATA_CHANNELS

        self.seq_fields: List[str] = [""] * defs.NUM_OF_SEQ_CHANNELS
        self.parsed_seq_fields: List[Optional[List[SequenceInfo]]] = [None] * defs.NUM_OF_SEQ_CHANNELS

        self.all_rx_tx_data: List[str] = []

        self.output_data_representation = OutputRepresentation.STRING
        self.display_rx_data = True
        self.display_tx_data = True
        self.new_line_on_rx = False
        self.new_line_on_rx_timeout_msec: int = defs.DEFAULT_RX_NEWLINE_TIMEOUT_MS

    def set_serial_settings(self, settings: serial_hdlr.SerialCommSettings) -> None:
        """Update serial settings and emit a signal at the end."""
        self.serial_settings = settings
        self.sig_serial_settings_update.emit()

    def set_data_field(self, channel: int, data: str) -> None:
        """Update data field and emit a signal at the end."""
        self.data_fields[channel] = data
        self.sigDataFieldUpdate.emit(channel)

    def set_note_field(self, channel: int, data: str) -> None:
        """Update note field and emit a signal at the end."""
        self.note_fields[channel] = data
        self.sigNoteFieldUpdate.emit(channel)

    def set_seq_field(self, channel: int, data: str) -> None:
        """Update sequence field and emit a signal at the end."""
        self.seq_fields[channel] = data
        self.sigSeqFieldUpdate.emit(channel)

    def set_rx_display_ode(self, is_enabled: bool) -> None:
        """Update RX log visibility field and emit a signal at the end."""
        self.display_rx_data = is_enabled
        self.sigRxDisplayModeUpdate.emit()

    def set_tx_display_mode(self, is_enabled: bool) -> None:
        """Update TX log visibility field and emit a signal at the end."""
        self.display_tx_data = is_enabled
        self.sigTxDisplayModeUpdate.emit()

    def set_output_representation_mode(self, mode: OutputRepresentation) -> None:
        """Update output representation field and emit a signal at the end."""
        self.output_data_representation = mode
        self.sigOutputRepresentationModeUpdate.emit()

    def set_new_line_on_rx_mode(self, is_enabled: bool) -> None:
        """Update RX new line field and emit a signal at the end."""
        self.new_line_on_rx = is_enabled
        self.sigRxNewLineUpdate.emit()

    def set_new_line_on_rx_timeout(self, timeout_msec: int) -> None:
        """Update RX new line timeout field (timeout after \n is appended to next RX data)
        and emit a signal at the end."""
        self.new_line_on_rx_timeout_msec = timeout_msec
        self.sigRxNewLineTimeoutUpdate.emit()
