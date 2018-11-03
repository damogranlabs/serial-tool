# Serial Tool
Serial Tool is a utility tool for embedded projects that allows you to set up predefined data and send it to your device over chosen serial port with few extra features.

## Features
*  Data types: bytes, characters, integers, arrays
*  Add notes to each data slot
*  Send sequence of data slots, set up delay between different serial writes
*  Save/load data to configuration file
*  Read all available data
*  Display RX data in HEX or ASCII 
*  Compatible with python v3 and PyQt5.
  
More: http://damogranlabs.com/2017/05/serial-tool/  
Example video: https://www.youtube.com/watch?v=l7cXWDq-Eac

## Windows build
Executable (zip ~ 50MB) is available on Source Forge: http://sourceforge.net/p/serial-tool  

![Serial Tool 1](screenshots/1.png)
![Serial Tool 2](screenshots/2.png)
![Serial Tool 3](screenshots/3.png)
![Serial Tool 4](screenshots/blank.png)

---
### Changelog:  
**v1.3 (3.11.2018):**
- updated icons, minor GUI updates
- added utility scripts and .bat files
- added screenshots


**v1.2 (7.2.2018):**
- port to Python v3.6 and PyQt5
- improv: updated hex/ascii log writeout
- improv: added cx_freeze distribution (see sourceforge)
- fix: buttons blackout
- improv: icon

**v1.1 (25.6.2017):**
- fix: minor bug fixes and code formatting
- fix: updated serial methods (read, write, in_waiting)
- improv: py2exe distribution added

**v1.0 - initial release (24.4.2017)**
- python v2.7, pyqt4