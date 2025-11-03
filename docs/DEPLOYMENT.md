# EFIS Data Manager - Deployment Guide

This guide covers the installation and deployment of EFIS Data Manager on both Windows and macOS platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Windows Installation](#windows-installation)
- [macOS Installation](#macos-installation)
- [Configuration](#configuration)
- [Service Management](#service-management)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Prerequisites

### Common Requirements
- Python 3.8 or higher
- Internet connection for downloading dependencies
- Administrative/sudo privileges for system installation

### Windows Requirements
- Windows 10 or higher
- PowerShell 5.0 or higher
- ImDisk Virtual Disk Driver (will be installed automatically)

### macOS Requirements
- macOS 10.15 (Catalina) or higher
- Homebrew (recommended for dependencies)
- Xcode Command Line Tools

## Quick Start

### Automated Installation

1. **Download the project:**
   ```bash
   git clone <repository-url>
   cd efis-data-manager
   ```

2. **Run the cross-platform installer:**
   ```bash
   python deploy.py install
   ```

3. **Start the service:**
   - **Windows:** `sc start EFISDataManager`
   - **macOS:** `launchctl start com.efis.datamanager`

### Development Environment Setup

For development, use the environment setup script:

```bash
python setup_environment.py --dev
source venv/bin/activate  # macOS/Linux
# or
venv\\Scripts\\activate   # Windows
```

## Windows Installation

### Method 1: Using the Deployment Script

```bash
# Check requirements
python deploy.py check

# Install with default settings
python deploy.py install

# Install with custom configuration
python deploy.py install --config my_config.yaml --install-dir "C:\\MyEFIS"
```

### Method 2: Direct Installation

```bash
cd windows
python install.py
```

### Method 3: Using Installation Package

1. Create deployment package:
   ```bash
   python deploy.py package --output dist/
   ```

2. Copy the `dist/windows/efis-data-manager-windows` folder to target machine

3. Run as administrator:
   ```cmd
   install.bat
   ```

### Windows Service Configuration

The installer creates a Windows service with the following properties:
- **Service Name:** EFISDataManager
- **Display Name:** EFIS Data Manager Service
- **Start Type:** Automatic
- **Recovery:** Restart on failure

#### Service Management Commands

```cmd
# Start service
sc start EFISDataManager

# Stop service
sc stop EFISDataManager

# Check service status
sc query EFISDataManager

# View service configuration
sc qc EFISDataManager
```

### Scheduled Task

The installer also creates a scheduled task "MountEFIS" that:
- Runs at system startup (1-minute delay)
- Runs every hour as backup
- Ensures virtual USB drive stays mounted
- Logs to `C:\\Scripts\\MountEFIS.log`

## macOS Installation

### Method 1: Using the Deployment Script

```bash
# Check requirements
python deploy.py check

# User installation (recommended)
python deploy.py install

# System-wide installation (requires sudo)
sudo python deploy.py install --system-wide

# Custom user installation
python deploy.py install --user myuser --install-dir /opt/efis
```

### Method 2: Direct Installation

```bash
cd macos

# User installation
python install.py

# System-wide installation
sudo python install.py --system-wide

# Custom installation
python install.py --user myuser --install-dir /opt/efis
```

### Method 3: Using Installation Package

1. Create deployment package:
   ```bash
   python deploy.py package --output dist/
   ```

2. Copy the `dist/macos/efis-data-manager-macos` folder to target machine

3. Run installation:
   ```bash
   ./install.sh
   # or for system-wide
   sudo ./install.sh
   ```

### launchd Configuration

The installer creates a launchd plist file:
- **User Agent:** `~/Library/LaunchAgents/com.efis.datamanager.plist`
- **System Daemon:** `/Library/LaunchDaemons/com.efis.datamanager.plist`

#### Service Management Commands

```bash
# User agent commands
launchctl load ~/Library/LaunchAgents/com.efis.datamanager.plist
launchctl start com.efis.datamanager
launchctl stop com.efis.datamanager
launchctl unload ~/Library/LaunchAgents/com.efis.datamanager.plist

# System daemon commands (requires sudo)
sudo launchctl load /Library/LaunchDaemons/com.efis.datamanager.plist
sudo launchctl start com.efis.datamanager
sudo launchctl stop com.efis.datamanager
sudo launchctl unload /Library/LaunchDaemons/com.efis.datamanager.plist
```

## Configuration

### Configuration Files

The system uses YAML configuration files with environment-specific overrides:

- **Production:** `config/efis_config.yaml`
- **Development:** `config/efis_config.development.yaml`
- **Staging:** `config/efis_config.staging.yaml`

### Configuration Management

Use the configuration CLI tool for management:

```bash
# Validate configuration
python -m shared.config.config_cli validate

# Show current configuration
python -m shared.config.config_cli show

# Set configuration value
python -m shared.config.config_cli set windows.syncInterval 1800

# Get configuration value
python -m shared.config.config_cli get macos.archivePath

# Create new configuration
python -m shared.config.config_cli create --output my_config.yaml
```

### Environment Variables

Set environment variables to override configuration:

```bash
# Set environment
export EFIS_ENV=development

# Override configuration values (JSON format)
export EFIS_CONFIG_OVERRIDES='{"windows":{"syncInterval":300}}'
```

### Secure Credentials

Store sensitive credentials securely using the system keyring:

```bash
# Store email password
python -m shared.config.config_cli credential set --key email_password --value mypassword

# Retrieve credential
python -m shared.config.config_cli credential get --key email_password

# Delete credential
python -m shared.config.config_cli credential delete --key email_password
```

## Service Management

### Windows Service Management

```cmd
# Service control
net start EFISDataManager
net stop EFISDataManager

# Service configuration
sc config EFISDataManager start= auto
sc config EFISDataManager start= disabled

# View service logs
type "C:\\Program Files\\EFIS Data Manager\\logs\\service.log"
```

### macOS Service Management

```bash
# Check service status
launchctl list | grep com.efis.datamanager

# View service logs
tail -f ~/Library/Logs/EFIS/efis_daemon.log

# Restart service
launchctl stop com.efis.datamanager
launchctl start com.efis.datamanager
```

### CLI Tools

Both platforms include CLI tools for management:

```bash
# Windows
"C:\\Program Files\\EFIS Data Manager\\efis_cli.py" --help

# macOS (if symlink created)
efis --help

# Direct execution
python macos/efis_cli.py --help
```

## Troubleshooting

### Common Issues

#### Windows

1. **Service won't start:**
   - Check if running as administrator
   - Verify ImDisk is installed
   - Check service logs in Event Viewer

2. **Virtual drive won't mount:**
   - Verify VHD file exists and is accessible
   - Check ImDisk installation
   - Review `C:\\Scripts\\MountEFIS.log`

3. **Network sync fails:**
   - Verify MacBook IP address in configuration
   - Check firewall settings
   - Test network connectivity

#### macOS

1. **Daemon won't start:**
   - Check launchd plist syntax: `plutil -lint plist_file`
   - Verify Python path and permissions
   - Check daemon logs

2. **USB drive not detected:**
   - Verify drive identifiers in configuration
   - Check USB drive format and contents
   - Review system logs: `log show --predicate 'process == "efis_daemon"'`

3. **GRT website scraping fails:**
   - Check internet connectivity
   - Verify GRT URLs in configuration
   - Review rate limiting settings

### Log Files

#### Windows
- Service logs: `C:\\Program Files\\EFIS Data Manager\\logs\\`
- Mount logs: `C:\\Scripts\\MountEFIS.log`
- Event Viewer: Windows Logs > Application

#### macOS
- Daemon logs: `~/Library/Logs/EFIS/`
- System logs: `log show --predicate 'process == "efis_daemon"'`
- Console.app: Filter by "efis"

### Debug Mode

Enable debug logging by setting log level to DEBUG in configuration:

```yaml
logging:
  level: DEBUG
```

Or use environment variable:
```bash
export EFIS_LOG_LEVEL=DEBUG
```

## Uninstallation

### Windows

```cmd
# Method 1: Use uninstaller
"C:\\Program Files\\EFIS Data Manager\\uninstall.py"

# Method 2: Manual removal
sc stop EFISDataManager
sc delete EFISDataManager
schtasks /delete /tn "MountEFIS" /f
rmdir /s "C:\\Program Files\\EFIS Data Manager"
```

### macOS

```bash
# Method 1: Use uninstaller
python /usr/local/efis-data-manager/uninstall.py

# Method 2: Manual removal
launchctl unload ~/Library/LaunchAgents/com.efis.datamanager.plist
rm ~/Library/LaunchAgents/com.efis.datamanager.plist
sudo rm -rf /usr/local/efis-data-manager
rm /usr/local/bin/efis
```

## Security Considerations

### File Permissions

- Configuration files should be readable only by the service user
- Log directories should have appropriate write permissions
- Credential storage uses system keyring for security

### Network Security

- Use SSH key authentication for file synchronization
- Configure firewall rules for required ports
- Consider VPN for remote synchronization

### Service Security

- Services run with minimal required privileges
- Regular security updates for dependencies
- Audit logs for security monitoring

## Support

For additional support:

1. Check the troubleshooting section above
2. Review log files for error messages
3. Validate configuration using the CLI tool
4. Consult the project documentation
5. Contact technical support with log files and configuration details