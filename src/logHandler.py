"""
Common LogHandler interface.

* LogHandler: if set, instance of such logger can log to:
    - console (terminal)
    - file
"""
import datetime
import inspect
import logging
import logging.handlers
import os
import struct
import sys
import threading
import time
import traceback

DEFAULT_NAME = 'root'

# https://docs.python.org/3/library/logging.html#logrecord-attributes
# Numbers after log item (for example: '+8') specify item length and position: +=right -=left aligned
DEFAULT_FORMATTER = "%(name)-8s %(asctime)s.%(msecs)03d %(levelname)+8s: %(message)s"
DEFAULT_FORMATTER_TIME = "%H:%M:%S"

# traceback log data format
INDENTATION_STRING = "  "
FIRST_TRACEBACK_DATA_TITLE = "First exception error data:"
FURTHER_TRACEBACK_DATA_TITLE = "Further traceback data:"
LOG_LOCATION_TITLE = "Log location:"


###################################################################################################
# private, do not modify
_ANOTHER_EXCEPTIONS_STR = "During handling of the above exception, another exception occurred:"
_TRACEBACK_HEAD_TITLE = "Traceback (most recent call last):"

_defaultLogger = None


class LogHandler():
    def __init__(self, loggerName=DEFAULT_NAME, setAsDefault=True):
        """
        This class holds all settings to manage log handler.
            @param loggerName: unique logger name
                If logger with such name already exists, it is overwritten
            @param setAsDefault: if True, created log handler is set as default logger
        """
        self._name = loggerName
        self._isDefaultLogHandler = setAsDefault

        self._logFileName = None
        self._logFolderPath = None
        self._logFilePath = None

        try:
            self.loggers = logging.getLogger(self._name)
            self.loggers.setLevel(logging.DEBUG)  # READ logger docs 'setLevel()'

            # remove all handlers, if this logger instance already exists
            for handle in self.loggers.handlers:
                self.loggers.removeHandler(handle)

            if self._isDefaultLogHandler:
                setDefaultLogHandler(self)

        except Exception as err:
            errorMsg = "Unable to init logger instance:\n" + str(err)
            raise Exception(errorMsg)

    def addConsoleHandler(self, formatter: logging.Formatter = None):
        """
        Add console handler to this logger instance. 
            @param formatter: if not None, override default formatter
        """
        try:
            consoleHandler = logging.StreamHandler()
            consoleHandler.setLevel(logging.DEBUG)

            if formatter is None:
                formatter = logging.Formatter(DEFAULT_FORMATTER, datefmt=DEFAULT_FORMATTER_TIME)
            consoleHandler.setFormatter(formatter)

            self.loggers.addHandler(consoleHandler)

        except Exception as err:
            errorMsg = "Unable to init logging console handler:\n" + str(err)
            raise Exception(errorMsg)

    def addFileHandler(self, fileName=None, folderPath=None, formatter: logging.Formatter = None):
        """
        Add file handler to this logger instance. If log folder does not exist, it is created.
            @param fileName: name of log file
                If None, default fileName is fetched with 'getDefaultLogFileName()'.
            @param folderPath: path to a folder where logs will be storred
                If None, path is fetched with 'getDefaultLogFolderPath()'.
            @param formatter: if not None, override default formatter
        """
        try:
            if fileName is None:
                fileName = getDefaultLogFileName(self._name)
            self._logFileName = fileName
            if folderPath is None:
                folderPath = getDefaultLogFolderPath()
            self._logFolderPath = folderPath
            self._logFilePath = os.path.join(self._logFolderPath, self._logFileName)

            self._createLogFolder()

            fileHandler = logging.FileHandler(self._logFilePath, mode='w', encoding='utf-8')
            fileHandler.setLevel(logging.DEBUG)

            if formatter is None:
                formatter = logging.Formatter(DEFAULT_FORMATTER, datefmt=DEFAULT_FORMATTER_TIME)
            fileHandler.setFormatter(formatter)

            self.loggers.addHandler(fileHandler)

        except Exception as err:
            errorMsg = "Unable to init logging file handler:\n" + str(err)
            raise Exception(errorMsg)

    def isDefaultLogHandler(self):
        """
        Returns True if this logHandler instance is set as process default log handler.
        """
        return self._isDefaultLogHandler

    def getName(self):
        """
        Return this logger instance name.
        Source name is specified only at logger instance creation.
        """
        return self._name

    def getLogFileName(self):
        """
        Return this logger instance log file name (if file handler is set).
        """
        return self._logFileName

    def getLogFolderPath(self):
        """
        Return this logger instance log file folder path (if file handler is set).
        """
        return self._logFolderPath

    def getLogFilePath(self):
        """
        Return this logger instance log file path (if file handler is set).
        """
        return self._logFilePath

    def _createLogFolder(self):
        """
        Create folder on a default/specified path.
        """
        # TODO move any folder creation to pathUtils in common folder
        try:
            os.makedirs(self._logFolderPath, exist_ok=True)
        except Exception as err:
            errorMsg = "Unable to create log folder tree: " + str(self._logFolderPath)
            errorMsg += "\nException:\n" + str(err)
            raise Exception(errorMsg)


###################################################################################################
# Other logging utility functions.
def _checkDefaultLogHandler():
    """
    Check if default log handler already exists and create it if it does not.
    """
    if _defaultLogger is None:
        errorMsg = "No logger instance available."
        raise Exception(errorMsg)


def setDefaultLogHandler(handler: LogHandler):
    """
    Set given handler as a default logger handler.
        @param handler: new default log handler to set
    """
    global _defaultLogger
    _defaultLogger = handler


def getDefaultLogHandler():
    """
    Get default logger handler instance.
    """
    return _defaultLogger


def removeOldLogFiles(logFolder=None, olderThanDays: int = 3):
    """
    Check if given/default log folder contains any files that are older than specified number of days.
        @param logFolder: path to a folder with log files
            If None, path is fetched with 'getDefaultLogFolderPath()'
        @param olderThanDays
    """
    if logFolder is None:
        logFolder = getDefaultLogFolderPath()
    else:
        logFolder = os.path.normpath(logFolder)

    if os.path.exists(logFolder):
        daysInSeconds = olderThanDays * 24 * 60 * 60
        currentTime = time.time()
        for item in os.listdir(logFolder):
            if item.endswith('.log'):
                itemPath = os.path.join(logFolder, item)
                lastModTime = os.path.getmtime(itemPath)
                if lastModTime < (currentTime - daysInSeconds):
                    try:
                        os.remove(itemPath)
                    except Exception as err:
                        errorMsg = "Unable to delete old log file: " + itemPath
                        errorMsg = "\nException:\n" + str(err)
                        print(errorMsg)


def removeAllLogFiles(logFolder=None):
    """
    Remove all files in given/default log folder.
        @param logFolder: path to a folder with log files
            If None, path is fetched with 'getDefaultLogFolderPath()'
    """
    removeOldLogFiles(logFolder, olderThanDays=0)


def getDefaultLogFileName(loggerName):
    """
    Get default log file name: <logerName>_<date>_<time>.log
        @param loggerName: name of a logger
    """
    today = datetime.datetime.now()
    logFileName = loggerName + '_{}-{}-{}_{}-{}-{}.log'.format(today.day, today.month, today.year,
                                                               today.hour, today.minute, today.second)

    return logFileName


def getDefaultLogFolderPath():
    """
    Get default log folder path: <cwd>/log
    """
    logFolderPath = os.path.join(os.getcwd(), 'log')
    return logFolderPath


###################################################################################################

###################################################################################################
# traceback data handler
def _filterRelevantStackEntries(frames):
    """
    Filter stack entries of unwanted python modules, like interpretter runner or debugger modules.
    """
    FILTER_ENTRIES_OF_SOURCE_FILES = ['runpy.py', 'ptvsd', '__main__.py']

    relevantFrames = []
    for frame in frames:
        filePath = frame.filename
        for filterItem in FILTER_ENTRIES_OF_SOURCE_FILES:
            if filterItem in filePath:
                break
        else:
            relevantFrames.append(frame)

    return relevantFrames


def _getTracebackPartsFromLines(tracebackLines: list):
    """
    Get traceback blocks (parts) from default traceback.format_exc() data lines.
        @param tracebackLines: list of lines from traceback.format_exc()
    """

    tracebackParts = []
    thisPartData = []

    for line in tracebackLines:
        line = line.strip()
        if line != '':
            if line not in [_TRACEBACK_HEAD_TITLE, _ANOTHER_EXCEPTIONS_STR]:
                if line.find("File \"") != -1:
                    # 'File "' string found, new traceback part
                    if thisPartData:  # add last part
                        tracebackParts.append(thisPartData)
                    thisPartData = [line]
                else:
                    thisPartData.append(INDENTATION_STRING + line)
    tracebackParts.append(thisPartData)  # append the last block

    return tracebackParts


def _getTracebackPartString(tracebackPart, partDepth):
    """
    Get traceback block as a string.
        @param tracebackPart:
        @param partDepth: add partDepth of INDENTATION_STRING to each traceback part line

    """
    partStr = ""
    for line in tracebackPart:
        line = _formatExceptionTracebackline(line)
        partStr += INDENTATION_STRING * partDepth
        partStr += line + "\n"
    return partStr


def _formatExceptionTracebackline(tracebackLine):
    """
    Convert traceback location format to a custom format.
        @param tracebackLine: traceback data line in default format
    """
    # New format: <file>:<lineNumber> in <function>
    # tracebackLine = tracebackLine.replace("File \"", "")
    # tracebackLine = tracebackLine.replace("\", line ", ":")
    # tracebackLine = tracebackLine.replace(", in ", " in ")

    return tracebackLine


def getCallingFunctionLocation(ignoreDepth=2):
    """
    Get location of a function that called function that called this function.
        @param ignoreDepth: this number of stack entries are ignored
            1 by default means that function that called this function is not accounted.

    someFunction() [file a.py]
        var = b.myFunction() [file a.py, line 42] (*)

    myFunction()) [file b.py]
        <thisFile>.getCallingFunctionLocation() [file b.py, line 6] 
            -> will return location of (*) = [file a.py, line 42]

    Format: 
    LOG_LOCATION_TITLE <filePath>:<lineNumber>

    # https://docs.python.org/3/library/inspect.html
    """
    stackFrames = inspect.stack()
    stackFrames = _filterRelevantStackEntries(stackFrames)
    if len(stackFrames) > ignoreDepth:
        stackFrames = stackFrames[ignoreDepth:]  # ignore first [0] stack entry - this function
        logLocation = str(stackFrames[0].filename) + ':' + str(stackFrames[0].lineno)
        logLocationStr = LOG_LOCATION_TITLE + " " + logLocation + "\n"

        return logLocationStr
    else:
        return ''


def getErrorTraceback(verboseTraceback=False):
    """
    Get a string of a beautified traceback data.
        @param verboseTraceback: if True, all traceback stack data is displayed. Otherwise, only first
            traceback entry is returned.

    Format: 
    FIRST_TRACEBACK_DATA_TITLE
    location
      data

      FURTHER_TRACEBACK_DATA_TITLE (if <verboseTraceback=True>)
      location
        data
      location
        data
      ...

    NOTE: As it turned out, manually building stack data trace inspect.stack(), .trace() and sys.exc_info()
        is complicated, so current implementation just analyze lines of traceback data, fetched
        with traceback.format_exc().
    """
    tracebackStr = ''

    tbData = sys.exc_info()[1]
    if tbData is not None:
        # exception data is available
        firstExceptionTracebackParts = None
        otherExceptionsTracebackParts = None

        tracebackData = traceback.format_exc().splitlines()
        tracebackStr = FIRST_TRACEBACK_DATA_TITLE + "\n"

        # prepare traceback data parts
        for lineIndex, line in enumerate(tracebackData):
            line = line.strip()
            if _ANOTHER_EXCEPTIONS_STR in line:
                firstExceptionTracebackParts = _getTracebackPartsFromLines(tracebackData[:lineIndex])
                if verboseTraceback:
                    otherExceptionsTracebackParts = _getTracebackPartsFromLines(tracebackData[lineIndex:])
                break
        else:
            # if no exception was re-raised, only one (first) traceback data is available
            firstExceptionTracebackParts = _getTracebackPartsFromLines(tracebackData)

        # create log data tab-ed and in reverse order - error first
        firstExceptionTracebackParts = firstExceptionTracebackParts[::-1]  # reverse
        for partIndex, part in enumerate(firstExceptionTracebackParts):
            if partIndex:
                tracebackStr += _getTracebackPartString(part, 1)
            else:
                tracebackStr += _getTracebackPartString(part, 0)

        if otherExceptionsTracebackParts is not None:
            tracebackStr += "\n" + INDENTATION_STRING + FURTHER_TRACEBACK_DATA_TITLE + "\n"
            # otherExceptionsTracebackParts = otherExceptionsTracebackParts[::-1]  # reverse
            for partIndex, part in enumerate(otherExceptionsTracebackParts):
                tracebackStr += _getTracebackPartString(part, 1)

    return tracebackStr


###################################################################################################
# LOGGING FUNCTIONS. Use first logger instance (handler) by default.
def debug(dMsg, handler: LogHandler = None):
    """
    Log with 'DEBUG' level.
        @param dMsg: message to log
        @param handler: use specific handler, otherwise use default log handler
    """
    dMsg = str(dMsg)
    if handler is None:
        _checkDefaultLogHandler()
        handler = _defaultLogger

    handler.loggers.debug(dMsg)


def info(iMsg, handler: LogHandler = None):
    """
    Log with 'INFO' level.
        @param iMsg: message to log
        @param handler: use specific handler, otherwise use default log handler
    """
    iMsg = str(iMsg)
    if handler is None:
        _checkDefaultLogHandler()
        handler = _defaultLogger

    handler.loggers.info(iMsg)


def warning(wMsg, handler: LogHandler = None):
    """
    Log with 'WARNING' level.
        @param wMsg: message to log
        @param handler: use specific handler, otherwise use default log handler
    """
    wMsg = str(wMsg)
    if handler is None:
        _checkDefaultLogHandler()
        handler = _defaultLogger

    handler.loggers.warning(wMsg)


def error(eMsg, showTraceback=False, verboseTraceback=False, handler: LogHandler = None, ignoreCallerFuncDepth=2):
    """
    Log with 'ERROR' level.
        @param eMsg: message to log
        @param showTraceback: if True, error traceback is added to message
        @param verboseTraceback: if True, complete traceback is displayed, otherwise only last stack entry
            Only valid if 'showTraceback' is set to True.
        @param handler: use specific handler, otherwise use default log handler
    """
    eMsg = str(eMsg)
    if handler is None:
        _checkDefaultLogHandler()
        handler = _defaultLogger

    if showTraceback:
        tbStr = getErrorTraceback(verboseTraceback)
        if tbStr != '':
            locStr = getCallingFunctionLocation(ignoreCallerFuncDepth)
            eMsg = eMsg + "\n" + tbStr + locStr
    handler.loggers.error(eMsg)


def criticalError(cMsg, verboseTraceback=False, handler: LogHandler = None, ignoreCallerFuncDepth=2):
    """
    Log with 'CRITICAL' level, always add error traceback
        @param cMsg: message to log
        @param verboseTraceback: if True, complete traceback is displayed, otherwise only last stack entry
            Only valid if 'showTraceback' is set to True.
        @param handler: use specific handler, otherwise use default log handler
    """
    cMsg = str(cMsg)
    if handler is None:
        _checkDefaultLogHandler()
        handler = _defaultLogger

    tbStr = getErrorTraceback(verboseTraceback)
    if tbStr != '':
        locStr = getCallingFunctionLocation(ignoreCallerFuncDepth)
        cMsg = cMsg + "\n" + tbStr + locStr

    handler.loggers.critical(cMsg)


if __name__ == "__main__":
    """
    Test logHandler by creating two loggers, where:
    - both logs to a file
    - only one logs to console
    """
    # removeAllLogFiles()
    # removeOldLogFiles()

    # create one logger (which will also be automatically set as default logger)
    testLog = LogHandler()  # default name, see getDefaultLogFileName()
    testLog.addConsoleHandler()
    testLog.addFileHandler()

    # additional logger, only logs to file
    secondTestLog = LogHandler('root2', setAsDefault=False)
    secondTestLog.addFileHandler()
    # secondTestLog.addConsoleHandler()

    # test some log inspect files and console
    info("Default loger")
    info("Additional logger", handler=secondTestLog)
    debug("Debugging debugger that debugs a debugger")
    warning("Security Alert - Moving cursor is not as safe as you thought.")
    error("Keyboard not detected, press F5 to continue")

    # some nested exceptions to check traceback logging
    try:
        try:
            try:

                #raise ValueError('404')
                customFailingLine  # some incorrect syntax

            except Exception as err:
                errorMsg = "First caught exception!"
                raise Exception(errorMsg)
        except:
            raise

    except Exception as err:
        errorMsg = "Some caught \'unexpected\' exception!"
        error(errorMsg, True)
        criticalError("\n\nRun as fast as you can", handler=secondTestLog)
        print()
        criticalError("\n\nWith verbose traceback", verboseTraceback=True, handler=secondTestLog)
