# EFIS Data Manager

A cross-platform system that automates the management of aviation chart data, navigation databases, logging data, and software updates between a MacBook Pro, Windows 11 machine, and aircraft EFIS systems via USB drives.

## Overview

The EFIS Data Manager consists of two main components:
- **Windows Service**: Manages virtual USB drive mounting and chart data synchronization
- **macOS Daemon**: Handles GRT software downloads, USB drive processing, and file orchestration

## Architecture

- Windows 11 system runs Chart Manager and maintains virtual USB drive
- macOS system manages USB drives, downloads GRT updates, and archives flight data
- Network synchronization keeps chart data current between systems
- Automated processing of EFIS USB drives for data archival and updates

## Components

### Windows Component (`src/windows/`)
- Virtual drive management using ImDisk
- Network synchronization client
- Windows service framework

### macOS Component (`src/macos/`)
- GRT website scraping and downloads
- USB drive detection and processing
- File archive management
- Notification system

### Shared Components (`src/shared/`)
- Configuration management
- Logging utilities
- Data models and interfaces

## Requirements

- Windows 11 with ImDisk installed
- macOS with Python 3.8+
- Network connectivity between systems
- USB drive access

## Installation

See `docs/installation.md` for detailed setup instructions.

## Configuration

Configuration files are located in `config/` directory:
- `windows-config.json`: Windows service settings
- `macos-config.json`: macOS daemon settings

## Usage

### Windows Service
```bash
# Install and start service
python src/windows/service_installer.py install
python src/windows/service_installer.py start
```

### macOS Daemon
```bash
# Install daemon
sudo python src/macos/daemon_installer.py install
# Start daemon
launchctl load ~/Library/LaunchAgents/com.efis.datamanager.plist
```

## Development

### Setup Development Environment
```bash
# Create virtual environments
python -m venv venv-windows
python -m venv venv-macos

# Install dependencies
pip install -r requirements-windows.txt
pip install -r requirements-macos.txt
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific component tests
python -m pytest tests/windows/
python -m pytest tests/macos/
```

## Logging

Logs are stored in:
- Windows: `C:\Scripts\efis-data-manager.log`
- macOS: `~/Library/Logs/efis-data-manager.log`

## License

MIT License - see LICENSE file for details.