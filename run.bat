@echo off
set VENV_DIR=.venv

REM Check if .venv exists
if exist %VENV_DIR% (
    echo Activating the virtual environment...
    call %VENV_DIR%\Scripts\activate
) else (
    echo Creating the virtual environment...
    python -m venv %VENV_DIR%
    echo Activating the virtual environment...
    call %VENV_DIR%\Scripts\activate
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run main.py
echo Running main.py...
python stock.py
python updates.py

REM Deactivate the virtual environment
deactivate
