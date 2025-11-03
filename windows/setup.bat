@echo off
REM EFIS Data Manager Windows Setup Script
REM This script automates the installation process

echo ========================================
echo EFIS Data Manager Windows Setup
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click on this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Checking prerequisites...

REM Check Python installation
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check ImDisk installation
if not exist "C:\Program Files\ImDisk\MountImg.exe" (
    echo ERROR: ImDisk Toolkit is not installed
    echo Please download and install from: https://sourceforge.net/projects/imdisk-toolkit/
    pause
    exit /b 1
)

echo ImDisk Toolkit found

REM Install Python dependencies
echo.
echo Installing Python dependencies...
pip install pywin32 colorlog pyyaml pathlib
if %errorLevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

REM Check if configuration exists
if not exist "..\config\windows-config.json" (
    echo.
    echo Creating default configuration file...
    if not exist "..\config" mkdir "..\config"
    
    echo {> "..\config\windows-config.json"
    echo   "virtualDrive": {>> "..\config\windows-config.json"
    echo     "vhdPath": "C:\\Users\\%USERNAME%\\OneDrive\\Desktop\\virtualEFISUSB.vhd",>> "..\config\windows-config.json"
    echo     "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",>> "..\config\windows-config.json"
    echo     "driveLetter": "E:",>> "..\config\windows-config.json"
    echo     "logFile": "C:\\Scripts\\MountEFIS.log">> "..\config\windows-config.json"
    echo   },>> "..\config\windows-config.json"
    echo   "sync": {>> "..\config\windows-config.json"
    echo     "interval": 1800,>> "..\config\windows-config.json"
    echo     "macbookIP": "192.168.1.100",>> "..\config\windows-config.json"
    echo     "retryAttempts": 3,>> "..\config\windows-config.json"
    echo     "retryDelay": 600>> "..\config\windows-config.json"
    echo   },>> "..\config\windows-config.json"
    echo   "monitoring": {>> "..\config\windows-config.json"
    echo     "checkInterval": 300,>> "..\config\windows-config.json"
    echo     "remountRetryDelay": 60,>> "..\config\windows-config.json"
    echo     "maxConsecutiveFailures": 5>> "..\config\windows-config.json"
    echo   },>> "..\config\windows-config.json"
    echo   "logging": {>> "..\config\windows-config.json"
    echo     "level": "INFO",>> "..\config\windows-config.json"
    echo     "file": "C:\\Scripts\\efis-data-manager.log",>> "..\config\windows-config.json"
    echo     "maxSize": "10MB",>> "..\config\windows-config.json"
    echo     "backupCount": 5>> "..\config\windows-config.json"
    echo   }>> "..\config\windows-config.json"
    echo }>> "..\config\windows-config.json"
    
    echo Configuration file created at: ..\config\windows-config.json
    echo.
    echo IMPORTANT: Please edit this file to match your system:
    echo - Update the VHD file path
    echo - Set the correct macOS IP address
    echo - Adjust drive letter if needed
    echo.
    set /p continue="Press Enter to continue after editing the configuration file..."
)

REM Create log directory
if not exist "C:\Scripts" mkdir "C:\Scripts"

REM Install the service
echo.
echo Installing Windows service...
python install_service.py install
if %errorLevel% neq 0 (
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

echo Service installed successfully!

REM Ask if user wants to start the service now
echo.
set /p startservice="Do you want to start the service now? (y/n): "
if /i "%startservice%"=="y" (
    echo Starting service...
    python install_service.py start
    if %errorLevel% neq 0 (
        echo ERROR: Failed to start service
        echo Check the configuration and try: python install_service.py start
        pause
        exit /b 1
    )
    
    echo.
    echo Service started successfully!
    
    REM Show service status
    echo.
    echo Current service status:
    python install_service.py status
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Verify your VHD file exists at the configured path
echo 2. Test the drive mounting: python drive_manager_cli.py status
echo 3. Check service logs: type C:\Scripts\efis-data-manager.log
echo 4. Monitor drive health: python drive_manager_cli.py health
echo.
echo Service management commands:
echo - Check status: python install_service.py status
echo - Start service: python install_service.py start
echo - Stop service: python install_service.py stop
echo - Restart service: python install_service.py restart
echo.
echo For detailed help, see: README.md
echo.
pause