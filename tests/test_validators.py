from typing import List
import pytest

from serial_tool import defines as defs
from serial_tool import models
from serial_tool import validators


@pytest.mark.parametrize(
    "data_in,data_out",
    [
        ("0", [0]),
        ("1; -128; -127; 255; 0", [1, 128, 129, 255, 0]),  # note two's complement
        ("0x0; 0x1; 0X2; 0x123456789", [0, 1, 2] + list(bytearray.fromhex("0123456789"))),
        ('"a"; "A"; "ABCD"', [ord("a"), ord("A"), ord("A"), ord("B"), ord("C"), ord("D")]),
        # special cases
        ('1; 0x2; "aBc"', [1, 2, ord("a"), ord("B"), ord("c")]),  # mixed values
        (' 1 ; 0x2    ; "aBc";     ', [1, 2, ord("a"), ord("B"), ord("c")]),  # spaces, extra end char
    ],
)
def test_parse_channel_data_valid(data_in: str, data_out: List[int]) -> None:
    result = validators.parse_channel_data(data_in)
    assert result.status == models.TextFieldStatus.OK, result.msg

    assert len(result.data) == len(data_out)
    assert result.data == data_out


@pytest.mark.parametrize(
    "data_in, msg",
    [
        ("1 2", "No separator"),
        ("1; 2 3; 4", "No separator #2"),
        ("1, 2, 3", "Invalid separator"),
        ("1; !}", "Invalid character"),
        ("-255", "Out of range"),
        ("256", "Out of range"),
    ],
)
def test_parse_channel_data_invalid_format(data_in: str, msg: str) -> None:
    result = validators.parse_channel_data(data_in)
    assert result.status == models.TextFieldStatus.BAD, f"Expected fail: {msg}\n{result.msg}"


@pytest.mark.parametrize(
    "data_in,data_out",
    [
        ("(1, 2)", [defs.SequenceInfo(0, 2)]),
        ("(2, 3, 4)", [defs.SequenceInfo(1, 3, 4)]),
        ("(1, 2); (2, 3, 4)", [defs.SequenceInfo(0, 2), defs.SequenceInfo(1, 3, 4)]),
        # special cases
        ("( 1   , 2    );   ", [defs.SequenceInfo(0, 2)]),  # allow extra spaces end char
    ],
)
def test_parse_seq_data_valid(data_in: str, data_out: List[defs.SequenceInfo]) -> None:
    result = validators.parse_seq_data(data_in)
    assert result.status == models.TextFieldStatus.OK, result.msg

    assert len(result.data) == len(data_out)
    for idx, data in enumerate(data_out):
        result_data = result.data[idx]
        assert result_data.channel_idx == data.channel_idx
        assert result_data.delay_msec == data.delay_msec
        assert result_data.repeat == data.repeat


@pytest.mark.parametrize(
    "data_in, msg",
    [
        ("1,2", "No start/end char"),
        ("{1, 2,}", "Invalid start/end char"),
        ("()", "No minimum required data"),
        ("(1)", "No minimum required data (delay)"),
        ("(, )", "No minimum required data (channel idx)"),
        ("(1, 2, 3, 4)", "To much data"),
        ("(1, 2), (1, 2)", "Invalid block separator character"),
        ("(1,a)", "'a' is not an int"),
        ('(1,"a")', "'a' is not an int"),
        ("(1,'a')", "'a' is not an int"),
        ('(1,"a")', "'a' is not an int"),
    ],
)
def test_parse_seq_data_invalid_format(data_in: str, msg: str) -> None:
    result = validators.parse_seq_data(data_in)
    assert result.status == models.TextFieldStatus.BAD, f"Expected fail: {msg}\n{result.msg}"
