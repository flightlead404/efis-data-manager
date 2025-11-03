@echo off
REM EFIS Data Manager CLI wrapper for Windows

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Execute the Python CLI script
python "%SCRIPT_DIR%efis_cli.py" %*