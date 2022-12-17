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
        """Show dialog and raise it above parent widget."""
        self.show()
        self.raise_()

    @QtCore.pyqtSlot(bool)
    def on_exit(self, save_if_ok: bool) -> None:
        """
        On OK, store dialog settings to settings.
        On Cancel or close, don't do nothing.
        On Exit, close the dialog.
        """
        if save_if_ok:
            self._store_ui_settings()
            self.apply_settings_on_close = True

        self.close()

    def _store_ui_settings(self) -> None:
        """Save current setup dialog values from GUI fields."""
        self.settings.hw_flow_ctrl = self.ui.CB_hwFlowCtrl.isChecked()
        self.settings.sw_flow_ctrl = self.ui.CB_swFlowCtrl.isChecked()

        self.settings.data_size = self.ui.RB_dataSizeGroup.checkedId()
        self.settings.stop_bits = self.ui.RB_stopBitsGroup.checkedId()
        self.settings.parity = serial_hdlr.parity_as_str(self.ui.RB_parityGroup.checkedId())

    def get_settings(self) -> serial_hdlr.SerialCommSettings:
        return self.settings

    def must_apply_settings(self) -> bool:
        """
        Return True if dialog values must be applied, False otherwise.
        Only make sense to call this function once dialog is closed.
        """
        return self.apply_settings_on_close

    def _set_ui_values(self, settings: serial_hdlr.SerialCommSettings) -> None:
        """Set dialog values from a given settings values"""
        self.ui.CB_hwFlowCtrl.setChecked(settings.sw_flow_ctrl)
        self.ui.CB_swFlowCtrl.setChecked(settings.hw_flow_ctrl)

        round_button = self.ui.RB_dataSizeGroup.button(settings.data_size)
        round_button.click()

        parity_as_num = serial_hdlr.parity_as_int(settings.parity)
        round_button = self.ui.RB_parityGroup.button(parity_as_num)
        round_button.click()

        round_button = self.ui.RB_stopBitsGroup.button(settings.stop_bits)
        round_button.click()

        self._store_ui_settings()
