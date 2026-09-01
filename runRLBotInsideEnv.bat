@echo off
REM RLBotGUI Launcher
REM This script sets up the Python 3.11 virtual environment and runs RLBotGUI

set "VENV_DIR=%~dp0venv\Scripts\python.exe"

REM Check if venv exists
if exist "%VENV_DIR%" (
    echo Virtual environment found, skipping setup...
    goto RUN_GUI
)

echo Virtual environment not found, running setup...
call "%~dp0setup_venv.bat"
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Setup failed!
    echo ========================================
    echo.
    echo Please run setup_venv.bat manually to resolve issues.
    echo Then try running this script again.
    echo.
    exit /b 1
)

:RUN_GUI
REM Now run the GUI using the venv Python
"%VENV_DIR%" "%~dp0run.py"
