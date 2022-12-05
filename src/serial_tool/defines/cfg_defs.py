CFG_FORMAT_VERSION = 2.0  # configuration file format version (not main software version)

# Configuration data JSON keys
# TODO: switch to pydantic models one day
KEY_FILE_VER = "version"

KEY_SER_CFG = "serialSettings"
KEY_SER_PORT = "port"
KEY_SER_BAUDRATE = "baudrate"
KEY_SER_DATASIZE = "dataSize"
KEY_SER_STOPBITS = "stopbits"
KEY_SER_PARITY = "parity"
KEY_SER_SWFLOWCTRL = "swFlowControl"
KEY_SER_HWFLOWCTRL = "hwFlowControl"
KEY_SER_RX_TIMEOUT_MS = "readTimeoutMs"
KEY_SER_TX_TIMEOUT = "writeTimeoutMs"

KEY_GUI_DATA_FIELDS = "dataFields"
KEY_GUI_NOTE_FIELDS = "noteFields"
KEY_GUI_SEQ_FIELDS = "sequenceFields"
KEY_GUI_RX_LOG = "rxToLog"
KEY_GUI_TX_LOG = "txToLog"
KEY_GUI_OUT_REPRESENTATION = "outputDataRepresentation"
KEY_GUI_RX_NEWLINE = "newLineOnRxData"
KEY_GUI_RX_NEWLINE_TIMEOUT = "newLineOnRxTimeout"
