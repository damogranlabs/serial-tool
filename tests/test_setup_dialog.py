import sys

import serial
from PyQt5 import QtWidgets

from serial_tool import serial_hdlr
from serial_tool import setup_dialog


def manual_test_widget() -> None:
    app = QtWidgets.QApplication(sys.argv)

    init_settings = serial_hdlr.SerialCommSettings()
    init_settings.sw_flow_ctrl = True
    init_settings.stop_bits = serial.STOPBITS_TWO
    init_settings.data_size = serial.SIXBITS

    dialog = setup_dialog.SerialSetupDialog(init_settings)
    dialog.display()

    app.exec_()


if __name__ == "__main__":
    manual_test_widget()
