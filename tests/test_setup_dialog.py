import sys

import serial
from PyQt5 import QtWidgets

from serial_tool import serial_hdlr
from serial_tool import setup_dialog


def manual_test_widget() -> None:
    app = QtWidgets.QApplication(sys.argv)

    initialSerialDialogSettings = serial_hdlr.SerialCommSettings()
    initialSerialDialogSettings.swFlowControl = True
    initialSerialDialogSettings.stopbits = serial.STOPBITS_TWO
    initialSerialDialogSettings.dataSize = serial.SIXBITS

    dialog = setup_dialog.SerialSetupDialog(initialSerialDialogSettings)
    dialog.display()

    app.exec_()


if __name__ == "__main__":
    manual_test_widget()
