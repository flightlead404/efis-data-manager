# EFIS Data Manager CLI Usage Guide

This document describes how to use the command-line interface tools for the EFIS Data Manager system.

## Overview

The EFIS Data Manager provides CLI tools for both macOS and Windows platforms:

- **macOS**: `macos/efis_cli.py` or `macos/efis` wrapper script
- **Windows**: `windows/efis_cli.py` or `windows/efis.bat` wrapper script

## Installation

### macOS
```bash
# Make the CLI executable
chmod +x macos/efis_cli.py
chmod +x macos/efis

# Optionally, create a symlink for system-wide access
sudo ln -s /path/to/efis-data-manager/macos/efis /usr/local/bin/efis
```

### Windows
```cmd
# Add the Windows directory to your PATH, or run directly:
windows\efis.bat --help
```

## Common Commands

### System Status
Check the overall system status:

```bash
# macOS
./macos/efis status

# Windows
windows\efis.bat status

# JSON output
./macos/efis status --json
```

### USB Drive Preparation (macOS only)
Prepare a new EFIS USB drive with current chart data and software:

```bash
# Prepare USB drive
./macos/efis prepare-usb /Volumes/EFIS_USB

# Force preparation even if drive has existing data
./macos/efis prepare-usb /Volumes/EFIS_USB --force
```

### Manual Synchronization
Trigger manual file synchronization:

```bash
# macOS
./macos/efis sync --target 192.168.1.100

# Windows
windows\efis.bat sync --target 192.168.1.100
```

### GRT Software Updates (macOS only)
Check for GRT software updates:

```bash
./macos/efis check-updates
```

### Log Viewing
View system logs:

```bash
# View last 50 lines
./macos/efis logs

# View last 100 lines
./macos/efis logs --lines 100

# Filter by component
./macos/efis logs --component grt

# Windows
windows\efis.bat logs --lines 50
```

### Configuration Management
Manage system configuration:

```bash
# Show current configuration
./macos/efis config show

# Get specific configuration value
./macos/efis config get archive_path

# Windows - nested keys
windows\efis.bat config get virtualDrive.driveLetter

# Set configuration value (not yet implemented)
./macos/efis config set key value
```

### System Diagnostics
Run comprehensive system diagnostics:

```bash
# macOS
./macos/efis diagnostics

# Windows
windows\efis.bat diagnostics
```

## Windows-Specific Commands

### Virtual Drive Management
```cmd
# Check virtual drive status
windows\efis.bat drive status

# Mount virtual drive
windows\efis.bat drive mount

# Force mount even if already mounted
windows\efis.bat drive mount --force

# Unmount virtual drive
windows\efis.bat drive unmount
```

### Windows Service Management
```cmd
# Check service status
windows\efis.bat service status

# Start service
windows\efis.bat service start

# Stop service
windows\efis.bat service stop

# Install service
windows\efis.bat service install

# Uninstall service
windows\efis.bat service uninstall
```

## Global Options

All commands support these global options:

- `--config, -c`: Specify custom configuration file path
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help information

## Examples

### Complete USB Drive Setup (macOS)
```bash
# 1. Check system status
./macos/efis status

# 2. Check for GRT updates
./macos/efis check-updates

# 3. Prepare USB drive
./macos/efis prepare-usb /Volumes/EFIS_USB

# 4. Verify preparation
./macos/efis status
```

### Windows Service Setup
```cmd
# 1. Check system status
windows\efis.bat status

# 2. Install and start service
windows\efis.bat service install
windows\efis.bat service start

# 3. Check virtual drive
windows\efis.bat drive status

# 4. Mount drive if needed
windows\efis.bat drive mount
```

### Troubleshooting
```bash
# Run diagnostics
./macos/efis diagnostics

# Check recent logs
./macos/efis logs --lines 100

# Check configuration
./macos/efis config show

# Windows troubleshooting
windows\efis.bat diagnostics
windows\efis.bat service status
windows\efis.bat drive status
```

## Output Formats

### JSON Output
Many commands support `--json` flag for machine-readable output:

```bash
./macos/efis status --json
windows\efis.bat drive status --json
```

### Log Filtering
Filter logs by component or search terms:

```bash
# Filter by component
./macos/efis logs --component grt
./macos/efis logs --component usb

# View more lines
./macos/efis logs --lines 200
```

## Error Handling

The CLI tools provide detailed error messages and return appropriate exit codes:

- `0`: Success
- `1`: General error or failure

Use verbose mode (`-v`) for additional debugging information:

```bash
./macos/efis -v status
windows\efis.bat -v diagnostics
```

## Configuration Files

The CLI tools automatically locate configuration files in these locations:

### macOS
- `config/macos-config.yaml`
- `~/.efis/config.yaml`

### Windows
- `config/windows-config.json`
- `C:/Scripts/efis-config.json`
- `~/.efis/windows-config.json`

Use `--config` to specify a custom configuration file path.

## Integration with System Services

### macOS Daemon Integration
The CLI can interact with the macOS daemon:

```bash
# Check if daemon is running
./macos/efis status

# View daemon logs
./macos/efis logs --component daemon
```

### Windows Service Integration
The CLI can manage the Windows service:

```cmd
# Full service lifecycle
windows\efis.bat service install
windows\efis.bat service start
windows\efis.bat service status
windows\efis.bat service stop
windows\efis.bat service uninstall
```

## Notifications

The CLI tools integrate with the notification system and will display notifications for:

- Successful operations
- Errors and warnings
- System status changes
- Update availability

Notification preferences can be configured through the configuration files.