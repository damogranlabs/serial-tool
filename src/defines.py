"""
This file holds definitions of default serial tool settings, strings and internal data values.
"""


class OutputRepresentation:
    STRING = 0
    INT_LIST = 1
    HEX_LIST = 2
    ASCII_LIST = 3


class SequenceData:
    def __init__(self, channelIndex: int = None, delayMS: int = 0, repeat: int = 1):
        """
        Each item in sequence field list is of this type and holds 
            @param channelIndex: index of data channel index as described in GUI fields
            @param delayMS: delay after this channel data is sent in milliseconds.
            @param repeat: number of times this channel is sent with given data and delay
        """
        self.channelIndex: int = channelIndex
        self.delayMS: int = delayMS
        self.repeat: int = repeat

    def __str__(self):
        seqAsString = f"({self.channelIndex}{SEQ_BLOCK_DATA_SEPARATOR}{self.delayMS}{SEQ_BLOCK_DATA_SEPARATOR}{self.repeat})"
        return seqAsString


###################################################################################################
# default serial settings
DEFAULT_BAUDRATE = 115200
SERIAL_READ_TIMEOUT_MS = 300
SERIAL_WRITE_TIMEOUT_MS = 300

###################################################################################################
# links
LINK_DAMOGRANLABS = "http://damogranlabs.com/"
LINK_HOMEPAGE = "https://damogranlabs.com/2017/05/serial-tool/"
LINK_GITHUB = "https://github.com/damogranlabs/serial-tool/"
LINK_GITHUB_DOCS = "https://github.com/damogranlabs/serial-tool/blob/master/README.md"
LINK_SOURCEFORGE = "http://sourceforge.net/p/serial-tool/"

###################################################################################################
# colors
_RED = "#d45353"
_GREEN = "#9dff96"
_ORANGE = "#f5881b"

DAMOGRANLABS_BLUE_COLOR = "#4f7fd7"
DAMOGRANLABS_GRAY_COLOR = "#646464"

COMM_PORT_CONNECTED_COLOR = _GREEN
COMM_PORT_NOT_CONNECTED_COLOR = _RED

SEQ_ACTIVE_COLOR = _ORANGE
INPUT_VALID_COLOR = _GREEN
INPUT_NONE_COLOR = "None"
INPUT_ERROR_COLOR = _RED
LOG_COLOR_NORMAL = "#000000"
LOG_COLOR_GRAY = DAMOGRANLABS_GRAY_COLOR
LOG_COLOR_ERROR = "#FF0000"
LOG_COLOR_WARNING = "#ff8000"  # orange
RX_DATA_LOG_COLOR = DAMOGRANLABS_GRAY_COLOR
TX_DATA_LOG_COLOR = DAMOGRANLABS_BLUE_COLOR

###################################################################################################
# button strings
COMM_PORT_CONNECTED_TEXT = "CONNECTED"
COMM_PORT_NOT_CONNECTED_TEXT = "not connected"

SEQ_BUTTON_START_TEXT = "SEND SEQUENCE"
SEQ_BUTTON_STOP_TEXT = "STOP SEQUENCE"

###################################################################################################
# log/window tags and separation strings
TX_TAG = "TX"
RX_TAG = "RX"
SEQ_TAG = "SEQ"
RX_CHANNEL_TAG = "CH"
TX_CHANNEL_TAG = "CH"
EXPORT_RX_TAG = "   <-- "  # added spaces at the beginning, to align with tx channel syntax (example: CH0)
EXPORT_TX_TAG = "--> "
RX_DATA_LIST_SEPARATOR = "; "
TX_DATA_LIST_SEPARATOR = "; "
DATA_BYTES_SEPARATOR = ";"

SEQ_BLOCK_SEPARATOR = ";"
SEQ_BLOCK_DATA_SEPARATOR = ","
SEQ_BLOCK_START_CHARACTER = "("
SEQ_BLOCK_END_CHARACTER = ")"


###################################################################################################
# configuration file tags
CFG_TAG_FILE_VERSION = "version"
CFG_TAG_SERIAL_CFG = "serialSettings"
CFG_TAG_SERIAL_CFG_PORT = "port"
CFG_TAG_SERIAL_CFG_BAUDRATE = "baudrate"
CFG_TAG_SERIAL_CFG_DATASIZE = "dataSize"
CFG_TAG_SERIAL_CFG_STOPBITS = "stopbits"
CFG_TAG_SERIAL_CFG_PARITY = "parity"
CFG_TAG_SERIAL_CFG_SWFLOWCONTROL = "swFlowControl"
CFG_TAG_SERIAL_CFG_HWFLOWCONTROL = "hwFlowControl"
CFG_TAG_SERIAL_CFG_READTIMEOUTMS = "readTimeoutMs"
CFG_TAG_SERIAL_CFG_WRITETIMEOUTMS = "writeTimeoutMs"
CFG_TAG_DATA_FIELDS = "dataFields"
CFG_TAG_NOTE_FIELDS = "noteFields"
CFG_TAG_SEQ_FIELDS = "sequenceFields"
CFG_TAG_RXLOG = "rxToLog"
CFG_TAG_TXLOG = "txToLog"
CFG_TAG_OUTPUT_REPRESENTATION = "outputDataRepresentation"
CFG_TAG_VERBOSE_DISPLAY = "verboseDataDisplay"

MAX_NUM_OF_RECENTLY_USED_CFGS = 20

###################################################################################################
# extensions
CFG_FILE_EXTENSION_FILTER = "*.json"
LOG_EXPORT_FILE_EXTENSION_FILTER = "*.log"
DATA_EXPORT_FILE_EXTENSION_FILTER = "*.log"

###################################################################################################
# default paths and file names
SERIAL_TOOL_APPDATA_FOLDER_NAME = "SerialTool"
SERIAL_TOOL_LOG_FILENAME = "SerialToolLog.log"
DEFAULT_CFG_FILE_NAME = "SerialToolCfg.json"
DEFAULT_LOG_EXPORT_FILENAME = "logWindow.log"
DEFAULT_DATA_EXPORT_FILENAME = "rxTxData.log"
RECENTLY_USED_CFG_FILE_NAME = "_recentlyUsedConfigurations.txt"

###################################################################################################
# other settings
DEFAULT_FONT_STYLE = "font-size: 10pt;"
NUM_OF_MAX_RECENTLY_USED_CFG_GUI = 8

NUM_OF_DATA_CHANNELS = 8
NUM_OF_SEQ_CHANNELS = 3
