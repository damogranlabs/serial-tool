"""
Main application window GUI handler.
"""
import logging
from functools import partial
import os
import sys
import platform
import subprocess
import time
import traceback
import webbrowser

import serial.serialutil as serialUtil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

import cfgHandler
import dataModel
import logHandler as log
import serComm
import communication
import setupDialog
from defines import *

# pyuic generated GUI files
from gui.gui import Ui_root
from gui.serialSetupDialog import Ui_SerialSetupDialog

__version__ = "2.3"  # software version


class Gui(QtWidgets.QMainWindow):
    sigWrite = QtCore.pyqtSignal(str, str)
    sigWarning = QtCore.pyqtSignal(str, str)
    sigError = QtCore.pyqtSignal(str, str)

    sigClose = QtCore.pyqtSignal()

    def __init__(self):
        """
        Main Serial Tool application window.
        """
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_root()
        self.ui.setupUi(self)

        # create lists of all similar items
        self.uiDataFields = [self.ui.TI_data1,
                             self.ui.TI_data2,
                             self.ui.TI_data3,
                             self.ui.TI_data4,
                             self.ui.TI_data5,
                             self.ui.TI_data6,
                             self.ui.TI_data7,
                             self.ui.TI_data8]
        self.uiDataSendButtons = [self.ui.PB_send1,
                                  self.ui.PB_send2,
                                  self.ui.PB_send3,
                                  self.ui.PB_send4,
                                  self.ui.PB_send5,
                                  self.ui.PB_send6,
                                  self.ui.PB_send7,
                                  self.ui.PB_send8]

        self.uiNoteFields = [self.ui.TI_note1,
                             self.ui.TI_note2,
                             self.ui.TI_note3,
                             self.ui.TI_note4,
                             self.ui.TI_note5,
                             self.ui.TI_note6,
                             self.ui.TI_note7,
                             self.ui.TI_note8]

        self.uiSeqFields = [self.ui.TI_sequence1,
                            self.ui.TI_sequence2,
                            self.ui.TI_sequence3]
        self.uiSeqSendButtons = [self.ui.PB_sendSequence1,
                                 self.ui.PB_sendSequence2,
                                 self.ui.PB_sendSequence3]
        self._seqThreads: [QtCore.QThread] = [None] * NUM_OF_SEQ_CHANNELS  # threads of sequence handlers
        self._seqSendWorkers: [communication.SerialDataSequenceTransmitterThread] = [None] * NUM_OF_SEQ_CHANNELS  # actual sequence handlers

        self.ui.RB_GROUP_outputRepresentation.setId(self.ui.RB_outputRepresentationString, OutputRepresentation.STRING)
        self.ui.RB_GROUP_outputRepresentation.setId(self.ui.RB_outputRepresentationIntList, OutputRepresentation.INT_LIST)
        self.ui.RB_GROUP_outputRepresentation.setId(self.ui.RB_outputRepresentationHexList, OutputRepresentation.HEX_LIST)
        self.ui.RB_GROUP_outputRepresentation.setId(self.ui.RB_outputRepresentationAsciiList, OutputRepresentation.ASCII_LIST)

        # set up exception handler
        sys.excepthook = self._appExceptionHandler

        self.sharedSignals = dataModel.SharedSignalsContainer()
        self.sharedSignals.sigWrite = self.sigWrite
        self.sharedSignals.sigWarning = self.sigWarning
        self.sharedSignals.sigError = self.sigError

        # prepare data and port handlers
        self.dataModel: dataModel.SerialToolSettings = dataModel.SerialToolSettings()
        self.commHandler: communication.SerialToolPortHandler = communication.SerialToolPortHandler()
        
        # RX display data newline internal logic
        self._lastRxEventTimestamp: int = time.time()  # timestamp of a last RX data event
        self._logDisplayingRxData: bool = False # if true, log window is currently displaying RX data (to be used with '\n on RX data')

        self.cfgHandler: cfgHandler.ConfigurationHandler = cfgHandler.ConfigurationHandler(self.dataModel, self.sharedSignals)

        # init app and gui
        self.connectGuiSignalsToSlots()
        self.connectDataUpdateSignalsToSlots()
        self.connectExecutionSignalsToSlots()

        self.initGuiState()

        self.raise_()

    def connectGuiSignalsToSlots(self):
        # save/load dialog
        self.ui.PB_fileMenu_newConfiguration.triggered.connect(self.onFileCreateNewConfiguration)
        self.ui.PB_fileMenu_saveConfiguration.triggered.connect(self.onFileSaveConfiguration)
        self.ui.PB_fileMenu_loadConfiguration.triggered.connect(self.onFileLoadConfiguration)

        # help menu
        self.ui.PB_helpMenu_about.triggered.connect(self.onHelpAbout)
        self.ui.PB_helpMenu_docs.triggered.connect(self.onHelpDocs)
        self.ui.PB_helpMenu_openLogFile.triggered.connect(self.onOpenLog)

        # SERIAL PORT setup
        self.ui.PB_serialSetup.clicked.connect(self.setSerialSettingsWithDialog)
        self.ui.PB_refreshCommPortsList.clicked.connect(self.refreshPortsList)
        self.ui.PB_commPortCtrl.clicked.connect(self.onPortHandlerButton)

        # data note data send and button fields
        for index, dataField in enumerate(self.uiDataFields):
            dataField.textChanged.connect(partial(self.onDataFieldChange, index))

        for index, dataSendButton in enumerate(self.uiDataSendButtons):
            dataSendButton.clicked.connect(partial(self.onSendDataButton, index))

        for index, noteField in enumerate(self.uiNoteFields):
            noteField.textChanged.connect(partial(self.onNoteFieldChange, index))

        # sequence fields
        for index, seqField in enumerate(self.uiSeqFields):
            seqField.textChanged.connect(partial(self.onSeqFieldChange, index))

        for index, seqSendButton in enumerate(self.uiSeqSendButtons):
            seqSendButton.clicked.connect(partial(self.onSendStopSequenceButton, index))

        # log
        self.ui.PB_clearLog.clicked.connect(self.clearLogWindow)
        self.ui.PB_exportLog.clicked.connect(self.saveLogWindowToFile)
        self.ui.PB_exportRxTxData.clicked.connect(self.saveRxTxDataToFile)
        self.ui.CB_rxToLog.clicked.connect(self.onRxDisplayModeChange)
        self.ui.CB_txToLog.clicked.connect(self.onTxDisplayModeChange)
        self.ui.RB_GROUP_outputRepresentation.buttonClicked.connect(self.onOutputRepresentationModeChange)
        self.ui.CB_rxNewLine.clicked.connect(self.onRxNewLineChange)
        self.ui.SB_rxTimeoutMs.valueChanged.connect(self.onRxNewLineTimeoutChange)

    def connectExecutionSignalsToSlots(self):
        self.sigWrite.connect(self.writeToLogWindow)
        self.sigWarning.connect(self.writeToLogWindow)
        self.sigError.connect(self.writeToLogWindow)

        self.sigClose.connect(self.onQuitApplicationEvent)

        self.commHandler.sigConnectionSuccessfull.connect(self.onConnectEvent)
        self.commHandler.sigConnectionClosed.connect(self.onDisconnectEvent)
        self.commHandler.sigDataReceived.connect(self.onDataReceiveEvent)

    def connectDataUpdateSignalsToSlots(self):
        self.dataModel.sigSerialSettingsUpdate.connect(self.onSerialSettingsUpdate)
        self.dataModel.sigDataFieldUpdate.connect(self.onDataFieldUpdate)
        self.dataModel.sigNoteFieldUpdate.connect(self.onNoteFieldUpdate)
        self.dataModel.sigSeqFieldUpdate.connect(self.onSeqFieldUpdate)
        self.dataModel.sigRxDisplayModeUpdate.connect(self.onRxDisplayModeUpdate)
        self.dataModel.sigTxDisplayModeUpdate.connect(self.onTxDisplayModeUpdate)
        self.dataModel.sigOutputRepresentationModeUpdate.connect(self.onOutputRepresentationModeUpdate)
        self.dataModel.sigRxNewLineUpdate.connect(self.onRxNewLineUpdate)

    def initGuiState(self):
        """
        Init GUI once created (check data/sequence fields, ...).
        """
        #update current window name with version string
        self.setAplicationWindowName()

        self._setMruCfgPaths()

        self.cfgHandler.createDefaultConfiguration()

        # serial port settings
        baudrateValidator = QtGui.QIntValidator(0, serialUtil.SerialBase.BAUDRATES[-1])
        self.ui.DD_baudrate.setValidator(baudrateValidator)
        baudratesAsString = list(map(str, serialUtil.SerialBase.BAUDRATES))
        self.ui.DD_baudrate.addItems(baudratesAsString)

        defaultBaudrateListIndex = serialUtil.SerialBase.BAUDRATES.index(DEFAULT_BAUDRATE)
        self.ui.DD_baudrate.setCurrentIndex(defaultBaudrateListIndex)

        # log fields
        self.clearLogWindow()

        log.info("GUI initialized.")

    def _setMruCfgPaths(self):
        """
        Set most recently used configurations to "File menu > Recently used configurations" list
        """
        self.ui.PB_fileMenu_recentlyUsedConfigurations.clear()

        mruCfgFiles = getMostRecentlyUsedConfigurations(NUM_OF_MAX_RECENTLY_USED_CFG_GUI)
        for mruCfgFile in mruCfgFiles:
            fileName = os.path.basename(mruCfgFile)

            mruCfgAction = QtWidgets.QAction(fileName, self)
            mruCfgAction.triggered.connect(partial(self.onFileLoadConfiguration, mruCfgFile))
            self.ui.PB_fileMenu_recentlyUsedConfigurations.addAction(mruCfgAction)

    def setAplicationWindowName(self, name: str = None):
        """
        Set main application GUI window name.
            @param name: new name to set.
        """
        serialToolName = f"{APPLICATION_NAME} v{__version__}"
        if name is None:
            name = serialToolName
        else:
            name = f"{serialToolName} - {name}"

        self.setWindowTitle(name)

    def getSelectedPort(self) -> str:
        """
        Return name of currently selected serial port from a drop down menu. 
        """
        selectedSerialPort = self.ui.DD_commPortSelector.currentText()
        return selectedSerialPort

    def getPortBaudrate(self) -> int:
        """
        Return selected/set baudrate from a drop down menu. 
        """
        baudrate = self.ui.DD_baudrate.currentText()
        return baudrate

    def setDataSendButtonState(self, channel: int, state: bool):
        """
        Set chosen data data channel push button state to enabled/disabled.
            @param channel: index of data field channel
            @param state: if True, button is enabled. Disabled otherwise.
        """
        self.uiDataSendButtons[channel].setEnabled(state)

    def setAllDataSendButtonState(self, state: bool):
        """
        Set all data send push button state to enabled/disabled.
            @param state: if True, buttons are enabled. Disabled otherwise.
        """
        for button in self.uiDataSendButtons:
            button.setEnabled(state)

    def setSeqSendButtonState(self, channel: int, state: bool):
        """
        Set chosen sequence data channel push button state to enabled/disabled.
            @param channel: index of sequence field channel
            @param state: if True, button is enabled. Disabled otherwise.
        """
        self.uiSeqSendButtons[channel].setEnabled(state)

    def setAllSeqSendButtonState(self, state: bool):
        """
        Set all sequence send push button state to enabled/disabled.
            @param state: if True, buttons are enabled. Disabled otherwise.
        """
        for button in self.uiSeqSendButtons:
            button.setEnabled(state)

    def stopAllSeqThreads(self):
        """
        Stop all sequence threads.
        Ignore exceptions.
        """
        for seqIndex, seqWorker in enumerate(self._seqSendWorkers):
            try:
                if seqWorker is not None:
                    seqWorker.sigSequenceStopRequest.emit()
            except Exception as err:
                errorMsg = f"Unable to stop sequence {seqIndex+1} thread."
                log.error(errorMsg)

    def colorizeTextInputField(self, textInputField: QtWidgets.QLineEdit, status) -> bool:
        """
        Colorize given text input field with pre-defined scheme (see status parameter).
            @param channel: data channel selector: 0 - 7
            @param status: new field color:
                - if status == False: RED
                - if status == True: GREEN
                - if status == None: TRANSPARENT
        """
        if status is None:
            textInputField.setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {INPUT_NONE_COLOR}")
        elif status:
            textInputField.setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {INPUT_VALID_COLOR}")
        else:
            textInputField.setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {INPUT_ERROR_COLOR}")

    def setConnectionButtonState(self, state: bool):
        """
        Set comm port connection status button state (text and color).
            @param state:
                - if True: text = CONNECTED, color = green
                - if False: text = not connected, color = red
        """
        if state:
            self.ui.PB_commPortCtrl.setText(COMM_PORT_CONNECTED_TEXT)
            self.ui.PB_commPortCtrl.setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {COMM_PORT_CONNECTED_COLOR}")
        else:
            self.ui.PB_commPortCtrl.setText(COMM_PORT_NOT_CONNECTED_TEXT)
            self.ui.PB_commPortCtrl.setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {COMM_PORT_NOT_CONNECTED_COLOR}")

    def getRxNewLineTimeoutMs(self) -> int:
        """
        Return value from RX new line spinbox timeout setting.
        """
        value = self.ui.SB_rxTimeoutMs.value() / 1e3  # (to ms conversion)

        return value

    @QtCore.pyqtSlot(str, str)
    def writeToLogWindow(self, msg: str, color: str = LOG_COLOR_NORMAL, appendNewLine: bool = True, ensureInNewline: bool = True):
        """
        Write to log window with a given color.
            @param msg: message to write to log window.
            @param color: color of displayed text (hex format).
            @param appendNewLine: if True, new line terminator is appended to a message
            @param ensureInNewline: if True, additional cursor position check is implemented so given msg is really displayed in new line.
        """
        self._logDisplayingRxData = False

        if appendNewLine:
            msg = f"{msg}\n"

        if ensureInNewline:
            if self.ui.TE_log.textCursor().position() != 0:
                msg = f"\n{msg}"

        currentVerticalScrollBarPos = self.ui.TE_log.verticalScrollBar().value()  # if autoscroll is not in use, set previous location.
        self.ui.TE_log.moveCursor(QtGui.QTextCursor.End)  # always insert at the end of the log window

        self.ui.TE_log.setTextColor(QtGui.QColor(color))
        self.ui.TE_log.insertPlainText(msg)
        self.ui.TE_log.setTextColor(QtGui.QColor(LOG_COLOR_NORMAL))

        if self.ui.PB_autoScroll.isChecked():
            self.ui.TE_log.moveCursor(QtGui.QTextCursor.End)
        else:
            self.ui.TE_log.verticalScrollBar().setValue(currentVerticalScrollBarPos)

        log.debug(f"[LOG_WINDOW]: {msg.strip()}")

    def writeHtmlToLogWindow(self, msg: str):
        """
        Write HTML content to log window with a given color.
            @param msg: html formatted message to write to log window.
        NOTE: override autoscroll checkbox setting - always display message.
        """
        msg = f"{msg}<br>"
        self.ui.TE_log.moveCursor(QtGui.QTextCursor.End)
        self.ui.TE_log.insertHtml(msg)

        if self.ui.PB_autoScroll.isChecked():
            self.ui.TE_log.ensureCursorVisible()

        log.debug(f"writeHtmlToLogWindow: {msg}")

    ################################################################################################
    # Menu bar slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def onFileCreateNewConfiguration(self):
        """
        Create new blank configuration and discard any current settings. User is previously asked for confirmation.
        """
        if self.confirmActionDialog("Warning!", "Create new configuration?\nThis will discard any changes!"):
            self.dataModel.configurationFilePath = None
            self.cfgHandler.createDefaultConfiguration()

            msg = f"New default configuration created."
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)

            self.setAplicationWindowName()
        else:
            log.debug("New configuration request canceled.")

    @QtCore.pyqtSlot()
    def onFileSaveConfiguration(self):
        """
        Save current configuration to a file. File path is selected with default os GUI pop-up.
        """
        if self.dataModel.configurationFilePath is None:
            cfgFilePath = os.path.join(getDefaultLogFolderPath(), DEFAULT_CFG_FILE_NAME)
        else:
            cfgFilePath = self.dataModel.configurationFilePath

        filePath = self.getSaveFileLocation("Save configuration...", cfgFilePath, CFG_FILE_EXTENSION_FILTER)
        if filePath is not None:
            self.dataModel.configurationFilePath = filePath
            self.cfgHandler.saveConfiguration(filePath)

            addCurrentCfgToRecentlyUsedCfgs(filePath)
            self._setMruCfgPaths()

            msg = f"Configuration saved: {filePath}"
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)

            self.setAplicationWindowName(filePath)
        else:
            log.debug("Save configuration request canceled.")

    @QtCore.pyqtSlot()
    def onFileLoadConfiguration(self, filePath: str = None):
        """
        Load configuration from a file and discard any current settings. User is previously asked for confirmation.
            @param filePath: if None, user is asked to entry file path.
        """
        refreshMenu = False

        if filePath is None:
            if self.dataModel.configurationFilePath is None:
                cfgFolder = getDefaultLogFolderPath()
            else:
                cfgFolder = os.path.dirname(self.dataModel.configurationFilePath)

            if self.confirmActionDialog("Warning!", "Loading new configuration?\nThis will discard any changes!"):
                filePath = self.getOpenFileLocation("Load configuration...", cfgFolder, CFG_FILE_EXTENSION_FILTER)
                if filePath is not None:
                    self.dataModel.configurationFilePath = filePath
                    self.cfgHandler.loadConfiguration(filePath)
                    refreshMenu = True
                else:
                    log.debug("Load configuration request canceled.")
        else:
            filePath = os.path.normpath(filePath)
            self.cfgHandler.loadConfiguration(filePath)
            self.dataModel.configurationFilePath = filePath
            refreshMenu = True

        if refreshMenu:
            addCurrentCfgToRecentlyUsedCfgs(filePath)
            self._setMruCfgPaths()

            msg = f"Configuration loaded: {filePath}"
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)

            self.setAplicationWindowName(filePath)

    @QtCore.pyqtSlot()
    def onHelpAbout(self):
        """
        Print current version and info links to log window.
        """
        aboutLines = []
        aboutLines.append(f"<br>************ Serial Tool v{__version__} ************")
        aboutLines.append(f"Domen Jurkovic @ <a href=\"{LINK_DAMOGRANLABS}\">Damogran Labs</a><br>")  # add extra new line
        aboutLines.append(f"GitHub (docs, releases): <a href=\"{LINK_GITHUB}\">{LINK_GITHUB}</a>")
        aboutLines.append(f"Homepage: <a href=\"{LINK_HOMEPAGE}\">{LINK_HOMEPAGE}</a>")

        mergedLines = '<br>'.join(aboutLines)
        self.writeHtmlToLogWindow(mergedLines)

    @QtCore.pyqtSlot()
    def onHelpDocs(self):
        """
        Open Github README page in a web browser.
        """
        webbrowser.open(LINK_GITHUB_DOCS, new=2)  # new=2 new tab

        log.debug("Online docs opened.")

    @QtCore.pyqtSlot()
    def onOpenLog(self):
        """
        Open Serial Tool log file with viewer.
        """
        defaultLogger = log.getDefaultLogHandler()
        filePath = defaultLogger.getLogFilePath()

        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filePath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filePath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filePath))

    ################################################################################################
    # serial settings slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def setSerialSettingsWithDialog(self):
        """
        Open serial settings dialog and set new port settings.
        """
        dialog = setupDialog.SerialSetupDialog(self.dataModel.serialSettings)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.showDialog()
        dialog.exec_()

        if dialog.mustApplySettings():
            self.dataModel.serialSettings = dialog.getDialogValues()

            self.refreshPortsList()

            msg = f"New serial settings applied: {self.dataModel.serialSettings}"
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)
        else:
            log.debug("New serial settings request canceled.")

    @QtCore.pyqtSlot()
    def onSerialSettingsUpdate(self):
        """
        Load new serial settings dialog values from data model.
        """
        self.refreshPortsList()  # also de-init

        if self.dataModel.serialSettings.port is not None:
            chosenCommPort = self.ui.DD_commPortSelector.findText(self.dataModel.serialSettings.port)
            if chosenCommPort == -1:
                self.writeToLogWindow(f"No {self.dataModel.serialSettings.port} serial port currently available.", LOG_COLOR_WARNING)
            else:
                self.ui.DD_commPortSelector.setCurrentIndex(chosenCommPort)

        if self.dataModel.serialSettings.baudrate is not None:
            chosenBaudrate = self.ui.DD_baudrate.findText(str(self.dataModel.serialSettings.baudrate))
            if chosenBaudrate == -1:
                self.writeToLogWindow(f"No {self.dataModel.serialSettings.baudrate} baudrate available, manually added.", LOG_COLOR_WARNING)
                self.ui.DD_baudrate.addItem(str(self.dataModel.serialSettings.baudrate))
                self.ui.DD_baudrate.setCurrentText(str(self.dataModel.serialSettings.baudrate))
            else:
                self.ui.DD_baudrate.setCurrentIndex(chosenBaudrate)

        log.debug("New serial settings applied.")

    @QtCore.pyqtSlot()
    def refreshPortsList(self):
        """
        Refresh list of available serial port list. Will close current port.
        """
        log.debug("Serial port list refresh request.")

        self.commHandler.deinitPort()  # TODO: signal or not?

        availablePorts = serComm.SerialPortHandler().getAvailablePorts()
        self.ui.DD_commPortSelector.clear()
        self.ui.DD_commPortSelector.addItems(list(reversed(availablePorts)))

    @QtCore.pyqtSlot()
    def onPortHandlerButton(self):
        """
        Connect/disconnect from a port with serial settings.
        """
        if self.ui.PB_commPortCtrl.text() == COMM_PORT_CONNECTED_TEXT:
            # currently connected, stop all sequences and disconnect
            self.stopAllSeqThreads()  # might be a problem with unfinished, blockin sequences

            self.commHandler.deinitPort()  # TODO: signal or not?
            msg = f"Disconnect request."
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)
        else:
            # currently disconnected, connect
            selectedPort = self.getSelectedPort()
            if selectedPort == '':
                errorMsg = f"No available port to init serial communication."
                raise Exception(errorMsg)
            else:
                self.dataModel.serialSettings.port = selectedPort

            baudrate = self.getPortBaudrate()
            if baudrate == '':
                errorMsg = f"Set baudrate of serial port."
                raise Exception(errorMsg)
            else:
                baudrateInt = int(baudrate)
                self.dataModel.serialSettings.baudrate = baudrateInt

            self.commHandler.serialSettings = self.dataModel.serialSettings
            self.commHandler.initPortAndReceiveThread()  # TODO: signal or not?

            msg = f"Connect request."
            self.writeToLogWindow(msg, LOG_COLOR_GRAY)

    ################################################################################################
    # application generated events
    ################################################################################################
    @QtCore.pyqtSlot()
    def onConnectEvent(self):
        """
        This function is called once connection to port is successfully created.
        """
        self.setConnectionButtonState(True)
        self.ui.DD_commPortSelector.setEnabled(False)
        self.ui.DD_baudrate.setEnabled(False)

        for dataFieldIndex, dataField in enumerate(self.uiDataFields):
            status, _ = self._unparseDataString(dataFieldIndex)
            if status:
                self.setDataSendButtonState(dataFieldIndex, True)
            else:
                self.setDataSendButtonState(dataFieldIndex, False)

        for seqFieldIndex, seqField in enumerate(self.uiSeqFields):
            status, seqData = self._unparseSequenceDataString(seqFieldIndex)
            if status:
                for block in seqData:
                    if self.dataModel.parsedDataFields[block.channelIndex] is None:
                        self.setSeqSendButtonState(seqFieldIndex, False)
                        break
                else:
                    self.setSeqSendButtonState(seqFieldIndex, True)
            else:
                self.setSeqSendButtonState(seqFieldIndex, False)

        log.debug("\tEvent: connect")

    @QtCore.pyqtSlot()
    def onDisconnectEvent(self):
        """
        This function is called once connection to port is closed.
        """
        self.setConnectionButtonState(False)
        self.ui.DD_commPortSelector.setEnabled(True)
        self.ui.DD_baudrate.setEnabled(True)

        self.setAllDataSendButtonState(False)
        self.setAllSeqSendButtonState(False)

        log.debug("\tEvent: disconnect")

    @QtCore.pyqtSlot(list)
    def onDataReceiveEvent(self, data: [int]):
        """
        This function is called once data is received on a serial port.
        """
        dataString = self.convertDataToChosenFormat(data)

        self.dataModel.allRxTxData.append(f"{EXPORT_RX_TAG}{data}")
        if self.dataModel.displayReceivedData:
            msg = f"{dataString}"
            if self.dataModel.rxNewLine:
                # insert \n on RX data, after specified timeout
                if self._logDisplayingRxData:
                    # we are in the middle of displaying RX data, check timestamp delta
                    if (time.time() - self._lastRxEventTimestamp) > self.getRxNewLineTimeoutMs():
                        msg = f"\n{dataString}"
                    # else: # not enough time has passed, just add data without new line
                # else: # some RX data or other message was displayed in log window since last RX data display
            #else: # no RX on new line is needed, just add RX data
            self.writeToLogWindow(msg, RX_DATA_LOG_COLOR, False, False)
            self._logDisplayingRxData = True
        
        self._lastRxEventTimestamp = time.time()

        log.debug(f"\tEvent: data received: {dataString}")

    @QtCore.pyqtSlot(int)
    def onSendSequenceFinishEvent(self, channel: int):
        """
        This function is called once sequence sending thread is finished.
            @param channel: sequence channel.
        """
        self.uiSeqSendButtons[channel].setText(SEQ_BUTTON_START_TEXT)
        self.uiSeqSendButtons[channel].setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: None")
        self._seqThreads[channel] = None

        log.debug(f"\tEvent: sequence {channel + 1} finished")

    @QtCore.pyqtSlot(int, int)
    def onSequenceSendEvent(self, seqChannel: int, dataChannel: int):
        """
        This function is called once data is send from send sequence thread.
            @param seqChannel: index of sequence channel index.
            @param dataChannel: index of data channel index.
        """
        data = self.dataModel.parsedDataFields[dataChannel]
        dataString = self.convertDataToChosenFormat(data)

        self.dataModel.allRxTxData.append(f"{SEQ_TAG}{seqChannel+1}_CH{dataChannel+1}{EXPORT_TX_TAG}{data}")
        if self.dataModel.displayTransmittedData:
            msg = f"{SEQ_TAG}{seqChannel+1}_CH{dataChannel+1}: {dataString}"

            self.writeToLogWindow(msg, TX_DATA_LOG_COLOR)

        log.debug(f"\tEvent: sequence {seqChannel + 1}, data channel {dataChannel + 1} send request")

    @QtCore.pyqtSlot(int)
    def stopSequenceRequestEvent(self, channel: int):
        """
        Display "stop" request sequence action.
            @param channel: sequence button channel.
        """
        self._seqSendWorkers[channel].sigSequenceStopRequest.emit()

        log.debug(f"\tEvent: sequence {channel + 1} stop request")

    @QtCore.pyqtSlot()
    def onQuitApplicationEvent(self):
        """
        Deinit serial port, close GUI.
        """
        self.commHandler.deinitPort()

        self.close()

    ################################################################################################
    # data/sequence fields/buttons slots
    ################################################################################################
    @QtCore.pyqtSlot(int)
    def onDataFieldUpdate(self, channel: int):
        """
        Actions to take place once data field is updated (for example, from load configuration).
            @param channel: index of data field
        """
        self.uiDataFields[channel].setText(self.dataModel.dataFields[channel])
        self.onDataFieldChange(channel)

    @QtCore.pyqtSlot(int)
    def onNoteFieldUpdate(self, channel: int):
        """
        Actions to take place once note field is updated (for example, from load configuration).
            @param channel: index of note field
        """
        self.uiNoteFields[channel].setText(self.dataModel.noteFields[channel])

    @QtCore.pyqtSlot(int)
    def onSeqFieldUpdate(self, channel: int):
        """
        Actions to take place once sequence field is updated (for example, from load configuration).
            @param channel: index of data field
        """
        self.uiSeqFields[channel].setText(self.dataModel.seqFields[channel])
        self.onSeqFieldChange(channel)

    @QtCore.pyqtSlot(int)
    def onDataFieldChange(self, channel: int):
        """
        Actions to take place once any data field is changed.
            @param channel: index of data field
        """
        self.dataModel.dataFields[channel] = self.uiDataFields[channel].text()

        status, data = self._unparseDataString(channel)
        self.colorizeTextInputField(self.uiDataFields[channel], status)

        if status:
            self.dataModel.parsedDataFields[channel] = data
            if self.commHandler.isConnected():
                self.setDataSendButtonState(channel, True)
            else:
                self.setDataSendButtonState(channel, False)
        else:  # False or None (empty field)
            self.dataModel.parsedDataFields[channel] = None
            self.setDataSendButtonState(channel, False)

        # update sequence fields - sequence fields depends on data fields.
        for seqFieldIndex, _ in enumerate(self.uiSeqFields):
            self.onSeqFieldChange(seqFieldIndex)

    @QtCore.pyqtSlot(int)
    def onNoteFieldChange(self, channel: int):
        """
        Actions to take place once any of note field is changed.
            @param channel: index of note field
        """
        noteFieldText = self.uiNoteFields[channel].text()
        self.dataModel.noteFields[channel] = noteFieldText.strip()

    @QtCore.pyqtSlot(int)
    def onSeqFieldChange(self, channel: int):
        """
        Actions to take place once any sequence field is changed.
            @param channel: index of sequence field

        TODO: colorize sequence RED if any of selected data channels is not valid
        """
        self.dataModel.seqFields[channel] = self.uiSeqFields[channel].text()

        status, data = self._unparseSequenceDataString(channel)
        self.colorizeTextInputField(self.uiSeqFields[channel], status)

        if status:
            self.dataModel.parsedSeqFields[channel] = data
            # check if seq button can be enabled (seq field is properly formatted. Are all data fields properly formatted?
            for block in data:
                if self.dataModel.parsedDataFields[block.channelIndex] is None:
                    self.setSeqSendButtonState(channel, False)
                    break
            else:
                if self.commHandler.isConnected():
                    self.setSeqSendButtonState(channel, True)
                else:
                    self.setSeqSendButtonState(channel, False)
        else:  # False or None (empty field)
            self.dataModel.parsedSeqFields[channel] = None
            self.setSeqSendButtonState(channel, False)

    @QtCore.pyqtSlot(int)
    def onSendDataButton(self, channel: int):
        """
        Send data on a selected data channel.
            @param channel: index of data field index
        """
        data = self.dataModel.parsedDataFields[channel]
        dataString = self.convertDataToChosenFormat(data)

        self.dataModel.allRxTxData.append(f"CH{channel}{EXPORT_TX_TAG}{data}")
        if self.dataModel.displayTransmittedData:
            self.writeToLogWindow(dataString, TX_DATA_LOG_COLOR)

        self.commHandler.sigWrite.emit(data)

    @QtCore.pyqtSlot(int)
    def onSendStopSequenceButton(self, channel: int):
        """
        Start sending data sequence.
            @param channel: sequence field channel.
        """
        if self.uiSeqSendButtons[channel].text() == SEQ_BUTTON_START_TEXT:
            self.uiSeqSendButtons[channel].setText(SEQ_BUTTON_STOP_TEXT)
            self.uiSeqSendButtons[channel].setStyleSheet(f"{DEFAULT_FONT_STYLE} background-color: {SEQ_ACTIVE_COLOR}")

            thread = QtCore.QThread(self)
            worker = communication.SerialDataSequenceTransmitterThread(self.commHandler.portHandler,
                                                                       channel,
                                                                       self.dataModel.parsedDataFields,
                                                                       self.dataModel.parsedSeqFields)
            worker.sigSequenceTransmittFinished.connect(self.onSendSequenceFinishEvent)
            worker.sigDataSendEvent.connect(self.onSequenceSendEvent)

            worker.moveToThread(thread)
            thread.started.connect(worker.run)

            self._seqThreads[channel] = thread
            self._seqSendWorkers[channel] = worker

            self._seqThreads[channel].start()
        else:
            self._seqSendWorkers[channel].sigSequenceStopRequest.emit()
            msg = f"Sequence {channel+1} stop request!"
            self.writeToLogWindow(msg, LOG_COLOR_WARNING)

    ################################################################################################
    # log settings slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def clearLogWindow(self):
        """
        Clear log window.
        """
        self.dataModel.allRxTxData = []
        self.ui.TE_log.clear()

    @QtCore.pyqtSlot()
    def saveLogWindowToFile(self):
        """
        Save (export) content of a current log window to a file.
        Pick destination with default OS pop-up window.
        """
        defaultLogFilePath = os.path.join(getDefaultLogFolderPath(), DEFAULT_LOG_EXPORT_FILENAME)
        filePath = self.getSaveFileLocation("Save log window content...", defaultLogFilePath, LOG_EXPORT_FILE_EXTENSION_FILTER)
        if filePath is not None:
            with open(filePath, 'w+') as fileHandler:
                contentToLog = self.ui.TE_log.toPlainText()
                fileHandler.writelines(contentToLog)

            self.writeToLogWindow(f"Log window content saved to: {filePath}", LOG_COLOR_GRAY)
        else:
            log.debug("Save log window content request canceled.")

    @QtCore.pyqtSlot()
    def saveRxTxDataToFile(self):
        """
        Save (export) content of all RX/TX data to a file.
        Pick destination with default OS pop-up window.
        """
        defaultLogFilePath = os.path.join(getDefaultLogFolderPath(), DEFAULT_DATA_EXPORT_FILENAME)
        filePath = self.getSaveFileLocation("Save raw RX/TX data...", defaultLogFilePath, DATA_EXPORT_FILE_EXTENSION_FILTER)
        if filePath is not None:
            with open(filePath, 'w+') as fileHandler:
                for data in self.dataModel.allRxTxData:
                    fileHandler.write(data + "\n")

            self.dataModel.allRxTxData = []
            self.writeToLogWindow(f"RX/TX data exported: {filePath}", LOG_COLOR_GRAY)
        else:
            log.debug("RX/TX data export request canceled.")

    @QtCore.pyqtSlot()
    def onRxDisplayModeUpdate(self):
        """
        Action to take place once RX-to-log checkbox setting is altered (for example, on load configuration).
        """
        self.ui.CB_rxToLog.setChecked(self.dataModel.displayReceivedData)

    @QtCore.pyqtSlot()
    def onRxDisplayModeChange(self):
        """
        Get RX-to-log checkbox settings from GUI.
        """
        self.dataModel.displayReceivedData = self.ui.CB_rxToLog.isChecked()

    @QtCore.pyqtSlot()
    def onTxDisplayModeUpdate(self):
        """
        Action to take place once TX-to-log checkbox setting is altered (for example, on load configuration).
        """
        self.ui.CB_txToLog.setChecked(self.dataModel.displayTransmittedData)

    @QtCore.pyqtSlot()
    def onTxDisplayModeChange(self):
        """
        Get TX-to-log checkbox settings from GUI.
        """
        self.dataModel.displayTransmittedData = self.ui.CB_txToLog.isChecked()

    @QtCore.pyqtSlot()
    def onOutputRepresentationModeUpdate(self):
        """
        Action to take place once outputDataRepresentation setting is altered (for example, on load configuration).
        """
        self.ui.RB_GROUP_outputRepresentation.button(self.dataModel.outputDataRepresentation).click()

    @QtCore.pyqtSlot()
    def onOutputRepresentationModeChange(self):
        """
        Get output representation type from GUI selection.
        """
        self.dataModel.outputDataRepresentation = self.ui.RB_GROUP_outputRepresentation.checkedId()

    @QtCore.pyqtSlot()
    def onRxNewLineUpdate(self):
        """
        Action to take place once RX new line setting is altered (for example, on load configuration).
        """
        self.ui.CB_rxNewLine.setChecked(self.dataModel.rxNewLine)
        if self.dataModel.rxNewLine:
            self.ui.SB_rxTimeoutMs.setEnabled(True)
        else:
            self.ui.SB_rxTimeoutMs.setEnabled(False)

    @QtCore.pyqtSlot()
    def onRxNewLineChange(self):
        """
        Get RX new line settings of log RX/TX data.
        """
        self.dataModel.rxNewLine = self.ui.CB_rxNewLine.isChecked()
        if self.dataModel.rxNewLine:
            self.ui.SB_rxTimeoutMs.setEnabled(True)
        else:
            self.ui.SB_rxTimeoutMs.setEnabled(False)

        return self.dataModel.rxNewLine

    @QtCore.pyqtSlot()
    def onRxNewLineTimeoutUpdate(self):
        """
        Action to take place once RX new line timeout setting is altered (for example, on load configuration).
        """
        self.ui.SB_rxTimeoutMs.setValue(self.dataModel.rxNewLineTimeout)

    @QtCore.pyqtSlot()
    def onRxNewLineTimeoutChange(self):
        """
        Get RX new line settings of log RX/TX data.
        """
        self.dataModel.rxNewLineTimeout = self.ui.SB_rxTimeoutMs.value()

        return self.dataModel.rxNewLineTimeout

    ################################################################################################
    # utility functions
    ################################################################################################

    def _checkIfDataNumberInRange(self, number: int) -> bool:
        """
        Return True if number is in range:
            - if number is signed char (as int8_t): -128 <= number <= +127
            - if number is unsigned char (as uint8_t): 0 <= number <= 255 
        False otherwise.
            @param number: number to check.
        """
        if number < 0:  # signed integer
            if number >= -128:
                return True
        else:  # unsigned integer
            if number <= 255:
                return True

        return False

    def _unparseDataString(self, channel: int) -> (bool, [int]):
        """
        Get string from a data field and return a tuple:
            - on success: True, [<valid data bytes to send>]
            - on empty string: None, ''
            - on error: False, <current string>

            @param ch: sequence channel selector: 0 - 7
        """
        dataField = self.uiDataFields[channel]
        currentText = dataField.text()
        if currentText != '':
            try:
                dataList = []

                currentText = currentText.strip()
                dataParts = currentText.strip(DATA_BYTES_SEPARATOR)
                dataParts = dataParts.split(DATA_BYTES_SEPARATOR)
                for dataPart in dataParts:
                    dataPart = dataPart.strip()

                    # handle HEX numbers (can be one or more bytes)
                    if dataPart.lower().startswith('0x'):
                        dataPart = dataPart.lower()
                        dataPart = dataPart.strip('0x')
                        if len(dataPart) % 2:
                            dataPart = '0' + dataPart
                        hexNumbers = list(bytearray.fromhex(dataPart))
                        dataList.extend(hexNumbers)
                        continue

                    # character (enclosed in "<one or more characters>")
                    if dataPart.startswith('\"') and dataPart.endswith('\"'):
                        dataPart = dataPart.strip('\"')
                        for char in dataPart:
                            charAsInt = ord(char)
                            if self._checkIfDataNumberInRange(charAsInt):
                                dataList.append(charAsInt)
                        continue

                    # number
                    if dataPart.isdigit() or dataPart.startswith('-'):
                        dataAsInt = int(dataPart)
                        if self._checkIfDataNumberInRange(dataAsInt):
                            # if negative number, create two's complement
                            if dataAsInt < 0:
                                intAsByte = dataAsInt.to_bytes(1, byteorder=sys.byteorder, signed=True)
                                dataAsUnsignedInt = int.from_bytes(intAsByte, byteorder=sys.byteorder, signed=False)
                            else:
                                dataAsUnsignedInt = dataAsInt
                            dataList.append(dataAsUnsignedInt)
                            continue

                    raise Exception('Invalid data format!')
                else:
                    return True, dataList

            except Exception as err:
                # something is wrong in a given data string
                return False, currentText

        return None, ''

    def _unparseSequenceDataString(self, channel: int) -> (bool, [SequenceData]):
        """
        Get data from a sequence field and and return a tuple:
            - on success: True, [<valid SequenceData objects>]
            - on empty string: None, ''
            - on error: False, <current string>

            @param channel: sequence channel selector: 0 - 2
        """
        seq = self.uiSeqFields[channel]
        currentText = seq.text()
        if currentText != '':
            try:
                parsedBlocksData = []

                currentText = currentText.strip()
                blocks = currentText.strip(SEQ_BLOCK_SEPARATOR)
                blocks = blocks.split(SEQ_BLOCK_SEPARATOR)
                for block in blocks:
                    block = block.strip()
                    if block.startswith(SEQ_BLOCK_START_CHARACTER) and block.endswith(SEQ_BLOCK_END_CHARACTER):
                        block = block.strip(SEQ_BLOCK_START_CHARACTER)
                        block = block.strip(SEQ_BLOCK_END_CHARACTER)
                        blockData = block.split(SEQ_BLOCK_DATA_SEPARATOR)
                        if len(blockData) in [2, 3]:  # repeat number is not mandatory
                            dataChannelIndex = int(blockData[0].strip())
                            if 1 <= dataChannelIndex <= NUM_OF_DATA_CHANNELS:  # user must enter a number as seen in GUI, starts with 1
                                dataChannelIndex = dataChannelIndex - 1
                                channelDelay = int(blockData[1].strip())
                                if 0 <= channelDelay:
                                    thisBlockData = SequenceData(dataChannelIndex, channelDelay)
                                    if len(blockData) == 3:  # repeat is specified
                                        repeatNumber = int(blockData[2].strip())
                                        if repeatNumber >= 1:
                                            thisBlockData.repeat = repeatNumber
                                        else:
                                            raise Exception("Invalid 'repeat' sequence block number, (negative or 0).")
                                    parsedBlocksData.append(thisBlockData)
                                    continue
                    raise Exception('Invalid sequence format!')
                else:
                    return True, parsedBlocksData

            except Exception as err:
                # something is wrong in a given sequence string
                return False, currentText

        return None, ''

    def listOfIntsToString(self, data: [int]) -> str:
        """
        Convert list of data (integers) to a string, without data separator.
            @param data: list of integers to be converted.
        """
        intStr = ''
        for number in data:
            intStr += chr(number)

        return intStr

    def listOfIntsToIntString(self, data: [int]) -> str:
        """
        Convert list of data (integers) to a string of integer values.
            @param data: list of integers to be converted.
        """
        intList = []
        for number in data:
            intList.append(str(number))
        intStr = RX_DATA_LIST_SEPARATOR.join(intList) + RX_DATA_LIST_SEPARATOR

        return intStr

    def listOfIntsToHexString(self, data: [int]) -> str:
        """
        Convert list of data (integers) to a string of hex values.
            @param data: list of integers to be converted.
        """
        hexList = []
        for number in data:
            hexNumber = "{0:#0{1}x}".format(number, 4)  # format always as 0x** (two fields for data value)
            hexList.append(hexNumber)
        hexStr = RX_DATA_LIST_SEPARATOR.join(hexList) + RX_DATA_LIST_SEPARATOR

        return hexStr

    def listOfIntsToAsciiString(self, data: [int]) -> str:
        """
        Convert list of data (integers) to a string of ascii characters.
            @param data: list of integers to be converted.
        """

        asciiList = []
        for number in data:
            asciiList.append(f"'{chr(number)}'")
        asciiStr = RX_DATA_LIST_SEPARATOR.join(asciiList) + RX_DATA_LIST_SEPARATOR

        return asciiStr

    def convertDataToChosenFormat(self, data: [int]) -> str:
        """
        Convert chosen data to a string with selected format.
        """
        dataString = ''
        if self.dataModel.outputDataRepresentation == OutputRepresentation.STRING:
            dataString = self.listOfIntsToString(data)
        elif self.dataModel.outputDataRepresentation == OutputRepresentation.INT_LIST:
            dataString = self.listOfIntsToIntString(data)
        elif self.dataModel.outputDataRepresentation == OutputRepresentation.HEX_LIST:
            dataString = self.listOfIntsToHexString(data)
        else: #self.dataModel.outputDataRepresentation == OutputRepresentation.ASCII_LIST
            dataString = self.listOfIntsToAsciiString(data)

        return dataString

    def getSaveFileLocation(self, name: str, folderPath: str = None, filterExtension: str = "*.txt") -> str:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
        See getFileLocation() for parameters.
        """
        return self.getFileLocation(name, True, folderPath, filterExtension)

    def getOpenFileLocation(self, name: str, folderPath: str = None, filterExtension: str = "*.txt") -> str:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
        See getFileLocation() for parameters.
        """
        return self.getFileLocation(name, False, folderPath, filterExtension)

    def getFileLocation(self, name: str, saveType: bool = True, folderPath: str = None, filterExtension: str = None) -> str:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
            @param name: name of pop-up gui window.
            @param saveType: if True, dialog for selecting save file is created. Otherwise, dialog to open file is created.
            @param folderPath: path to a folder/file where dialog should be open. getDefaultLogFolderPath() is used by default.
            @param filterExtension: file extension filter (can be merged list: "*.txt, "*.json", "*.log")
        """
        if folderPath is None:
            folderPath = getDefaultLogFolderPath()
        else:
            folderPath = os.path.normpath(folderPath)

        if saveType:
            fileName, _ = QFileDialog.getSaveFileName(self, name, folderPath, filterExtension)
        else:
            fileName, _ = QFileDialog.getOpenFileName(self, name, folderPath, filterExtension)
        if fileName != '':
            fileName = os.path.normpath(fileName)
            return fileName
        else:
            return None

    def confirmActionDialog(self, name: str, question: str, icon: QMessageBox.Icon = QMessageBox.Icon.Question) -> bool:
        """
        Pop-up system dialog with OK|Cancel options.
        Return True if user respond with click to OK button. Else, return False.
        """
        dialog = QtWidgets.QMessageBox()

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("gui/images/SerialTool.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        dialog.setWindowIcon(icon)

        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Ok)
        dialog.setEscapeButton(QMessageBox.Cancel)

        dialog.setText(question)
        dialog.setWindowTitle(name)

        retval = dialog.exec_()
        if retval == QMessageBox.Ok:
            return True
        else:
            return False

    def _appExceptionHandler(self, excType, excValue, tracebackObj):
        """
        Global function to catch unhandled exceptions.
        
        @param excType: exception type
        @param excValue: exception value
        @param tracebackObj: traceback object
        """
        try:
            errorMsg = "\n * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"
            errorMsg += f"\nUnhandled unexpected exception occurred! Program will try to continue with execution."
            errorMsg += f"\n\tExc. type: {excType}"
            errorMsg += f"\n\tExc. value: {excValue}"
            errorMsg += f"\n\tExc. traceback: {traceback.format_tb(tracebackObj)}"
            errorMsg += "\n\n"

            try:
                self.sigError.emit(errorMsg, LOG_COLOR_ERROR)
            except Exception as err:
                # at least, log to file if log over signal fails
                log.error(errorMsg)

            self.stopAllSeqThreads()
            self.commHandler.deinitPort()

        except Exception as err:
            log.error(f"Error in exception handling function.\n{err}")
            self.sigClose.emit()


###############################################################################################
# Other
################################################################################################
def getDefaultLogFolderPath() -> str:
    """
    Return path to a default Serial Tool Appdata folder: %APPDATA%/<SERIAL_TOOL_APPDATA_FOLDER_NAME>
    """
    appdataPath = os.environ["APPDATA"]
    serialToolFolderPath = os.path.join(appdataPath, SERIAL_TOOL_APPDATA_FOLDER_NAME)

    return serialToolFolderPath


def getRecentlyUsedCfgFilePath() -> str:
    """
    Get path to a RECENTLY_USED_CFG_FILE_NAME which is, by default stored in log folder.
    """
    recentlyUsedCfgsFilePath = os.path.join(getDefaultLogFolderPath(), RECENTLY_USED_CFG_FILE_NAME)

    return recentlyUsedCfgsFilePath


def addCurrentCfgToRecentlyUsedCfgs(cfgFilePath: str):
    """
    Add entry (insert at position 0, first line) current configuration file to a list of recently used configurations.
    """
    path = os.path.normpath(cfgFilePath)
    path = os.path.abspath(cfgFilePath)

    recentlyUsedCfgsFilePath = getRecentlyUsedCfgFilePath()
    if not os.path.exists(recentlyUsedCfgsFilePath):
        with open(recentlyUsedCfgsFilePath, 'w') as fileHandler:
            fileHandler.write(f"{path}\n")
    else:
        try:
            with open(recentlyUsedCfgsFilePath, 'r+') as fileHandler:
                lines = fileHandler.readlines()
                fileHandler.seek(0)  # strange \x00 appeared without this
                fileHandler.truncate(0)

                lines.insert(0, f"{path}\n")

                # remove duplicates
                relevantPaths = []
                linesToWrite = []
                configurationsNumber = 0
                for line in lines:
                    line = line.strip()
                    if line not in relevantPaths:
                        if os.path.exists(line):
                            if configurationsNumber < MAX_NUM_OF_RECENTLY_USED_CFGS:
                                relevantPaths.append(line)
                                linesToWrite.append(f"{line}\n")
                                configurationsNumber = configurationsNumber + 1

                fileHandler.writelines(linesToWrite)

        except Exception as err:
            log.warning(f"Error while writing/parsing recently used cfgs file:\n{err}")

            try:
                with open(recentlyUsedCfgsFilePath, 'w') as fileHandler:
                    fileHandler.write(f"{path}\n")
                log.info(f"New recently used cfgs file created: {recentlyUsedCfgsFilePath}")
            except Exception as err:
                log.warning(f"Unable to create new recently used cfgs file:\n{err}")
                log.warning(f"\tNo further attempts.")


def getMostRecentlyUsedConfiguration() -> str:
    """
    Get the most recently used configuration.
    Return None if file does not exist or it is empty.
    """
    mruCfgFilePaths = getMostRecentlyUsedConfigurations(1)
    if mruCfgFilePaths:
        mruCfgFilePath = mruCfgFilePath[0].strip("\n").strip()
        return mruCfgFilePath
    else:
        return None


def getMostRecentlyUsedConfigurations(number: int) -> [str]:
    """
    Get a list of last 'number' of valid entries of recently used configurations.
        @param number: number of  max recently used configuration file paths to return.
    """
    recentlyUsedCfgsFilePath = getRecentlyUsedCfgFilePath()

    recentlyUsedCfgFilePaths = []
    try:
        if os.path.exists(recentlyUsedCfgsFilePath):
            with open(recentlyUsedCfgsFilePath, 'r') as fileHandler:
                lines = fileHandler.readlines()
                currentNumber = 0
                for line in lines:
                    if currentNumber < number:
                        line = line.strip()
                        if os.path.exists(line):
                            if line not in recentlyUsedCfgFilePaths:
                                recentlyUsedCfgFilePaths.append(line)
                                currentNumber = currentNumber + 1
                    else:
                        break
    except Exception as err:
        log.warning(f"Unable to get most recently used configurations from file: {recentlyUsedCfgsFilePath}\n{err}")

    return recentlyUsedCfgFilePaths


def createLogFolder() -> str:
    """
    Create <application root folder>/log folder and return absolute path to this folder.
    On fail, return None.
    """
    logFolderPath = getDefaultLogFolderPath()
    if not os.path.exists(logFolderPath):
        try:
            os.mkdir(logFolderPath)
        except Exception as err:
            errorMsg = f"Unable to create log folder: {logFolderPath}"
            errorMsg += f"\nCheck location write permissions."
            errorMsg += f"\nError:{err}"
            raise Exception(errorMsg)

    return logFolderPath


def initEnvironment():
    """
    Init log folder, log handler and 
    """
    logFolder = getDefaultLogFolderPath()
    createLogFolder()

    logger = log.LogHandler()
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)+8s: %(message)s")
    logger.addConsoleHandler(formatter)
    logger.addFileHandler(SERIAL_TOOL_LOG_FILENAME, logFolder, formatter)

    log.info("Log initialized.")


###################################################################################################
def main():
    initEnvironment()

    app = QtWidgets.QApplication(sys.argv)
    gui = Gui()
    gui.show()

    ret = app.exec_()

    sys.exit(ret)


if __name__ == "__main__":
    main()
