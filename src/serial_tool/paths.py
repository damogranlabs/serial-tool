import logging
import os
from functools import lru_cache
from typing import List, Optional

import serial_tool.defines as defs


@lru_cache
def get_default_log_dir() -> str:
    """
    Return path to a default Serial Tool log directory in Appdata:
        %APPDATA%/<SERIAL_TOOL_APPDATA_FOLDER_NAME>
    """
    return os.path.join(os.environ["APPDATA"], defs.SERIAL_TOOL_APPDATA_FOLDER_NAME)


@lru_cache
def get_log_file_path() -> str:
    """
    Return path to a default Serial Tool log file.
    """
    return os.path.join(get_default_log_dir(), defs.SERIAL_TOOL_LOG_FILENAME)


@lru_cache
def get_recently_used_cfg_cache_file() -> str:
    """
    Return path to a RECENTLY_USED_CFG_FILE_NAME which is, by default stored in log folder.
    """
    return os.path.join(get_default_log_dir(), defs.RECENTLY_USED_CFG_FILE_NAME)


def get_most_recently_used_cfg_file() -> Optional[str]:
    """
    Get the most recently used configuration.
    Return None if file does not exist or it is empty.
    """
    file_paths = get_recently_used_cfgs(1)
    if file_paths:
        return file_paths[0]
    else:
        return None


def add_cfg_to_recently_used_cfgs(file_path: str) -> None:
    """
    Add entry (insert at position 0, first line) given configuration file path
    to a list of recently used configurations.
    """

    def _write_fresh(path: str, data: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)

    file_path = os.path.abspath(file_path)

    write_fresh = False
    ruc_file_path = get_recently_used_cfg_cache_file()
    if os.path.exists(ruc_file_path):
        try:
            with open(ruc_file_path, "r+", encoding="utf-8") as f:
                lines = f.readlines()

                lines.insert(0, f"{file_path}\n")
                lines = list(dict.fromkeys(lines))  # remove duplicates
                lines = lines[defs.MAX_NUM_OF_RECENTLY_USED_CFGS :]  # shorten number of entries

                f.seek(0)  # strange \x00 appeared without this
                f.truncate(0)
                f.writelines(lines)
        except PermissionError as err:
            logging.warning(f"Error while reading/writing/parsing recently used cfgs file:\n{err}")
            write_fresh = True
    else:
        write_fresh = True

    if write_fresh:
        try:
            logging.info(f"Writing new recently used cfgs file: {ruc_file_path}")
            _write_fresh(ruc_file_path, f"{file_path}\n")
        except PermissionError as err:
            logging.warning(f"Unable to create new recently used cfgs file. No further attempts.\n{err}")


def get_recently_used_cfgs(number: int) -> List[str]:
    """
    Get a list of last 'number' of valid entries (existing files) of recently used configurations.
        @param number: number of  max recently used configuration file paths to return.
    """
    ruc_file_path = get_recently_used_cfg_cache_file()

    file_paths: List[str] = []
    if os.path.exists(ruc_file_path):
        try:
            with open(ruc_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                file_paths = []
                for line in lines:
                    line = line.strip()
                    if os.path.exists(line):
                        file_paths.append(line)

                return file_paths[:number]
        except PermissionError as err:
            logging.warning(f"Unable to get most recently used configurations from file: {ruc_file_path}\n{err}")

    return file_paths
