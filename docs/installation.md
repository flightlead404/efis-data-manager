# Installation Guide

This guide covers the installation and setup of the EFIS Data Manager on both Windows 11 and macOS systems.

## Prerequisites

### Windows 11 System
- Windows 11 with administrator privileges
- Python 3.8 or higher
- ImDisk Toolkit installed
- Seattle Avionics Chart Manager (optional, for chart data)
- Network connectivity to macOS system

### macOS System
- macOS 10.15 (Catalina) or higher
- Python 3.8 or higher
- Xcode Command Line Tools
- Network connectivity to Windows system
- USB port access for EFIS drives

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/efis-data-manager.git
cd efis-data-manager
```

### 2. Windows Installation

#### Install ImDisk Toolkit
1. Download ImDisk Toolkit from: https://sourceforge.net/projects/imdisk-toolkit/
2. Run installer as administrator
3. Verify installation: `"C:\Program Files\ImDisk\MountImg.exe" /?`

#### Set up Python Environment
```cmd
# Create virtual environment
python -m venv venv-windows
venv-windows\Scripts\activate

# Install dependencies
pip install -r requirements-windows.txt
pip install -e .[windows]
```

#### Configure Windows Service
```cmd
# Navigate to Windows directory
cd windows

# Copy configuration template (if needed)
copy ..\config\windows-config.json ..\config\windows-config-local.json

# Edit configuration file with your specific paths
notepad ..\config\windows-config.json

# Install required Python packages for Windows service
pip install pywin32 colorlog

# Install Windows service (run as Administrator)
python install_service.py install

# Start service
python install_service.py start
```

### 3. macOS Installation

#### Install Dependencies
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Create virtual environment
python3 -m venv venv-macos
source venv-macos/bin/activate

# Install dependencies
pip install -r requirements-macos.txt
pip install -e .[macos]
```

#### Configure macOS Daemon
```bash
# Copy configuration template
cp config/macos-config.json config/macos-config-local.json

# Edit configuration file with your specific paths
nano config/macos-config-local.json

# Install daemon
sudo python src/macos/daemon_installer.py install

# Start daemon
launchctl load ~/Library/LaunchAgents/com.efis.datamanager.plist
```

## Configuration

### Windows Configuration (`config/windows-config-local.json`)

```json
{
  "virtualDrive": {
    "vhdPath": "C:\\Users\\YourUser\\OneDrive\\Desktop\\virtualEFISUSB.vhd",
    "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",
    "driveLetter": "E:",
    "logFile": "C:\\Scripts\\MountEFIS.log"
  },
  "sync": {
    "interval": 1800,
    "macbookIP": "192.168.1.100",
    "retryAttempts": 3,
    "retryDelay": 600
  }
}
```

### macOS Configuration (`config/macos-config-local.json`)

```json
{
  "paths": {
    "archivePath": "/Users/yourusername/Library/CloudStorage/Dropbox/Flying/EFIS-USB",
    "demoPath": "/Users/yourusername/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO",
    "logbookPath": "/Users/yourusername/Library/CloudStorage/Dropbox/Flying/Logbooks"
  }
}
```

## Verification

### Windows System
```cmd
# Check service status
python windows\install_service.py status

# Or use Windows service manager
sc query EFISDataManager

# View logs
type C:\Scripts\efis-data-manager.log

# Test virtual drive operations using CLI
cd windows
python drive_manager_cli.py status
python drive_manager_cli.py health
python drive_manager_cli.py mount
```

### macOS System
```bash
# Check daemon status
launchctl list | grep com.efis.datamanager

# View logs
tail -f ~/Library/Logs/efis-data-manager.log

# Test USB detection
python -c "from src.macos.usb_processor import USBDriveProcessor; print('USB processor ready')"
```

## Troubleshooting

### Common Issues

#### Windows: Service Won't Start
- Verify ImDisk is installed correctly
- Check that VHD file path exists
- Ensure service is running as administrator
- Check Windows Event Viewer for detailed errors

#### macOS: Daemon Won't Load
- Verify Python path in plist file
- Check file permissions on daemon script
- Ensure configuration file is valid JSON
- Check Console app for system errors

#### Network Connectivity Issues
- Verify both systems are on same network
- Test ping between systems
- Check firewall settings
- Verify IP addresses in configuration

### Log Locations
- Windows: `C:\Scripts\efis-data-manager.log`
- macOS: `~/Library/Logs/efis-data-manager.log`

### Getting Help
- Check log files for detailed error messages
- Verify all prerequisites are installed
- Ensure configuration files are valid JSON
- Test individual components before full system integration

## Uninstallation

### Windows
```cmd
# Stop and remove service
cd windows
python install_service.py stop
python install_service.py remove

# Remove virtual environment
cd ..
rmdir /s venv-windows
```

### macOS
```bash
# Unload daemon
launchctl unload ~/Library/LaunchAgents/com.efis.datamanager.plist

# Remove daemon
sudo python src/macos/daemon_installer.py remove

# Remove virtual environment
rm -rf venv-macos
```