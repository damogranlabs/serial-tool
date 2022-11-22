"""
Serial setup dialog window handler.
"""
import sys
from functools import partial

import serial
from PyQt5 import QtCore, QtWidgets

from serial_tool.gui.serialSetupDialog import Ui_SerialSetupDialog

from serial_tool import serComm


class SerialSetupDialog(QtWidgets.QDialog):
    def __init__(self, serialSettings: serComm.SerialCommSettings = None):
        """
        Serial settings dialog.
            @param serialSettings: if None, new blank (default settings) are applied. Otherwise, pre-set default given values
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_SerialSetupDialog()
        self.ui.setupUi(self)

        if serialSettings is None:
            self.dialogSettings: serComm.SerialCommSettings = serComm.SerialCommSettings()
        else:
            self.dialogSettings: serComm.SerialCommSettings = serialSettings

        self.applySettingsOnClose = False

        self.connectSignalsToSlots()

        self.setDialogValues(self.dialogSettings)

    def connectSignalsToSlots(self):
        """
        Connect GUI to functions.
        """
        # round button data size group
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_eight, serial.EIGHTBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_seven, serial.SEVENBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_six, serial.SIXBITS)
        self.ui.RB_dataSizeGroup.setId(self.ui.RB_dataSize_five, serial.FIVEBITS)

        # round button parity group
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_none, serComm.parity_as_int(serial.PARITY_NONE))
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_even, serComm.parity_as_int(serial.PARITY_EVEN))
        self.ui.RB_parityGroup.setId(self.ui.RB_parity_odd, serComm.parity_as_int(serial.PARITY_ODD))

        # round button stop bits group
        self.ui.RB_stopBitsGroup.setId(self.ui.RB_stopBits_one, serial.STOPBITS_ONE)
        self.ui.RB_stopBitsGroup.setId(self.ui.RB_stopBits_two, serial.STOPBITS_TWO)

        # OK/cancel buttons
        self.ui.PB_OK.clicked.connect(partial(self.onExit, True))
        self.ui.PB_cancel.clicked.connect(partial(self.onExit, False))

    def showDialog(self):
        """
        Show dialog and raise it above parent widget.
        """
        self.show()
        self.raise_()

    @QtCore.pyqtSlot(bool)
    def onExit(self, okButton: bool):
        """
        On OK, store dialog settings to self.dialogSettings. On Cancel or close, don't do nothing.
        On exit, close dialog.
            @param okButton: if True, OK was pressed. Cancel/close otherwise.
        """
        if okButton:
            self._storeDialogValues()
            self.applySettingsOnClose = True

        self.close()

    def _storeDialogValues(self):
        """
        Store values from a current setup dialog into self.dialogSettings.
        """
        self.dialogSettings.hwFlowControl = self.ui.CB_hwFlowCtrl.isChecked()
        self.dialogSettings.swFlowControl = self.ui.CB_swFlowCtrl.isChecked()

        self.dialogSettings.dataSize = self.ui.RB_dataSizeGroup.checkedId()
        self.dialogSettings.stopbits = self.ui.RB_stopBitsGroup.checkedId()
        parityAsNumber = self.ui.RB_parityGroup.checkedId()
        self.dialogSettings.parity = serComm.parity_as_str(parityAsNumber)

    def getDialogValues(self) -> serComm.SerialCommSettings:
        """
        Store and return dialog values.
        """
        return self.dialogSettings

    def mustApplySettings(self) -> bool:
        """
        Return True if dialog values must be applied, False otherwise.
        Only make sense to call this function once dialog is closed.
        """
        return self.applySettingsOnClose

    def setDialogValues(self, serialSettings: serComm.SerialCommSettings):
        """
        Set current setup dialog settings and refresh internal self.dialogValues state.
        """
        self.ui.CB_hwFlowCtrl.setChecked(serialSettings.swFlowControl)
        self.ui.CB_swFlowCtrl.setChecked(serialSettings.hwFlowControl)

        roundButton = self.ui.RB_dataSizeGroup.button(serialSettings.dataSize)
        roundButton.click()

        parityAsNumber = serComm.parity_as_int(serialSettings.parity)
        roundButton = self.ui.RB_parityGroup.button(parityAsNumber)
        roundButton.click()

        roundButton = self.ui.RB_stopBitsGroup.button(serialSettings.stopbits)
        roundButton.click()

        self._storeDialogValues()


def main():
    app = QtWidgets.QApplication(sys.argv)

    initialSerialDialogSettings = serComm.SerialCommSettings()
    initialSerialDialogSettings.swFlowControl = True
    initialSerialDialogSettings.stopbits = serial.STOPBITS_TWO
    initialSerialDialogSettings.dataSize = serial.SIXBITS

    # setupDialog = SerialSetupDialog()
    setupDialog = SerialSetupDialog(initialSerialDialogSettings)
    setupDialog.showDialog()

    ret = app.exec_()


if __name__ == "__main__":
    main()
