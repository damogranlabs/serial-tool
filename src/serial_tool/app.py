"""
Main application window GUI handler.
"""
import logging
from functools import partial
import os
import sys
import time
import traceback
import webbrowser
from typing import List, Optional, Tuple, Union

import serial.serialutil as serialUtil
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import serial_tool
from serial_tool import defines as defs
from serial_tool import models
from serial_tool import cfgHandler
from serial_tool import dataModel
from serial_tool import serial_hdlr
from serial_tool import communication
from serial_tool import setup_dialog
from serial_tool import paths
from serial_tool import validators

# pyuic generated GUI files
from serial_tool.gui.gui import Ui_root


class Gui(QtWidgets.QMainWindow):
    sig_write = QtCore.pyqtSignal(str, str)
    sig_warning = QtCore.pyqtSignal(str, str)
    sig_error = QtCore.pyqtSignal(str, str)

    sigClose = QtCore.pyqtSignal()

    def __init__(self):
        """
        Main Serial Tool application window.
        """
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_root()
        self.ui.setupUi(self)

        # create lists of all similar items
        self.uiDataFields: Tuple[QtWidgets.QLineEdit, ...] = (
            self.ui.TI_data1,
            self.ui.TI_data2,
            self.ui.TI_data3,
            self.ui.TI_data4,
            self.ui.TI_data5,
            self.ui.TI_data6,
            self.ui.TI_data7,
            self.ui.TI_data8,
        )
        self.uiDataSendButtons: Tuple[QtWidgets.QPushButton, ...] = (
            self.ui.PB_send1,
            self.ui.PB_send2,
            self.ui.PB_send3,
            self.ui.PB_send4,
            self.ui.PB_send5,
            self.ui.PB_send6,
            self.ui.PB_send7,
            self.ui.PB_send8,
        )

        self.uiNoteFields: Tuple[QtWidgets.QLineEdit, ...] = (
            self.ui.TI_note1,
            self.ui.TI_note2,
            self.ui.TI_note3,
            self.ui.TI_note4,
            self.ui.TI_note5,
            self.ui.TI_note6,
            self.ui.TI_note7,
            self.ui.TI_note8,
        )

        self.uiSeqFields: Tuple[QtWidgets.QLineEdit, ...] = (
            self.ui.TI_sequence1,
            self.ui.TI_sequence2,
            self.ui.TI_sequence3,
        )
        self.uiSeqSendButtons: Tuple[QtWidgets.QPushButton, ...] = (
            self.ui.PB_sendSequence1,
            self.ui.PB_sendSequence2,
            self.ui.PB_sendSequence3,
        )
        self._seqThreads: List[Optional[QtCore.QThread]] = [
            None
        ] * defs.NUM_OF_SEQ_CHANNELS  # threads of sequence handlers
        self._seqSendWorkers: List[Optional[communication.SerialDataSequenceTransmitterThread]] = [
            None
        ] * defs.NUM_OF_SEQ_CHANNELS  # actual sequence handlers

        self.ui.RB_GROUP_outputRepresentation.setId(
            self.ui.RB_outputRepresentationString, defs.OutputRepresentation.STRING
        )
        self.ui.RB_GROUP_outputRepresentation.setId(
            self.ui.RB_outputRepresentationIntList, defs.OutputRepresentation.INT_LIST
        )
        self.ui.RB_GROUP_outputRepresentation.setId(
            self.ui.RB_outputRepresentationHexList, defs.OutputRepresentation.HEX_LIST
        )
        self.ui.RB_GROUP_outputRepresentation.setId(
            self.ui.RB_outputRepresentationAsciiList, defs.OutputRepresentation.ASCII_LIST
        )

        # set up exception handler
        sys.excepthook = self._appExceptionHandler

        self._signals = dataModel.SharedSignalsContainer(self.sig_write, self.sig_warning, self.sig_error)

        # prepare data and port handlers
        self.dataModel = dataModel.SerialToolSettings()
        self.commHandler = communication.SerialToolPortHandler()

        # RX display data newline internal logic
        # timestamp of a last RX data event
        self._lastRxEventTimestamp = time.time()
        # if true, log window is currently displaying RX data (to be used with '\n on RX data')
        self._logDisplayingRxData = False

        self.cfgHandler: cfgHandler.ConfigurationHandler = cfgHandler.ConfigurationHandler(
            self.dataModel, self._signals
        )

        # init app and gui
        self.connectGuiSignalsToSlots()
        self.connectDataUpdateSignalsToSlots()
        self.connectExecutionSignalsToSlots()

        self.initGuiState()

        self.raise_()

    def connectGuiSignalsToSlots(self) -> None:
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
        for idx, data_field in enumerate(self.uiDataFields):
            data_field.textChanged.connect(partial(self.onDataFieldChange, idx))

        for idx, data_send_pb in enumerate(self.uiDataSendButtons):
            data_send_pb.clicked.connect(partial(self.onSendDataButton, idx))

        for idx, note_field in enumerate(self.uiNoteFields):
            note_field.textChanged.connect(partial(self.onNoteFieldChange, idx))

        # sequence fields
        for idx, seq_field in enumerate(self.uiSeqFields):
            seq_field.textChanged.connect(partial(self.onSeqFieldChange, idx))

        for idx, seq_send_pb in enumerate(self.uiSeqSendButtons):
            seq_send_pb.clicked.connect(partial(self.onSendStopSequenceButton, idx))

        # log
        self.ui.PB_clearLog.clicked.connect(self.clearLogWindow)
        self.ui.PB_exportLog.clicked.connect(self.saveLogWindowToFile)
        self.ui.PB_exportRxTxData.clicked.connect(self.saveRxTxDataToFile)
        self.ui.CB_rxToLog.clicked.connect(self.onRxDisplayModeChange)
        self.ui.CB_txToLog.clicked.connect(self.onTxDisplayModeChange)
        self.ui.RB_GROUP_outputRepresentation.buttonClicked.connect(self.onOutputRepresentationModeChange)
        self.ui.CB_rxNewLine.clicked.connect(self.onRxNewLineChange)
        self.ui.SB_rxTimeoutMs.valueChanged.connect(self.onRxNewLineTimeoutChange)

    def connectExecutionSignalsToSlots(self) -> None:
        self.sig_write.connect(self.writeToLogWindow)
        self.sig_warning.connect(self.writeToLogWindow)
        self.sig_error.connect(self.writeToLogWindow)

        self.sigClose.connect(self.onQuitApplicationEvent)

        self.commHandler.sigConnectionSuccessfull.connect(self.onConnectEvent)
        self.commHandler.sigConnectionClosed.connect(self.onDisconnectEvent)
        self.commHandler.sigDataReceived.connect(self.onDataReceiveEvent)

    def connectDataUpdateSignalsToSlots(self) -> None:
        self.dataModel.sig_serial_settings_update.connect(self.onSerialSettingsUpdate)
        self.dataModel.sigDataFieldUpdate.connect(self.onDataFieldUpdate)
        self.dataModel.sigNoteFieldUpdate.connect(self.onNoteFieldUpdate)
        self.dataModel.sigSeqFieldUpdate.connect(self.onSeqFieldUpdate)
        self.dataModel.sigRxDisplayModeUpdate.connect(self.onRxDisplayModeUpdate)
        self.dataModel.sigTxDisplayModeUpdate.connect(self.onTxDisplayModeUpdate)
        self.dataModel.sigOutputRepresentationModeUpdate.connect(self.onOutputRepresentationModeUpdate)
        self.dataModel.sigRxNewLineUpdate.connect(self.onRxNewLineUpdate)

    def initGuiState(self) -> None:
        """
        Init GUI once created (check data/sequence fields, ...).
        """
        # update current window name with version string
        self.setAplicationWindowName()

        self._setMruCfgPaths()

        self.cfgHandler.createDefaultConfiguration()

        # serial port settings
        baudrateValidator = QtGui.QIntValidator(0, serialUtil.SerialBase.BAUDRATES[-1])
        self.ui.DD_baudrate.setValidator(baudrateValidator)
        baudratesAsString = list(map(str, serialUtil.SerialBase.BAUDRATES))
        self.ui.DD_baudrate.addItems(baudratesAsString)

        defaultBaudrateListIndex = serialUtil.SerialBase.BAUDRATES.index(defs.DEFAULT_BAUDRATE)
        self.ui.DD_baudrate.setCurrentIndex(defaultBaudrateListIndex)

        # log fields
        self.clearLogWindow()

        logging.info("GUI initialized.")

    def _setMruCfgPaths(self) -> None:
        """
        Set most recently used configurations to "File menu > Recently used configurations" list
        """
        self.ui.PB_fileMenu_recentlyUsedConfigurations.clear()

        mruCfgFiles = paths.get_recently_used_cfgs(defs.NUM_OF_MAX_RECENTLY_USED_CFG_GUI)
        for mruCfgFile in mruCfgFiles:
            fileName = os.path.basename(mruCfgFile)

            mruCfgAction = QtWidgets.QAction(fileName, self)
            mruCfgAction.triggered.connect(partial(self.onFileLoadConfiguration, mruCfgFile))
            self.ui.PB_fileMenu_recentlyUsedConfigurations.addAction(mruCfgAction)

    def setAplicationWindowName(self, name: Optional[str] = None) -> None:
        """
        Set additional name to the main application GUI window.

        Args:
            name: Optional additional name to set.
        """
        main_name = f"{defs.APPLICATION_NAME} v{serial_tool.__version__}"
        if name:
            main_name += f" - {name}"

        self.setWindowTitle(main_name)

    def getSelectedPort(self) -> str:
        """
        Return name of currently selected serial port from a drop down menu.
        """
        return self.ui.DD_commPortSelector.currentText()

    def getPortBaudrate(self) -> str:
        """
        Return selected/set baudrate from a drop down menu.
        """
        return self.ui.DD_baudrate.currentText()

    def setDataSendButtonState(self, channel: int, state: bool) -> None:
        """
        Set chosen data data channel push button state to enabled/disabled.
            @param channel: index of data field channel
            @param state: if True, button is enabled. Disabled otherwise.
        """
        self.uiDataSendButtons[channel].setEnabled(state)

    def setAllDataSendButtonState(self, state: bool) -> None:
        """
        Set all data send push button state to enabled/disabled.
            @param state: if True, buttons are enabled. Disabled otherwise.
        """
        for button in self.uiDataSendButtons:
            button.setEnabled(state)

    def setSeqSendButtonState(self, channel: int, state: bool) -> None:
        """
        Set chosen sequence data channel push button state to enabled/disabled.
            @param channel: index of sequence field channel
            @param state: if True, button is enabled. Disabled otherwise.
        """
        self.uiSeqSendButtons[channel].setEnabled(state)

    def setAllSeqSendButtonState(self, state: bool) -> None:
        """
        Set all sequence send push button state to enabled/disabled.
            @param state: if True, buttons are enabled. Disabled otherwise.
        """
        for button in self.uiSeqSendButtons:
            button.setEnabled(state)

    def stopAllSeqThreads(self) -> None:
        """
        Stop all sequence threads.
        Ignore exceptions.
        """
        for seqIndex, seqWorker in enumerate(self._seqSendWorkers):
            try:
                if seqWorker is not None:
                    seqWorker.sigSequenceStopRequest.emit()
            except Exception as err:
                logging.error(f"Unable to stop sequence {seqIndex+1} thread.\n{err}")

    def colorize_text_field(self, field: QtWidgets.QLineEdit, status: models.TextFieldStatus) -> None:
        """Colorize given text input field with pre-defined scheme (see status parameter)."""
        color = models.TextFieldStatus.get_color(status)
        field.setStyleSheet(f"{defs.DEFAULT_FONT_STYLE} background-color: {color}")

    def setConnectionButtonState(self, state: bool) -> None:
        """
        Set comm port connection status button state (text and color).
            @param state:
                - if True: text = CONNECTED, color = green
                - if False: text = not connected, color = red
        """
        if state:
            self.ui.PB_commPortCtrl.setText(defs.COMM_PORT_CONNECTED_TEXT)
            self.ui.PB_commPortCtrl.setStyleSheet(
                f"{defs.DEFAULT_FONT_STYLE} background-color: {defs.COMM_PORT_CONNECTED_COLOR}"
            )
        else:
            self.ui.PB_commPortCtrl.setText(defs.COMM_PORT_NOT_CONNECTED_TEXT)
            self.ui.PB_commPortCtrl.setStyleSheet(
                f"{defs.DEFAULT_FONT_STYLE} background-color: {defs.COMM_PORT_NOT_CONNECTED_COLOR}"
            )

    def getRxNewLineTimeoutMs(self) -> int:
        """
        Return value from RX new line spinbox timeout setting.
        """
        value = self.ui.SB_rxTimeoutMs.value() / 1e3  # (to ms conversion)

        return int(value)

    @QtCore.pyqtSlot(str, str)
    def writeToLogWindow(
        self, msg: str, color: str = defs.LOG_COLOR_NORMAL, appendNewLine: bool = True, ensureInNewline: bool = True
    ) -> None:
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

        # if autoscroll is not in use, set previous location.
        currentVerticalScrollBarPos = self.ui.TE_log.verticalScrollBar().value()
        # always insert at the end of the log window
        self.ui.TE_log.moveCursor(QtGui.QTextCursor.End)

        self.ui.TE_log.setTextColor(QtGui.QColor(color))
        self.ui.TE_log.insertPlainText(msg)
        self.ui.TE_log.setTextColor(QtGui.QColor(defs.LOG_COLOR_NORMAL))

        if self.ui.PB_autoScroll.isChecked():
            self.ui.TE_log.moveCursor(QtGui.QTextCursor.End)
        else:
            self.ui.TE_log.verticalScrollBar().setValue(currentVerticalScrollBarPos)

        logging.debug(f"[LOG_WINDOW]: {msg.strip()}")

    def writeHtmlToLogWindow(self, msg: str) -> None:
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

        logging.debug(f"writeHtmlToLogWindow: {msg}")

    ################################################################################################
    # Menu bar slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def onFileCreateNewConfiguration(self) -> None:
        """
        Create new blank configuration and discard any current settings. User is previously asked for confirmation.
        """
        if self.confirmActionDialog("Warning!", "Create new configuration?\nThis will discard any changes!"):
            self.dataModel.cfg_file_path = None
            self.cfgHandler.createDefaultConfiguration()

            msg = "New default configuration created."
            self.writeToLogWindow(msg, defs.LOG_COLOR_GRAY)

            self.setAplicationWindowName()
        else:
            logging.debug("New configuration request canceled.")

    @QtCore.pyqtSlot()
    def onFileSaveConfiguration(self) -> None:
        """
        Save current configuration to a file. File path is selected with default os GUI pop-up.
        """
        if self.dataModel.cfg_file_path is None:
            cfgFilePath = os.path.join(paths.get_default_log_dir(), defs.DEFAULT_CFG_FILE_NAME)
        else:
            cfgFilePath = self.dataModel.cfg_file_path

        filePath = self.getSaveFileLocation("Save configuration...", cfgFilePath, defs.CFG_FILE_EXTENSION_FILTER)
        if filePath is not None:
            self.dataModel.cfg_file_path = filePath
            self.cfgHandler.saveConfiguration(filePath)

            paths.add_cfg_to_recently_used_cfgs(filePath)
            self._setMruCfgPaths()

            msg = f"Configuration saved: {filePath}"
            self.writeToLogWindow(msg, defs.LOG_COLOR_GRAY)

            self.setAplicationWindowName(filePath)
        else:
            logging.debug("Save configuration request canceled.")

    @QtCore.pyqtSlot()
    def onFileLoadConfiguration(self, filePath: Optional[str] = None) -> None:
        """
        Load configuration from a file and discard any current settings. User is previously asked for confirmation.
            @param filePath: if None, user is asked to entry file path.
        """
        refreshMenu = False

        if filePath is None:
            if self.dataModel.cfg_file_path is None:
                cfgFolder = paths.get_default_log_dir()
            else:
                cfgFolder = os.path.dirname(self.dataModel.cfg_file_path)

            if self.confirmActionDialog("Warning!", "Loading new configuration?\nThis will discard any changes!"):
                filePath = self.getOpenFileLocation("Load configuration...", cfgFolder, defs.CFG_FILE_EXTENSION_FILTER)
                if filePath is not None:
                    self.dataModel.cfg_file_path = filePath
                    self.cfgHandler.loadConfiguration(filePath)
                    refreshMenu = True
                else:
                    logging.debug("Load configuration request canceled.")
        else:
            filePath = os.path.normpath(filePath)
            self.cfgHandler.loadConfiguration(filePath)
            self.dataModel.cfg_file_path = filePath
            refreshMenu = True

        if refreshMenu:
            paths.add_cfg_to_recently_used_cfgs(filePath)
            self._setMruCfgPaths()

            msg = f"Configuration loaded: {filePath}"
            self.writeToLogWindow(msg, defs.LOG_COLOR_GRAY)

            self.setAplicationWindowName(filePath)

    @QtCore.pyqtSlot()
    def onHelpAbout(self) -> None:
        """
        Print current version and info links to log window.
        """
        aboutLines = []
        aboutLines.append(f"<br>************ Serial Tool v{serial_tool.__version__} ************")
        # add extra new line
        aboutLines.append(f'Domen Jurkovic @ <a href="{defs.LINK_DAMOGRANLABS}">Damogran Labs</a><br>')
        aboutLines.append(f'GitHub (docs, releases): <a href="{defs.LINK_GITHUB}">{defs.LINK_GITHUB}</a>')
        aboutLines.append(f'Homepage: <a href="{defs.LINK_HOMEPAGE}">{defs.LINK_HOMEPAGE}</a>')

        mergedLines = "<br>".join(aboutLines)
        self.writeHtmlToLogWindow(mergedLines)

    @QtCore.pyqtSlot()
    def onHelpDocs(self) -> None:
        """
        Open Github README page in a web browser.
        """
        webbrowser.open(defs.LINK_GITHUB_DOCS, new=2)  # new=2 new tab

        logging.debug("Online docs opened.")

    @QtCore.pyqtSlot()
    def onOpenLog(self) -> None:
        """
        Open Serial Tool log file.
        """
        path = paths.get_log_file_path()

        webbrowser.open(f"file://{path}", new=2)

    ################################################################################################
    # serial settings slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def setSerialSettingsWithDialog(self) -> None:
        """
        Open serial settings dialog and set new port settings.
        """
        dialog = setup_dialog.SerialSetupDialog(self.dataModel.serial_settings)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.display()
        dialog.exec_()

        if dialog.mustApplySettings():
            self.dataModel.serial_settings = dialog.get_settings()

            self.refreshPortsList()

            msg = f"New serial settings applied: {self.dataModel.serial_settings}"
            self.writeToLogWindow(msg, defs.LOG_COLOR_GRAY)
        else:
            logging.debug("New serial settings request canceled.")

    @QtCore.pyqtSlot()
    def onSerialSettingsUpdate(self) -> None:
        """
        Load new serial settings dialog values from data model.
        """
        self.refreshPortsList()  # also de-init

        if self.dataModel.serial_settings.port is not None:
            chosenCommPort = self.ui.DD_commPortSelector.findText(self.dataModel.serial_settings.port)
            if chosenCommPort == -1:
                self.writeToLogWindow(
                    f"No {self.dataModel.serial_settings.port} serial port currently available.", defs.LOG_COLOR_WARNING
                )
            else:
                self.ui.DD_commPortSelector.setCurrentIndex(chosenCommPort)

        if self.dataModel.serial_settings.baudrate is not None:
            chosenBaudrate = self.ui.DD_baudrate.findText(str(self.dataModel.serial_settings.baudrate))
            if chosenBaudrate == -1:
                self.writeToLogWindow(
                    f"No {self.dataModel.serial_settings.baudrate} baudrate available, manually added.",
                    defs.LOG_COLOR_WARNING,
                )
                self.ui.DD_baudrate.addItem(str(self.dataModel.serial_settings.baudrate))
                self.ui.DD_baudrate.setCurrentText(str(self.dataModel.serial_settings.baudrate))
            else:
                self.ui.DD_baudrate.setCurrentIndex(chosenBaudrate)

        logging.debug("New serial settings applied.")

    @QtCore.pyqtSlot()
    def refreshPortsList(self) -> None:
        """
        Refresh list of available serial port list. Will close current port.
        """
        logging.debug("Serial port list refresh request.")

        self.commHandler.deinitPort()  # TODO: signal or not?

        availablePorts = serial_hdlr.SerialPortHandler().get_available_ports()
        self.ui.DD_commPortSelector.clear()
        self.ui.DD_commPortSelector.addItems(list(reversed(availablePorts)))

    @QtCore.pyqtSlot()
    def onPortHandlerButton(self) -> None:
        """
        Connect/disconnect from a port with serial settings.
        """
        if self.ui.PB_commPortCtrl.text() == defs.COMM_PORT_CONNECTED_TEXT:
            # currently connected, stop all sequences and disconnect
            self.stopAllSeqThreads()  # might be a problem with unfinished, blockin sequences

            self.commHandler.deinitPort()  # TODO: signal or not?
            self.writeToLogWindow("Disconnect request.", defs.LOG_COLOR_GRAY)
        else:
            # currently disconnected, connect
            serial_port = self.getSelectedPort()
            if not serial_port:
                raise RuntimeError("No available port to init serial communication.")
            self.dataModel.serial_settings.port = serial_port

            baudrate = self.getPortBaudrate()
            if not baudrate:
                raise RuntimeError("Set baudrate of serial port.")
            self.dataModel.serial_settings.baudrate = int(baudrate)

            self.commHandler.serialSettings = self.dataModel.serial_settings
            self.commHandler.initPortAndReceiveThread()  # TODO: signal or not?

            self.writeToLogWindow("Connect request.", defs.LOG_COLOR_GRAY)

    ################################################################################################
    # application generated events
    ################################################################################################
    @QtCore.pyqtSlot()
    def onConnectEvent(self) -> None:
        """
        This function is called once connection to port is successfully created.
        """
        self.setConnectionButtonState(True)
        self.ui.DD_commPortSelector.setEnabled(False)
        self.ui.DD_baudrate.setEnabled(False)

        for idx, _ in enumerate(self.uiDataFields):
            result = self._parse_data_field(idx)
            if result.status == models.TextFieldStatus.OK:
                self.setDataSendButtonState(idx, True)
            else:
                self.setDataSendButtonState(idx, False)

        for seqFieldIndex, _ in enumerate(self.uiSeqFields):
            result = self._parse_seq_data_field(seqFieldIndex)
            if result.status:
                for block in result.data:
                    if self.dataModel.parsed_data_fields[block.channel_idx] is None:
                        self.setSeqSendButtonState(seqFieldIndex, False)
                        break
                else:
                    self.setSeqSendButtonState(seqFieldIndex, True)
            else:
                self.setSeqSendButtonState(seqFieldIndex, False)

        logging.debug("\tEvent: connect")

    @QtCore.pyqtSlot()
    def onDisconnectEvent(self) -> None:
        """
        This function is called once connection to port is closed.
        """
        self.setConnectionButtonState(False)
        self.ui.DD_commPortSelector.setEnabled(True)
        self.ui.DD_baudrate.setEnabled(True)

        self.setAllDataSendButtonState(False)
        self.setAllSeqSendButtonState(False)

        logging.debug("\tEvent: disconnect")

    @QtCore.pyqtSlot(list)
    def onDataReceiveEvent(self, data: List[int]) -> None:
        """
        This function is called once data is received on a serial port.
        """
        dataString = self._convert_data(data, self.dataModel.output_data_representation)

        self.dataModel.all_rx_tx_data.append(f"{defs.EXPORT_RX_TAG}{data}")
        if self.dataModel.display_rx_data:
            msg = f"{dataString}"
            if self.dataModel.new_line_on_rx:
                # insert \n on RX data, after specified timeout
                if self._logDisplayingRxData:
                    # we are in the middle of displaying RX data, check timestamp delta
                    if (time.time() - self._lastRxEventTimestamp) > self.getRxNewLineTimeoutMs():
                        msg = f"\n{dataString}"
                    # else: # not enough time has passed, just add data without new line
                # else: # some RX data or other message was displayed in log window since last RX data display
            # else: # no RX on new line is needed, just add RX data
            self.writeToLogWindow(msg, defs.RX_DATA_LOG_COLOR, False, False)
            self._logDisplayingRxData = True

        self._lastRxEventTimestamp = time.time()

        logging.debug(f"\tEvent: data received: {dataString}")

    @QtCore.pyqtSlot(int)
    def onSendSequenceFinishEvent(self, channel: int) -> None:
        """
        This function is called once sequence sending thread is finished.
            @param channel: sequence channel.
        """
        self.uiSeqSendButtons[channel].setText(defs.SEQ_BUTTON_START_TEXT)
        self.uiSeqSendButtons[channel].setStyleSheet(f"{defs.DEFAULT_FONT_STYLE} background-color: None")
        self._seqThreads[channel] = None

        logging.debug(f"\tEvent: sequence {channel + 1} finished")

    @QtCore.pyqtSlot(int, int)
    def onSequenceSendEvent(self, seqChannel: int, dataChannel: int) -> None:
        """
        This function is called once data is send from send sequence thread.
            @param seqChannel: index of sequence channel index.
            @param dataChannel: index of data channel index.
        """
        data = self.dataModel.parsed_data_fields[dataChannel]
        assert data is not None
        data_str = self._convert_data(data, self.dataModel.output_data_representation)

        self.dataModel.all_rx_tx_data.append(
            f"{defs.SEQ_TAG}{seqChannel+1}_CH{dataChannel+1}{defs.EXPORT_TX_TAG}{data}"
        )
        if self.dataModel.display_tx_data:
            msg = f"{defs.SEQ_TAG}{seqChannel+1}_CH{dataChannel+1}: {data_str}"

            self.writeToLogWindow(msg, defs.TX_DATA_LOG_COLOR)

        logging.debug(f"\tEvent: sequence {seqChannel + 1}, data channel {dataChannel + 1} send request")

    @QtCore.pyqtSlot(int)
    def stopSequenceRequestEvent(self, channel: int) -> None:
        """
        Display "stop" request sequence action.
            @param channel: sequence button channel.
        """
        worker = self._seqSendWorkers[channel]
        assert worker is not None
        worker.sigSequenceStopRequest.emit()

        logging.debug(f"\tEvent: sequence {channel + 1} stop request")

    @QtCore.pyqtSlot()
    def onQuitApplicationEvent(self) -> None:
        """
        Deinit serial port, close GUI.
        """
        self.commHandler.deinitPort()

        self.close()

    ################################################################################################
    # data/sequence fields/buttons slots
    ################################################################################################
    @QtCore.pyqtSlot(int)
    def onDataFieldUpdate(self, channel: int) -> None:
        """
        Actions to take place once data field is updated (for example, from load configuration).
            @param channel: index of data field
        """
        self.uiDataFields[channel].setText(self.dataModel.data_fields[channel])
        self.onDataFieldChange(channel)

    @QtCore.pyqtSlot(int)
    def onNoteFieldUpdate(self, channel: int) -> None:
        """
        Actions to take place once note field is updated (for example, from load configuration).
            @param channel: index of note field
        """
        self.uiNoteFields[channel].setText(self.dataModel.note_fields[channel])

    @QtCore.pyqtSlot(int)
    def onSeqFieldUpdate(self, channel: int) -> None:
        """
        Actions to take place once sequence field is updated (for example, from load configuration).
            @param channel: index of data field
        """
        self.uiSeqFields[channel].setText(self.dataModel.seq_fields[channel])
        self.onSeqFieldChange(channel)

    @QtCore.pyqtSlot(int)
    def onDataFieldChange(self, channel: int) -> None:
        """
        Actions to take place once any data field is changed.
            @param channel: index of data field
        """
        self.dataModel.data_fields[channel] = self.uiDataFields[channel].text()

        result = self._parse_data_field(channel)
        self.colorize_text_field(self.uiDataFields[channel], result.status)

        if result.status == models.TextFieldStatus.OK:
            assert result.data is not None
            self.dataModel.parsed_data_fields[channel] = result.data
            if self.commHandler.isConnected():
                self.setDataSendButtonState(channel, True)
            else:
                self.setDataSendButtonState(channel, False)
        else:  # False or None (empty field)
            self.dataModel.parsed_data_fields[channel] = None
            self.setDataSendButtonState(channel, False)

        # update sequence fields - sequence fields depends on data fields.
        for seqFieldIndex, _ in enumerate(self.uiSeqFields):
            self.onSeqFieldChange(seqFieldIndex)

    @QtCore.pyqtSlot(int)
    def onNoteFieldChange(self, channel: int) -> None:
        """
        Actions to take place once any of note field is changed.
            @param channel: index of note field
        """
        noteFieldText = self.uiNoteFields[channel].text()
        self.dataModel.note_fields[channel] = noteFieldText.strip()

    @QtCore.pyqtSlot(int)
    def onSeqFieldChange(self, channel: int) -> None:
        """
        Actions to take place once any sequence field is changed.
            @param channel: index of sequence field

        TODO: colorize sequence RED if any of selected data channels is not valid
        """
        self.dataModel.seq_fields[channel] = self.uiSeqFields[channel].text()

        result = self._parse_seq_data_field(channel)
        self.colorize_text_field(self.uiSeqFields[channel], result.status)

        if result.status == models.TextFieldStatus.OK:
            self.dataModel.parsed_seq_fields[channel] = result.data
            # check if seq button can be enabled (seq field is properly formatted. Are all data fields properly formatted?
            for block in result.data:
                if self.dataModel.parsed_data_fields[block.channel_idx] is None:
                    self.setSeqSendButtonState(channel, False)
                    break
            else:
                if self.commHandler.isConnected():
                    self.setSeqSendButtonState(channel, True)
                else:
                    self.setSeqSendButtonState(channel, False)
        else:  # False or None (empty field)
            self.dataModel.parsed_seq_fields[channel] = None
            self.setSeqSendButtonState(channel, False)

    @QtCore.pyqtSlot(int)
    def onSendDataButton(self, channel: int) -> None:
        """Send data on a selected data channel."""
        data = self.dataModel.parsed_data_fields[channel]
        assert data is not None
        dataString = self._convert_data(data, self.dataModel.output_data_representation)

        self.dataModel.all_rx_tx_data.append(f"CH{channel}{defs.EXPORT_TX_TAG}{data}")
        if self.dataModel.display_tx_data:
            self.writeToLogWindow(dataString, defs.TX_DATA_LOG_COLOR)

        self.commHandler.sigWrite.emit(data)

    @QtCore.pyqtSlot(int)
    def onSendStopSequenceButton(self, channel: int) -> None:
        """
        Start sending data sequence.
            @param channel: sequence field channel.
        """
        if self.uiSeqSendButtons[channel].text() == defs.SEQ_BUTTON_START_TEXT:
            self.uiSeqSendButtons[channel].setText(defs.SEQ_BUTTON_STOP_TEXT)
            self.uiSeqSendButtons[channel].setStyleSheet(
                f"{defs.DEFAULT_FONT_STYLE} background-color: {defs.SEQ_ACTIVE_COLOR}"
            )

            thread = QtCore.QThread(self)
            worker = communication.SerialDataSequenceTransmitterThread(
                self.commHandler.portHandler,
                channel,
                self.dataModel.parsed_data_fields,
                self.dataModel.parsed_seq_fields,
            )
            worker.sigSequenceTransmittFinished.connect(self.onSendSequenceFinishEvent)
            worker.sigDataSendEvent.connect(self.onSequenceSendEvent)

            worker.moveToThread(thread)
            thread.started.connect(worker.run)

            self._seqThreads[channel] = thread
            self._seqSendWorkers[channel] = worker

            thread.start()
        else:
            worker = self._seqSendWorkers[channel]
            assert worker is not None
            worker.sigSequenceStopRequest.emit()

            self.writeToLogWindow(f"Sequence {channel+1} stop request!", defs.LOG_COLOR_WARNING)

    ################################################################################################
    # log settings slots
    ################################################################################################
    @QtCore.pyqtSlot()
    def clearLogWindow(self) -> None:
        """
        Clear log window.
        """
        self.dataModel.all_rx_tx_data = []
        self.ui.TE_log.clear()

    @QtCore.pyqtSlot()
    def saveLogWindowToFile(self) -> None:
        """
        Save (export) content of a current log window to a file.
        Pick destination with default OS pop-up window.
        """
        defaultLogFilePath = os.path.join(paths.get_default_log_dir(), defs.DEFAULT_LOG_EXPORT_FILENAME)
        filePath = self.getSaveFileLocation(
            "Save log window content...", defaultLogFilePath, defs.LOG_EXPORT_FILE_EXTENSION_FILTER
        )
        if filePath is not None:
            with open(filePath, "w+") as fileHandler:
                contentToLog = self.ui.TE_log.toPlainText()
                fileHandler.writelines(contentToLog)

            self.writeToLogWindow(f"Log window content saved to: {filePath}", defs.LOG_COLOR_GRAY)
        else:
            logging.debug("Save log window content request canceled.")

    @QtCore.pyqtSlot()
    def saveRxTxDataToFile(self) -> None:
        """
        Save (export) content of all RX/TX data to a file.
        Pick destination with default OS pop-up window.
        """
        defaultLogFilePath = os.path.join(paths.get_default_log_dir(), defs.DEFAULT_DATA_EXPORT_FILENAME)
        filePath = self.getSaveFileLocation(
            "Save raw RX/TX data...", defaultLogFilePath, defs.DATA_EXPORT_FILE_EXTENSION_FILTER
        )
        if filePath is not None:
            with open(filePath, "w+") as fileHandler:
                for data in self.dataModel.all_rx_tx_data:
                    fileHandler.write(data + "\n")

            self.dataModel.all_rx_tx_data = []
            self.writeToLogWindow(f"RX/TX data exported: {filePath}", defs.LOG_COLOR_GRAY)
        else:
            logging.debug("RX/TX data export request canceled.")

    @QtCore.pyqtSlot()
    def onRxDisplayModeUpdate(self) -> None:
        """
        Action to take place once RX-to-log checkbox setting is altered (for example, on load configuration).
        """
        self.ui.CB_rxToLog.setChecked(self.dataModel.display_rx_data)

    @QtCore.pyqtSlot()
    def onRxDisplayModeChange(self) -> None:
        """
        Get RX-to-log checkbox settings from GUI.
        """
        self.dataModel.display_rx_data = self.ui.CB_rxToLog.isChecked()

    @QtCore.pyqtSlot()
    def onTxDisplayModeUpdate(self) -> None:
        """
        Action to take place once TX-to-log checkbox setting is altered (for example, on load configuration).
        """
        self.ui.CB_txToLog.setChecked(self.dataModel.display_tx_data)

    @QtCore.pyqtSlot()
    def onTxDisplayModeChange(self) -> None:
        """
        Get TX-to-log checkbox settings from GUI.
        """
        self.dataModel.display_tx_data = self.ui.CB_txToLog.isChecked()

    @QtCore.pyqtSlot()
    def onOutputRepresentationModeUpdate(self) -> None:
        """
        Action to take place once outputDataRepresentation setting is altered (for example, on load configuration).
        """
        self.ui.RB_GROUP_outputRepresentation.button(self.dataModel.output_data_representation).click()

    @QtCore.pyqtSlot()
    def onOutputRepresentationModeChange(self) -> None:
        """
        Get output representation type from GUI selection.
        """
        self.dataModel.output_data_representation = self.ui.RB_GROUP_outputRepresentation.checkedId()

    @QtCore.pyqtSlot()
    def onRxNewLineUpdate(self) -> None:
        """
        Action to take place once RX new line setting is altered (for example, on load configuration).
        """
        self.ui.CB_rxNewLine.setChecked(self.dataModel.new_line_on_rx)
        if self.dataModel.new_line_on_rx:
            self.ui.SB_rxTimeoutMs.setEnabled(True)
        else:
            self.ui.SB_rxTimeoutMs.setEnabled(False)

    @QtCore.pyqtSlot()
    def onRxNewLineChange(self) -> None:
        """
        Get RX new line settings of log RX/TX data.
        """
        self.dataModel.new_line_on_rx = self.ui.CB_rxNewLine.isChecked()
        if self.dataModel.new_line_on_rx:
            self.ui.SB_rxTimeoutMs.setEnabled(True)
        else:
            self.ui.SB_rxTimeoutMs.setEnabled(False)

        return self.dataModel.new_line_on_rx

    @QtCore.pyqtSlot()
    def onRxNewLineTimeoutUpdate(self) -> None:
        """
        Action to take place once RX new line timeout setting is altered (for example, on load configuration).
        """
        self.ui.SB_rxTimeoutMs.setValue(self.dataModel.new_line_on_rx_timeout_msec)

    @QtCore.pyqtSlot()
    def onRxNewLineTimeoutChange(self) -> None:
        """
        Get RX new line settings of log RX/TX data.
        """
        self.dataModel.new_line_on_rx_timeout_msec = self.ui.SB_rxTimeoutMs.value()

        return self.dataModel.new_line_on_rx_timeout_msec

    ################################################################################################
    # utility functions
    ################################################################################################
    def _parse_data_field(self, channel: int) -> models.ChannelTextFieldParserResult:
        """Get string from a data field and return parsed data"""
        assert 0 <= channel < defs.NUM_OF_DATA_CHANNELS

        text = self.uiDataFields[channel].text()
        return validators.parse_channel_data(text)

    def _parse_seq_data_field(self, channel: int) -> models.SequenceTextFieldParserResult:
        """Get data from a sequence field and return parsed data"""
        assert 0 <= channel < defs.NUM_OF_SEQ_CHANNELS
        seq = self.uiSeqFields[channel]
        text = seq.text()

        return validators.parse_seq_data(text)

    def _convert_data(self, data: List[int], new_format: Union[int, defs.OutputRepresentation]) -> str:
        """Convert chosen data to a string with selected format."""
        if new_format == defs.OutputRepresentation.STRING:
            # Convert list of integers to a string, without data separator.
            output_data = "".join([chr(num) for num in data])
        elif new_format == defs.OutputRepresentation.INT_LIST:
            # Convert list of integers to a string of integer values.
            int_data = [str(num) for num in data]
            output_data = defs.RX_DATA_LIST_SEPARATOR.join(int_data) + defs.RX_DATA_LIST_SEPARATOR
        elif new_format == defs.OutputRepresentation.HEX_LIST:
            # Convert list of integers to a string of hex values.
            # format always as 0x** (two fields for data value)
            hex_data = ["{0:#0{1}x}".format(num, 4) for num in data]
            output_data = defs.RX_DATA_LIST_SEPARATOR.join(hex_data) + defs.RX_DATA_LIST_SEPARATOR
        else:
            ascii_data = [f"'{chr(num)}'" for num in data]
            output_data = defs.RX_DATA_LIST_SEPARATOR.join(ascii_data) + defs.RX_DATA_LIST_SEPARATOR

        return output_data

    def getSaveFileLocation(
        self, name: str, folderPath: Optional[str] = None, filterExtension: str = "*.txt"
    ) -> Optional[str]:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
        See getFileLocation() for parameters.
        """
        return self.getFileLocation(name, True, folderPath, filterExtension)

    def getOpenFileLocation(
        self, name: str, folderPath: Optional[str] = None, filterExtension: str = "*.txt"
    ) -> Optional[str]:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
        See getFileLocation() for parameters.
        """
        return self.getFileLocation(name, False, folderPath, filterExtension)

    def getFileLocation(
        self, name: str, saveType: bool = True, folderPath: Optional[str] = None, filterExtension: Optional[str] = None
    ) -> Optional[str]:
        """
        Get path where file should be saved with default os GUI pop-up. Returns None on cancel or exit.
            @param name: name of pop-up gui window.
            @param saveType: if True, dialog for selecting save file is created. Otherwise, dialog to open file is created.
            @param folderPath: path to a folder/file where dialog should be open.
                paths.get_default_log_dir() is used by default.
            @param filterExtension: file extension filter (can be merged list: '"*.txt, "*.json", "*.log"')
        """
        if folderPath is None:
            folderPath = paths.get_default_log_dir()
        else:
            folderPath = os.path.normpath(folderPath)

        if filterExtension is None:
            filterExtension = ""

        if saveType:
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, name, folderPath, filterExtension)
        else:
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, name, folderPath, filterExtension)
        if fileName != "":
            fileName = os.path.normpath(fileName)
            return fileName
        else:
            return None

    def confirmActionDialog(
        self,
        name: str,
        question: str,
        icon_type: Optional[QtWidgets.QMessageBox.Icon] = QtWidgets.QMessageBox.Icon.Warning,
    ) -> bool:
        """
        Pop-up system dialog with OK|Cancel options.
        Return True if user respond with click to OK button. Else, return False.
        """
        dialog = QtWidgets.QMessageBox()

        window_icon = QtGui.QIcon()
        window_icon.addPixmap(QtGui.QPixmap(":/icons/icons/SerialTool.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        dialog.setWindowIcon(window_icon)

        if icon_type is not None:
            dialog.setIcon(icon_type)

        dialog.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        dialog.setDefaultButton(QtWidgets.QMessageBox.Ok)
        dialog.setEscapeButton(QtWidgets.QMessageBox.Cancel)

        dialog.setText(question)
        dialog.setWindowTitle(name)

        retval = dialog.exec_()

        return retval == QtWidgets.QMessageBox.Ok

    def _appExceptionHandler(self, excType, excValue, tracebackObj) -> None:
        """
        Global function to catch unhandled exceptions.

        @param excType: exception type
        @param excValue: exception value
        @param tracebackObj: traceback object
        """
        try:
            errorMsg = (
                "\n * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"
            )
            errorMsg += f"\nUnhandled unexpected exception occurred! Program will try to continue with execution."
            errorMsg += f"\n\tExc. type: {excType}"
            errorMsg += f"\n\tExc. value: {excValue}"
            errorMsg += f"\n\tExc. traceback: {traceback.format_tb(tracebackObj)}"
            errorMsg += "\n\n"

            try:
                self.sig_error.emit(errorMsg, defs.LOG_COLOR_ERROR)
            except Exception as err:
                # at least, log to file if log over signal fails
                logging.error(errorMsg)

            self.stopAllSeqThreads()
            self.commHandler.deinitPort()

        except Exception as err:
            logging.error(f"Error in exception handling function.\n{err}")
            self.sigClose.emit()


def init_logger() -> None:
    log_dir = paths.get_default_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, defs.SERIAL_TOOL_LOG_FILENAME)

    fmt = logging.Formatter(defs.LOG_FORMAT, datefmt=defs.LOG_DATETIME_FORMAT)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    std_hdlr = logging.StreamHandler()
    std_hdlr.setLevel(logging.DEBUG)
    std_hdlr.setFormatter(fmt)
    logger.addHandler(std_hdlr)

    file_hdlr = logging.FileHandler(file_path, encoding="utf-8")
    file_hdlr.setFormatter(fmt)
    file_hdlr.setLevel(logging.DEBUG)
    logger.addHandler(file_hdlr)

    logging.info(f"Logger initialized: {file_path}")


def main() -> None:
    init_logger()

    app = QtWidgets.QApplication(sys.argv)
    gui = Gui()
    gui.show()

    ret = app.exec_()

    sys.exit(ret)


if __name__ == "__main__":
    main()
