@echo off

SET PY_EXE_PATH="C:\Python311\python.exe"

SET VENV_NAME=venv_py311

cd ..

%PY_EXE_PATH% -m venv %VENV_NAME%

CALL "%VENV_NAME%/Scripts/activate.bat"

python -m pip install -U pip
python -m pip install -U -r requirements_dev.txt
python -m pip install -e .
pause