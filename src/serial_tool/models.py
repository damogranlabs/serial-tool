import enum
from typing import Generic, List, Optional, TypeVar

from serial_tool import defines as defs


class TextFieldStatus(enum.Enum):
    OK = "valid"
    BAD = "invalid"
    EMPTY = "no content"

    @staticmethod
    def get_color(status: "TextFieldStatus") -> str:
        if status == TextFieldStatus.OK:
            return defs.INPUT_VALID_COLOR
        elif status == TextFieldStatus.BAD:
            return defs.INPUT_ERROR_COLOR
        elif status == TextFieldStatus.EMPTY:
            return defs.INPUT_NONE_COLOR
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


class SequenceTextFieldParserResult(_TextFieldParserResult[List[defs.SequenceInfo]]):
    def __init__(self, status: TextFieldStatus, msg: str = "", data: Optional[List[defs.SequenceInfo]] = None) -> None:
        super().__init__(status, msg, data)
