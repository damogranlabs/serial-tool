# Changelog:  
**v2.3 (8.12.2019):**
- fix: serial read with asyncio (low CPU usage)
- improv: added "\n" control on RX data
- improv: configuration loading with better backward compatibility

**v2.2 (16.11.2019):**
- fix: log window scroll issue on text selection
  
**v2.1 (16.11.2019):**
- fix: RT/TX checkbox, log message exception handler
- improv: note font more readable (now black)

**v2 (3.11.2019):**
- REWRITE: v2.0
- MVC architecture (appropriate use of PyQt signals and slots)
- data/sequence validator
- RX background thread
- log window settings, export capabilities

**v1.5 (14.10.2019):**
- improv: restructured repository
- fix: new configuration load

**v1.4 (10.10.2019):**
- Python 3.7
- added string output representation
- improv: output representation stored to config file
- added VS Code workspace files
- improv: changed default save/load config path

**v1.3 (3.11.2018):**
- updated icons, minor GUI updates
- added utility scripts and .bat files
- added screenshots


**v1.2 (7.2.2018):**
- port to Python v3.6 and PyQt5
- improv: updated hex/ascii log write-out
- improv: added cx_freeze distribution (see sourceforge)
- fix: buttons blackout
- improv: icon

**v1.1 (25.6.2017):**
- fix: minor bug fixes and code formatting
- fix: updated serial methods (read, write, in_waiting)
- improv: py2exe distribution added

**v1.0 - initial release (24.4.2017)**
- python v2.7, pyqt4