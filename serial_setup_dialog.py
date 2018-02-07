# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'serial_setup_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SerialSetupDialog(object):
    def setupUi(self, SerialSetupDialog):
        SerialSetupDialog.setObjectName("SerialSetupDialog")
        SerialSetupDialog.resize(453, 133)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SerialSetupDialog.sizePolicy().hasHeightForWidth())
        SerialSetupDialog.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("damogranlabs.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SerialSetupDialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(SerialSetupDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.bytesize = QtWidgets.QVBoxLayout()
        self.bytesize.setObjectName("bytesize")
        self.label = QtWidgets.QLabel(SerialSetupDialog)
        self.label.setObjectName("label")
        self.bytesize.addWidget(self.label)
        self.bytesize_eightbits = QtWidgets.QRadioButton(SerialSetupDialog)
        self.bytesize_eightbits.setChecked(True)
        self.bytesize_eightbits.setObjectName("bytesize_eightbits")
        self.bytesize_group = QtWidgets.QButtonGroup(SerialSetupDialog)
        self.bytesize_group.setObjectName("bytesize_group")
        self.bytesize_group.addButton(self.bytesize_eightbits)
        self.bytesize.addWidget(self.bytesize_eightbits)
        self.bytesize_sevenbits = QtWidgets.QRadioButton(SerialSetupDialog)
        self.bytesize_sevenbits.setObjectName("bytesize_sevenbits")
        self.bytesize_group.addButton(self.bytesize_sevenbits)
        self.bytesize.addWidget(self.bytesize_sevenbits)
        self.bytesize_sixbits = QtWidgets.QRadioButton(SerialSetupDialog)
        self.bytesize_sixbits.setObjectName("bytesize_sixbits")
        self.bytesize_group.addButton(self.bytesize_sixbits)
        self.bytesize.addWidget(self.bytesize_sixbits)
        self.bytesize_fivebits = QtWidgets.QRadioButton(SerialSetupDialog)
        self.bytesize_fivebits.setObjectName("bytesize_fivebits")
        self.bytesize_group.addButton(self.bytesize_fivebits)
        self.bytesize.addWidget(self.bytesize_fivebits)
        spacerItem = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.bytesize.addItem(spacerItem)
        self.gridLayout.addLayout(self.bytesize, 0, 2, 1, 1)
        self.parity = QtWidgets.QVBoxLayout()
        self.parity.setObjectName("parity")
        self.label_2 = QtWidgets.QLabel(SerialSetupDialog)
        self.label_2.setObjectName("label_2")
        self.parity.addWidget(self.label_2)
        self.parity_none = QtWidgets.QRadioButton(SerialSetupDialog)
        self.parity_none.setChecked(True)
        self.parity_none.setObjectName("parity_none")
        self.parity_group = QtWidgets.QButtonGroup(SerialSetupDialog)
        self.parity_group.setObjectName("parity_group")
        self.parity_group.addButton(self.parity_none)
        self.parity.addWidget(self.parity_none)
        self.parity_even = QtWidgets.QRadioButton(SerialSetupDialog)
        self.parity_even.setObjectName("parity_even")
        self.parity_group.addButton(self.parity_even)
        self.parity.addWidget(self.parity_even)
        self.parity_odd = QtWidgets.QRadioButton(SerialSetupDialog)
        self.parity_odd.setObjectName("parity_odd")
        self.parity_group.addButton(self.parity_odd)
        self.parity.addWidget(self.parity_odd)
        spacerItem1 = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.parity.addItem(spacerItem1)
        self.gridLayout.addLayout(self.parity, 0, 4, 1, 1)
        self.stop_bits = QtWidgets.QVBoxLayout()
        self.stop_bits.setObjectName("stop_bits")
        self.label_3 = QtWidgets.QLabel(SerialSetupDialog)
        self.label_3.setObjectName("label_3")
        self.stop_bits.addWidget(self.label_3)
        self.stopbits_one = QtWidgets.QRadioButton(SerialSetupDialog)
        self.stopbits_one.setChecked(True)
        self.stopbits_one.setObjectName("stopbits_one")
        self.stopbits_group = QtWidgets.QButtonGroup(SerialSetupDialog)
        self.stopbits_group.setObjectName("stopbits_group")
        self.stopbits_group.addButton(self.stopbits_one)
        self.stop_bits.addWidget(self.stopbits_one)
        self.stopbits_two = QtWidgets.QRadioButton(SerialSetupDialog)
        self.stopbits_two.setObjectName("stopbits_two")
        self.stopbits_group.addButton(self.stopbits_two)
        self.stop_bits.addWidget(self.stopbits_two)
        spacerItem2 = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.stop_bits.addItem(spacerItem2)
        self.confirm = QtWidgets.QPushButton(SerialSetupDialog)
        self.confirm.setObjectName("confirm")
        self.stop_bits.addWidget(self.confirm)
        self.gridLayout.addLayout(self.stop_bits, 0, 6, 1, 1)
        self.flow_control = QtWidgets.QVBoxLayout()
        self.flow_control.setObjectName("flow_control")
        self.label_4 = QtWidgets.QLabel(SerialSetupDialog)
        self.label_4.setObjectName("label_4")
        self.flow_control.addWidget(self.label_4)
        self.flow_xon_xoff = QtWidgets.QCheckBox(SerialSetupDialog)
        self.flow_xon_xoff.setObjectName("flow_xon_xoff")
        self.flow_control.addWidget(self.flow_xon_xoff)
        self.line_2 = QtWidgets.QFrame(SerialSetupDialog)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.flow_control.addWidget(self.line_2)
        self.label_5 = QtWidgets.QLabel(SerialSetupDialog)
        self.label_5.setObjectName("label_5")
        self.flow_control.addWidget(self.label_5)
        self.flow_rts_cts = QtWidgets.QCheckBox(SerialSetupDialog)
        self.flow_rts_cts.setObjectName("flow_rts_cts")
        self.flow_control.addWidget(self.flow_rts_cts)
        spacerItem3 = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.flow_control.addItem(spacerItem3)
        self.gridLayout.addLayout(self.flow_control, 0, 0, 1, 1)
        self.line_3 = QtWidgets.QFrame(SerialSetupDialog)
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 0, 3, 1, 1)
        self.line_4 = QtWidgets.QFrame(SerialSetupDialog)
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.gridLayout.addWidget(self.line_4, 0, 5, 1, 1)
        self.line = QtWidgets.QFrame(SerialSetupDialog)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(SerialSetupDialog)
        QtCore.QMetaObject.connectSlotsByName(SerialSetupDialog)

    def retranslateUi(self, SerialSetupDialog):
        _translate = QtCore.QCoreApplication.translate
        SerialSetupDialog.setWindowTitle(_translate("SerialSetupDialog", "Serial Setup Dialog"))
        self.label.setText(_translate("SerialSetupDialog", "Byte size:"))
        self.bytesize_eightbits.setText(_translate("SerialSetupDialog", "EIGHTBITS"))
        self.bytesize_sevenbits.setText(_translate("SerialSetupDialog", "SEVENBITS"))
        self.bytesize_sixbits.setText(_translate("SerialSetupDialog", "SIXBITS"))
        self.bytesize_fivebits.setText(_translate("SerialSetupDialog", "FIVEBITS"))
        self.label_2.setText(_translate("SerialSetupDialog", "Parity:"))
        self.parity_none.setText(_translate("SerialSetupDialog", "PARITY_NONE"))
        self.parity_even.setText(_translate("SerialSetupDialog", "PARITY_EVEN"))
        self.parity_odd.setText(_translate("SerialSetupDialog", "PARITY_ODD"))
        self.label_3.setText(_translate("SerialSetupDialog", "Stop bits:"))
        self.stopbits_one.setText(_translate("SerialSetupDialog", "STOPBITS_ONE"))
        self.stopbits_two.setText(_translate("SerialSetupDialog", "STOPBITS_TWO"))
        self.confirm.setText(_translate("SerialSetupDialog", "OK"))
        self.label_4.setText(_translate("SerialSetupDialog", "Software flow control:"))
        self.flow_xon_xoff.setText(_translate("SerialSetupDialog", "XON/XOFF"))
        self.label_5.setText(_translate("SerialSetupDialog", "Hardware flow control:"))
        self.flow_rts_cts.setText(_translate("SerialSetupDialog", "RTS/CTS"))
