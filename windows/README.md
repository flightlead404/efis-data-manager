# EFIS Data Manager - Windows Installation Guide

This guide provides detailed instructions for installing and configuring the EFIS Data Manager Windows service.

## Overview

The Windows component of EFIS Data Manager provides:
- Automatic virtual USB drive mounting using ImDisk
- Continuous drive monitoring with auto-remount capabilities
- Windows service for background operation
- Chart data synchronization with macOS system
- Comprehensive logging and health monitoring

## Prerequisites

### System Requirements
- Windows 10/11 with administrator privileges
- Python 3.8 or higher
- At least 2GB free disk space
- Network connectivity (for sync with macOS)

### Required Software
1. **ImDisk Toolkit** - For virtual drive mounting
2. **Python** - Runtime environment
3. **Git** (optional) - For source code management

## Installation Steps

### 1. Install ImDisk Toolkit

ImDisk is required for mounting VHD files as virtual drives.

1. Download ImDisk Toolkit from: https://sourceforge.net/projects/imdisk-toolkit/
2. Run the installer **as Administrator**
3. Accept default installation options
4. Verify installation by opening Command Prompt and running:
   ```cmd
   "C:\Program Files\ImDisk\MountImg.exe" /?
   ```
   You should see the ImDisk help text.

### 2. Install Python Dependencies

Open Command Prompt **as Administrator** and navigate to the project directory:

```cmd
cd path\to\efis-data-manager\windows
```

Install required Python packages:
```cmd
pip install pywin32 colorlog pyyaml pathlib
```

### 3. Configure the Service

#### Create Configuration File

The service uses a JSON configuration file. Copy the example configuration:

```cmd
copy ..\config\windows-config.json ..\config\windows-config.json
```

#### Edit Configuration

Open the configuration file in a text editor:
```cmd
notepad ..\config\windows-config.json
```

Update the following settings:

```json
{
  "virtualDrive": {
    "vhdPath": "C:\\Users\\YourUsername\\OneDrive\\Desktop\\virtualEFISUSB.vhd",
    "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",
    "driveLetter": "E:",
    "logFile": "C:\\Scripts\\MountEFIS.log"
  },
  "sync": {
    "interval": 1800,
    "macbookIP": "192.168.1.100",
    "retryAttempts": 3,
    "retryDelay": 600
  },
  "monitoring": {
    "checkInterval": 300,
    "remountRetryDelay": 60,
    "maxConsecutiveFailures": 5
  },
  "logging": {
    "level": "INFO",
    "file": "C:\\Scripts\\efis-data-manager.log",
    "maxSize": "10MB",
    "backupCount": 5
  }
}
```

**Important Configuration Notes:**
- `vhdPath`: Full path to your VHD file
- `driveLetter`: Drive letter to mount the VHD (must include colon)
- `macbookIP`: IP address of your macOS system (for sync)
- `checkInterval`: How often to check drive status (seconds)

### 4. Install the Windows Service

**Important:** This step must be run as Administrator.

```cmd
python install_service.py install
```

If successful, you should see:
```
Installing EFIS Data Manager Service...
Service installed successfully
```

### 5. Start the Service

```cmd
python install_service.py start
```

Verify the service is running:
```cmd
python install_service.py status
```

You should see: `Service status: Running`

## Testing and Verification

### Using the CLI Tool

The Windows installation includes a command-line tool for testing and management:

```cmd
# Check drive status
python drive_manager_cli.py status

# Perform health check
python drive_manager_cli.py health

# Manually mount drive
python drive_manager_cli.py mount

# Start interactive monitoring
python drive_manager_cli.py monitor
```

### Check Service Logs

View the service logs to ensure everything is working:
```cmd
type C:\Scripts\efis-data-manager.log
```

Look for messages like:
```
2024-01-01 12:00:00 - windows-service - INFO - EFIS Data Manager Service started successfully
2024-01-01 12:00:05 - windows-service - INFO - Virtual drive is properly mounted
2024-01-01 12:00:05 - windows-service - INFO - Drive monitor started successfully
```

### Windows Services Manager

You can also check the service status using Windows Services:

1. Press `Win + R`, type `services.msc`, press Enter
2. Look for "EFIS Data Manager Service"
3. Status should show "Running"

## Service Management

### Common Commands

```cmd
# Check service status
python install_service.py status

# Start service
python install_service.py start

# Stop service
python install_service.py stop

# Restart service
python install_service.py restart

# Remove service (stops first)
python install_service.py remove
```

### Service Configuration

The service automatically:
- Mounts the virtual drive on startup
- Monitors drive status every 5 minutes
- Attempts automatic remounting if drive is lost
- Logs all operations to the configured log file
- Synchronizes with macOS system (if configured)

## Troubleshooting

### Service Won't Install

**Error:** "Access denied" or "Permission denied"
- **Solution:** Run Command Prompt as Administrator

**Error:** "Python module not found"
- **Solution:** Install missing dependencies: `pip install pywin32`

### Service Won't Start

**Check the Windows Event Log:**
1. Open Event Viewer (`eventvwr.msc`)
2. Navigate to Windows Logs > Application
3. Look for errors from "EFISDataManager"

**Common Issues:**
- **VHD file not found:** Check the `vhdPath` in configuration
- **ImDisk not installed:** Reinstall ImDisk Toolkit
- **Drive letter in use:** Change `driveLetter` in configuration
- **Invalid configuration:** Validate JSON syntax

### Drive Won't Mount

```cmd
# Test ImDisk directly
"C:\Program Files\ImDisk\MountImg.exe" -a -f "C:\path\to\your.vhd" -m E:

# Check if drive letter is available
dir E:

# Use CLI tool for diagnosis
python drive_manager_cli.py health
```

### Performance Issues

**Slow mounting or monitoring:**
- Check VHD file location (local vs network drive)
- Increase `checkInterval` in configuration
- Check system resources and disk space

### Network Sync Issues

**Cannot connect to macOS system:**
- Verify both systems are on same network
- Test connectivity: `ping 192.168.1.100`
- Check firewall settings on both systems
- Verify macOS system is running EFIS Data Manager

## Advanced Configuration

### Custom Log Locations

To change log file location, update the configuration:
```json
{
  "logging": {
    "file": "D:\\Logs\\efis-data-manager.log"
  }
}
```

### Multiple VHD Files

To manage multiple VHD files, you can:
1. Run multiple service instances with different configurations
2. Use the CLI tool to manually switch between VHDs
3. Modify the configuration and restart the service

### Monitoring Integration

The service provides callbacks for integration with monitoring systems:
- Mount success/failure events
- Drive health status
- Performance metrics
- Error notifications

## Uninstallation

To completely remove the EFIS Data Manager:

```cmd
# Stop and remove service
python install_service.py stop
python install_service.py remove

# Remove log files (optional)
del C:\Scripts\efis-data-manager.log*

# Remove configuration (optional)
del ..\config\windows-config.json
```

## Support

### Log Files
- Service logs: `C:\Scripts\efis-data-manager.log`
- Windows Event Log: Application log, source "EFISDataManager"
- Installation log: `service_install.log`

### Diagnostic Commands
```cmd
# Full system health check
python drive_manager_cli.py health -v

# List all ImDisk drives
python drive_manager_cli.py list

# Interactive monitoring with statistics
python drive_manager_cli.py monitor --stats
```

### Getting Help
1. Check log files for detailed error messages
2. Verify all prerequisites are installed correctly
3. Test individual components using the CLI tool
4. Ensure configuration file is valid JSON
5. Check Windows Event Viewer for system-level errors

For additional support, include the following information:
- Windows version and build
- Python version (`python --version`)
- ImDisk version
- Service logs
- Configuration file (remove sensitive information)
- Error messages from Event Viewer