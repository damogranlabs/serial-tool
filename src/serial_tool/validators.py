import sys
from typing import List

from serial_tool.defines import ui_defs
from serial_tool import models


def parse_channel_data(text: str) -> models.ChannelTextFieldParserResult:
    """
    Get string from a data field and return a tuple:
        - on success: True, [<valid data bytes to send>]
        - on empty string: None, ''
        - on error: False, <current string>

        @param ch: sequence channel selector: 0 - 7
    """
    text = text.strip()
    if text == "":
        return models.ChannelTextFieldParserResult(models.TextFieldStatus.EMPTY)

    data = []

    try:
        parts = text.strip(ui_defs.DATA_BYTES_SEPARATOR).split(ui_defs.DATA_BYTES_SEPARATOR)
        for part in parts:
            part = part.strip()

            # handle HEX numbers (can be one or more bytes)
            if part.lower().startswith("0x"):
                part = part.lower()[2:]
                if not part:  # `0x` and nothing after
                    return models.ChannelTextFieldParserResult(
                        models.TextFieldStatus.BAD, f"HEX data format detected, but no value specified: {text}"
                    )
                if len(part) % 2:
                    part = "0" + part
                hex_numbers = list(bytearray.fromhex(part))
                data.extend(hex_numbers)
                continue

            # character (enclosed in "<one or more characters>")
            if part.startswith('"') and part.endswith('"'):
                part = part.strip('"')
                for char in part:
                    int_value = ord(char)
                    _check_number_in_range(int_value)
                    data.append(int_value)
                continue

            # number
            if part.isdigit() or part.startswith("-"):
                int_value = int(part)
                _check_number_in_range(int_value)
                # if negative number, create two's complement
                if int_value < 0:
                    byta_value = int_value.to_bytes(1, byteorder=sys.byteorder, signed=True)
                    uint = int.from_bytes(byta_value, byteorder=sys.byteorder, signed=False)
                else:
                    uint = int_value
                data.append(uint)
                continue

            return models.ChannelTextFieldParserResult(
                models.TextFieldStatus.BAD, f"Channel data format/values not valid: {text}"
            )

    except ValueError as err:
        return models.ChannelTextFieldParserResult(
            models.TextFieldStatus.BAD, f"Unable to parse given channel data: {text}\n{err}"
        )

    return models.ChannelTextFieldParserResult(models.TextFieldStatus.OK, data=data)


def _check_number_in_range(num: int) -> None:
    """
    Raise ValueError if given number is not within possible values of 1 byte
        - Number is signed char (as int8_t): -128 <= number <= +127
        - Number is unsigned char (as uint8_t): 0 <= number <= 255
    False otherwise.
    """
    if not (-128 <= num <= 255):
        raise ValueError(f"Number {num} is not within allowed range (-128 ... 255){'.'}")


def parse_seq_data(text: str) -> models.SequenceTextFieldParserResult:
    """Parse sequence data string."""
    text = text.strip()

    if text == "":
        return models.SequenceTextFieldParserResult(models.TextFieldStatus.EMPTY)

    parsed_blocks_data: List[models.SequenceInfo] = []
    blocks = text.strip(ui_defs.SEQ_BLOCK_SEPARATOR).split(ui_defs.SEQ_BLOCK_SEPARATOR)
    for block in blocks:
        block = block.strip()

        try:
            if not (block.startswith(ui_defs.SEQ_BLOCK_START_CHAR) and block.endswith(ui_defs.SEQ_BLOCK_END_CHAR)):
                return models.SequenceTextFieldParserResult(
                    models.TextFieldStatus.BAD,
                    f"Invalid format, expecting '{ui_defs.SEQ_BLOCK_START_CHAR}' and '{ui_defs.SEQ_BLOCK_END_CHAR}' "
                    f"separators in block: {block}",
                )

            block = block.strip(ui_defs.SEQ_BLOCK_START_CHAR).strip(ui_defs.SEQ_BLOCK_END_CHAR)
            data = block.split(ui_defs.SEQ_BLOCK_DATA_SEPARATOR)
            data = [d for d in data if d.strip() != ""]
            # repeat number is not mandatory
            if len(data) not in [2, 3]:
                return models.SequenceTextFieldParserResult(
                    models.TextFieldStatus.BAD,
                    f"Invalid format, expecting two or three fields: channel index, delay[, repeat]. "
                    f"Block: {block}",
                )

            ch_idx = int(data[0].strip())
            # user must enter a number as seen in GUI, starts with 1
            if not (1 <= ch_idx <= ui_defs.NUM_OF_DATA_CHANNELS):
                return models.SequenceTextFieldParserResult(
                    models.TextFieldStatus.BAD,
                    f"Invalid data channel index in sequence: {ch_idx}, block: {block}",
                )

            ch_idx = ch_idx - 1
            delay_msec = int(data[1].strip())
            if delay_msec < 0:
                return models.SequenceTextFieldParserResult(
                    models.TextFieldStatus.BAD,
                    f"Invalid delay, must be a positive number: {delay_msec}, block: {block}",
                )

            seq_data = models.SequenceInfo(ch_idx, delay_msec)
            if len(data) == 3:  # repeat is specified
                repeat_num = int(data[2].strip())
                if repeat_num < 1:
                    return models.SequenceTextFieldParserResult(
                        models.TextFieldStatus.BAD,
                        f"Invalid 'repeat' number, must be a positive number: {repeat_num}, block: {block}",
                    )
                seq_data.repeat = repeat_num

            parsed_blocks_data.append(seq_data)
            continue

        except ValueError as err:
            return models.SequenceTextFieldParserResult(
                models.TextFieldStatus.BAD, f"Unable to parse given field as sequence data: {text}\n{err}"
            )

    return models.SequenceTextFieldParserResult(models.TextFieldStatus.OK, data=parsed_blocks_data)
