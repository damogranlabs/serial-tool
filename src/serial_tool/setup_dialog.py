"""
Serial setup dialog window handler.
"""
from functools import partial
from typing import Optional

import serial
from PyQt5 import QtCore, QtWidgets

from serial_tool.gui.serialSetupDialog import Ui_SerialSetupDialog

from serial_tool import serial_hdlr


class SerialSetupDialog(QtWidgets.QDialog):
    def __init__(self, settings: Optional[serial_hdlr.SerialCommSettings] = None) -> None:
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_SerialSetupDialog()
        self.ui.setupUi(self)

        if settings is None:
            settings = serial_hdlr.SerialCommSettings()
        self.settings = settings

        self.apply_settings_on_close = False

        self._connect_signals_to_slots()

        self._set_ui_values(self.settings)

    def _connect_signals_to_slots(self) -> None:
        """
        Connect GUI to functions.
        """
        # round button data size group
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_eight, serial.EIGHTBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_seven, serial.SEVENBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_six, serial.SIXBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_five, serial.FIVEBITS)

        # round button parity group
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_none, serial_hdlr.parity_as_int(serial.PARITY_NONE))
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_even, serial_hdlr.parity_as_int(serial.PARITY_EVEN))
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_odd, serial_hdlr.parity_as_int(serial.PARITY_ODD))

        # round button stop bits group
        self.ui.RB_stopBitsGroup.setId(self.ui.RB_stopBits_one, serial.STOPBITS_ONE)
        self.ui.RB_stopBitsGroup.setId(self.ui.RB_stopBits_two, serial.STOPBITS_TWO)

        # OK/cancel buttons
        self.ui.PB_OK.clicked.connect(partial(self.on_exit, True))
        self.ui.PB_cancel.clicked.connect(partial(self.on_exit, False))

    def display(self) -> None:
        """
        Show dialog and raise it above parent widget.
        """
        self.show()
        self.raise_()

    @QtCore.pyqtSlot(bool)
    def on_exit(self, save_if_ok: bool) -> None:
        """
        On OK, store dialog settings to settings. On Cancel or close, don't do nothing.
        On exit, close dialog.
        """
        if save_if_ok:
            self._store_ui_settings()
            self.apply_settings_on_close = True

        self.close()

    def _store_ui_settings(self) -> None:
        """
        Store values from a current setup dialog into self.dialogSettings.
        """
        self.settings.hw_flow_ctrl = self.ui.CB_hwFlowCtrl.isChecked()
        self.settings.sw_flow_ctrl = self.ui.CB_swFlowCtrl.isChecked()

        self.settings.data_size = self.ui.RB_dataSizeGroup.checkedId()
        self.settings.stop_bits = self.ui.RB_stopBitsGroup.checkedId()
        parityAsNumber = self.ui.RB_parityGroup.checkedId()
        self.settings.parity = serial_hdlr.parity_as_str(parityAsNumber)

    def get_settings(self) -> serial_hdlr.SerialCommSettings:
        """
        Store and return dialog values.
        """
        return self.settings

    def must_apply_settings(self) -> bool:
        """
        Return True if dialog values must be applied, False otherwise.
        Only make sense to call this function once dialog is closed.
        """
        return self.apply_settings_on_close

    def _set_ui_values(self, serialSettings: serial_hdlr.SerialCommSettings) -> None:
        """
        Set current setup dialog settings and refresh internal self.dialogValues state.
        """
        self.ui.CB_hwFlowCtrl.setChecked(serialSettings.sw_flow_ctrl)
        self.ui.CB_swFlowCtrl.setChecked(serialSettings.hw_flow_ctrl)

        roundButton = self.ui.RB_dataSizeGroup.button(serialSettings.data_size)
        roundButton.click()

        parityAsNumber = serial_hdlr.parity_as_int(serialSettings.parity)
        roundButton = self.ui.RB_parityGroup.button(parityAsNumber)
        roundButton.click()

        roundButton = self.ui.RB_stopBitsGroup.button(serialSettings.stop_bits)
        roundButton.click()

        self._store_ui_settings()
