@echo off
setlocal

REM Setup script for RLBotGUI Python 3.11 virtual environment
REM This script creates the venv if it doesn't exist and installs requirements

set "VENV_DIR=%~dp0venv"
set "REQUIREMENTS_FILE=%~dp0requirements.txt"

echo ========================================
echo RLBotGUI Environment Setup
echo ========================================

REM Try to find Python 3.11 in common locations
set "PYTHON_EXE="

REM First, try using py launcher with version specifier
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%i"
)

REM Second, try common installation paths
if not defined PYTHON_EXE (
    if exist "C:\Program Files\Python311\python.exe" set "PYTHON_EXE=C:\Program Files\Python311\python.exe"
)
if not defined PYTHON_EXE (
    if exist "C:\Python311\python.exe" set "PYTHON_EXE=C:\Python311\python.exe"
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311*\python.exe" for %%i in ("%LOCALAPPDATA%\Programs\Python\Python311*\python.exe") do set "PYTHON_EXE=%%i"
)

REM Check if we found Python 3.11
if not defined PYTHON_EXE (
    echo ERROR: Python 3.11 not found!
    echo.
    echo Please install Python 3.11 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Verify it's actually Python 3.11
"%PYTHON_EXE%" --version 2>nul | findstr /C:"3.11" >nul
if errorlevel 1 (
    echo ERROR: Found Python but it's not version 3.11!
    echo Found: 
    "%PYTHON_EXE%" --version
    echo.
    echo Please install Python 3.11 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

REM Upgrade pip first
echo.
echo Upgrading pip...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet

REM Install/upgrade requirements
echo.
echo Installing requirements from requirements.txt...
if exist "%REQUIREMENTS_FILE%" (
    "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REQUIREMENTS_FILE%" --upgrade
    if errorlevel 1 (
        echo ERROR: Failed to install requirements
        pause
        exit /b 1
    )
    echo Requirements installed successfully!
) else (
    echo WARNING: requirements.txt not found at %REQUIREMENTS_FILE%
    echo Skipping requirements installation.
)

echo.
echo ========================================
echo Setup complete!
echo Virtual environment: %VENV_DIR%
echo ========================================
echo.

REM Export venv path for the caller
set "VIRTUAL_ENV=%VENV_DIR%"
set "PATH=%VENV_DIR%\Scripts;%PATH%"

endlocal
