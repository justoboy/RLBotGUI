@echo off
REM RLBotGUI Launcher
REM This script sets up the Python 3.11 virtual environment and runs RLBotGUI

REM First, run the setup script to create/verify the venv
call "%~dp0setup_venv.bat"
if errorlevel 1 (
    echo Setup failed!
    pause
    exit /b 1
)

REM Now run the GUI using the venv Python
"%~dp0venv\Scripts\python.exe" "%~dp0run.py"
