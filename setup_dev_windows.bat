@echo off
REM Development setup script for Windows EFIS Data Manager component

echo Setting up Windows EFIS Data Manager development environment...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Navigate to Windows component directory
cd windows

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Install in development mode
echo Installing Windows component in development mode...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install Windows component
    pause
    exit /b 1
)

echo.
echo Windows EFIS Data Manager development environment setup complete!
echo.
echo To activate the environment in the future, run:
echo   cd windows
echo   venv\Scripts\activate.bat
echo.
echo To run the service in development mode:
echo   python src\efis_windows\service.py
echo.
pause