import argparse
import logging


class SerialToolArgs:
    def __init__(self, log_level=logging.DEBUG, load_mru_cfg: bool = False):
        self.log_level = log_level
        self.load_mru_cfg = load_mru_cfg

    @staticmethod
    def parse() -> "SerialToolArgs":
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--log-level", type=str, default="DEBUG", required=False, help="Optionally set logging level."
        )
        parser.add_argument(
            "--load-mru-cfg",
            action="store_true",
            required=False,
            help="If present, most recently used configuration is loaded on startup, if available.",
        )

        args = parser.parse_args()

        levels = logging.getLevelNamesMapping()
        if args.log_level not in levels:
            raise ValueError(f"`{args.log_level}` is not a valid log level. Must be any of: {levels.keys()}")
        return SerialToolArgs(levels[args.log_level], args.load_mru_cfg)
