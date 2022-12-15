import logging
import sys
from typing import List
import pytest

from serial_tool import cmd_args


class TempCmdArgs:
    def __init__(self, args: List[str]) -> None:
        self.args = args
        self.sysargs = sys.argv.copy()

    def __enter__(self):
        sys.argv = [self.sysargs[0]] + self.args

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.argv = [self.sysargs[0]] + self.args


def test_cmd_args():
    with TempCmdArgs([]):
        args = cmd_args.SerialToolArgs.parse()
        assert args.log_level == logging.DEBUG
        assert args.load_mru_cfg == False

    with TempCmdArgs(["--load-mru-cfg"]):
        args = cmd_args.SerialToolArgs.parse()
        assert args.log_level == logging.DEBUG
        assert args.load_mru_cfg == True

    with TempCmdArgs(["--log-level=ERROR"]):
        args = cmd_args.SerialToolArgs.parse()
        assert args.log_level == logging.ERROR
        assert args.load_mru_cfg == False

    with TempCmdArgs(["--load-mru-cfg", "--log-level=ERROR"]):
        args = cmd_args.SerialToolArgs.parse()
        assert args.log_level == logging.ERROR
        assert args.load_mru_cfg == True


def test_cmd_args_invalid():
    with pytest.raises(ValueError):
        with TempCmdArgs(["--log-level=WHATEVER"]):
            cmd_args.SerialToolArgs.parse()

    with pytest.raises(SystemExit):
        with TempCmdArgs(["--invalid"]):
            cmd_args.SerialToolArgs.parse()
