# EFIS Data Manager Configuration Guide

This document provides comprehensive information about configuring the EFIS Data Manager system.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Configuration Files](#configuration-files)
- [Windows Configuration](#windows-configuration)
- [macOS Configuration](#macos-configuration)
- [Shared Configuration](#shared-configuration)
- [Environment-Specific Configuration](#environment-specific-configuration)
- [Configuration Validation](#configuration-validation)
- [Configuration Examples](#configuration-examples)
- [Troubleshooting](#troubleshooting)

## Configuration Overview

The EFIS Data Manager uses YAML configuration files to manage system settings across Windows and macOS platforms. The configuration system supports:

- Platform-specific settings
- Environment-specific overrides
- Configuration validation
- Runtime configuration updates
- Secure credential storage

## Configuration Files

### Primary Configuration Files

| File | Purpose | Platform |
|------|---------|----------|
| `config/efis_config.yaml` | Main system configuration | Both |
| `config/efis_config.development.yaml` | Development environment | Both |
| `config/efis_config.staging.yaml` | Staging environment | Both |
| `windows/config/windows-config.json` | Windows-specific settings | Windows |
| `macos/config/macos-config.yaml` | macOS-specific settings | macOS |

### Configuration Loading Order

1. Main configuration file (`efis_config.yaml`)
2. Environment-specific file (if specified)
3. Platform-specific file
4. Local override file (ignored by git)

## Windows Configuration

### Virtual Drive Settings

```yaml
windows:
  # Virtual USB drive configuration
  virtualDriveFile: "C:/Users/fligh/OneDrive/Desktop/virtualEFISUSB.vhd"
  mountTool: "C:/Program Files/ImDisk/MountImg.exe"
  driveLetter: "E:"
  
  # Mount monitoring
  checkInterval: 300  # Check every 5 minutes
  retryDelay: 60      # Retry after 1 minute on failure
  maxRetries: 3       # Maximum retry attempts
  
  # PowerShell integration
  scriptPath: "C:/Scripts/MountEFIS.ps1"
  logFile: "C:/Scripts/MountEFIS.log"
```

### Network Synchronization

```yaml
windows:
  # Network settings
  macbookIP: "192.168.1.100"
  syncPort: 22
  syncUser: "mwalker"
  syncPath: "/Users/mwalker/EFIS-Sync"
  
  # Synchronization timing
  syncInterval: 1800    # Sync every 30 minutes
  syncTimeout: 300      # 5 minute timeout
  retryAttempts: 3      # Retry failed syncs
  retryDelay: 600       # 10 minute retry delay
  
  # File transfer settings
  compressionLevel: 6   # gzip compression level
  preservePermissions: true
  deleteExtraFiles: false
  excludePatterns:
    - "*.tmp"
    - "*.log"
    - ".DS_Store"
```

### Windows Service Configuration

```yaml
windows:
  service:
    name: "EFISDataManager"
    displayName: "EFIS Data Manager Service"
    description: "Manages EFIS chart data synchronization"
    startType: "automatic"
    
    # Service behavior
    restartOnFailure: true
    restartDelay: 30000  # 30 seconds
    maxRestarts: 3
    
    # Logging
    logLevel: "INFO"
    logFile: "logs/windows-service.log"
```

## macOS Configuration

### File Paths

```yaml
macos:
  # Archive and storage paths
  archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
  demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
  logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
  tempPath: "/tmp/efis-processing"
  
  # Backup settings
  backupEnabled: true
  backupPath: "/Users/mwalker/EFIS-Backups"
  backupRetention: 30  # days
```

### GRT Website Configuration

```yaml
macos:
  grtUrls:
    # Base URLs for GRT software downloads
    baseUrl: "https://grtavionics.com"
    navDatabase: "https://grtavionics.com/downloads/nav-database"
    hxrSoftware: "https://grtavionics.com/downloads/hxr-software"
    miniAPSoftware: "https://grtavionics.com/downloads/mini-ap"
    ahrsSoftware: "https://grtavionics.com/downloads/ahrs"
    servoSoftware: "https://grtavionics.com/downloads/servo"
  
  # Web scraping settings
  webScraping:
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    timeout: 30
    retries: 3
    retryDelay: 5
    rateLimit: 2  # seconds between requests
    
    # Caching
    cacheEnabled: true
    cacheTimeout: 3600  # 1 hour
```

### USB Drive Processing

```yaml
macos:
  usbProcessing:
    # Drive detection
    monitorInterval: 5    # Check every 5 seconds
    identificationMarkers:
      - "EFIS_DRIVE.txt"
      - "GRT_DATA"
    
    # File processing
    processTimeout: 300   # 5 minutes
    verifyIntegrity: true
    createBackups: true
    
    # File patterns
    demoFilePattern: "DEMO-\\d{8}-\\d{6}(\\+\\d+)?\\.LOG"
    snapFilePattern: ".*\\.png"
    logbookFilePattern: ".*\\.csv"
```

### macOS Daemon Configuration

```yaml
macos:
  daemon:
    # Daemon settings
    name: "com.efis-data-manager.daemon"
    runAsUser: "mwalker"
    workingDirectory: "/Users/mwalker/efis-data-manager"
    
    # Scheduling
    checkInterval: 3600   # Check every hour
    navCheckTime: "01:00" # Daily NAV check at 1 AM
    grtCheckTime: "01:30" # Daily GRT check at 1:30 AM
    
    # Process management
    maxMemoryUsage: 512   # MB
    maxCPUUsage: 50       # Percent
    restartOnCrash: true
```

## Shared Configuration

### Logging Configuration

```yaml
logging:
  # Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  logLevel: "INFO"
  
  # File logging
  logToFile: true
  logFile: "logs/efis-data-manager.log"
  maxFileSize: 10485760  # 10MB
  backupCount: 5
  
  # Console logging
  logToConsole: true
  coloredOutput: true
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  dateFormat: "%Y-%m-%d %H:%M:%S"
  
  # Component-specific logging
  components:
    grt_scraper: "DEBUG"
    usb_processor: "INFO"
    sync_engine: "INFO"
    network_manager: "WARNING"
```

### Notification Configuration

```yaml
notifications:
  # Desktop notifications
  enableDesktop: true
  desktopTimeout: 5000  # 5 seconds
  
  # Email notifications
  enableEmail: false
  emailSettings:
    smtpServer: "smtp.gmail.com"
    smtpPort: 587
    useTLS: true
    username: ""  # Set via environment variable
    password: ""  # Set via environment variable or keychain
    
    # Recipients
    recipients:
      - "pilot@example.com"
    
    # Email templates
    templates:
      error: "EFIS Error: {title}"
      update: "EFIS Update: {title}"
      sync: "EFIS Sync: {title}"
  
  # Notification filtering
  filters:
    minLevel: "INFO"
    excludeComponents: []
    includeComponents: []
```

### Security Configuration

```yaml
security:
  # Credential storage
  useKeychain: true  # macOS Keychain / Windows Credential Manager
  encryptConfig: false
  
  # File permissions
  restrictFileAccess: true
  filePermissions: "600"  # Owner read/write only
  
  # Network security
  sshKeyPath: "~/.ssh/efis_rsa"
  knownHostsFile: "~/.ssh/known_hosts"
  verifySSLCerts: true
```

## Environment-Specific Configuration

### Development Environment

```yaml
# config/efis_config.development.yaml
environment: "development"

logging:
  logLevel: "DEBUG"
  logToConsole: true
  coloredOutput: true

windows:
  syncInterval: 300  # More frequent syncing for testing
  
macos:
  checkInterval: 600  # More frequent checking for testing
  
notifications:
  enableDesktop: true
  enableEmail: false
```

### Staging Environment

```yaml
# config/efis_config.staging.yaml
environment: "staging"

logging:
  logLevel: "INFO"
  
windows:
  macbookIP: "192.168.1.101"  # Staging macOS system
  
macos:
  archivePath: "/Users/mwalker/EFIS-Staging"
  
notifications:
  enableEmail: true
  emailSettings:
    recipients:
      - "staging-alerts@example.com"
```

### Production Environment

```yaml
# config/efis_config.yaml (production)
environment: "production"

logging:
  logLevel: "INFO"
  logToConsole: false
  
security:
  encryptConfig: true
  restrictFileAccess: true
  
notifications:
  enableDesktop: true
  enableEmail: true
```

## Configuration Validation

### Required Configuration Keys

The system validates the presence of these required keys:

#### Windows Required Keys
- `windows.virtualDriveFile`
- `windows.mountTool`
- `windows.driveLetter`
- `windows.macbookIP`

#### macOS Required Keys
- `macos.archivePath`
- `macos.demoPath`
- `macos.logbookPath`
- `macos.grtUrls.navDatabase`

### Validation Rules

```python
# Example validation configuration
validation:
  rules:
    windows.syncInterval:
      type: "integer"
      minimum: 60
      maximum: 86400
    
    macos.archivePath:
      type: "string"
      pattern: "^/.*"  # Must be absolute path
      exists: true     # Path must exist
    
    logging.logLevel:
      type: "string"
      enum: ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
```

### Custom Validation

```python
from shared.config.validation import ConfigValidator

validator = ConfigValidator()
validator.add_rule('windows.driveLetter', 
                  lambda x: x.endswith(':') and len(x) == 2)
validator.add_rule('macos.grtUrls.baseUrl', 
                  lambda x: x.startswith('https://'))

errors = validator.validate(config)
```

## Configuration Examples

### Minimal Configuration

```yaml
# Minimal working configuration
windows:
  virtualDriveFile: "C:/EFIS/virtualEFISUSB.vhd"
  mountTool: "C:/Program Files/ImDisk/MountImg.exe"
  driveLetter: "E:"
  macbookIP: "192.168.1.100"

macos:
  archivePath: "/Users/pilot/EFIS-USB"
  demoPath: "/Users/pilot/EFIS-DEMO"
  logbookPath: "/Users/pilot/Logbooks"
  grtUrls:
    navDatabase: "https://grtavionics.com/downloads/nav-database"

logging:
  logLevel: "INFO"
```

### Complete Configuration

```yaml
# Complete configuration with all options
environment: "production"

windows:
  # Virtual drive settings
  virtualDriveFile: "C:/Users/fligh/OneDrive/Desktop/virtualEFISUSB.vhd"
  mountTool: "C:/Program Files/ImDisk/MountImg.exe"
  driveLetter: "E:"
  scriptPath: "C:/Scripts/MountEFIS.ps1"
  logFile: "C:/Scripts/MountEFIS.log"
  
  # Network and sync settings
  macbookIP: "192.168.1.100"
  syncPort: 22
  syncUser: "mwalker"
  syncPath: "/Users/mwalker/EFIS-Sync"
  syncInterval: 1800
  syncTimeout: 300
  retryAttempts: 3
  retryDelay: 600
  
  # Monitoring
  checkInterval: 300
  retryDelay: 60
  maxRetries: 3
  
  # Service configuration
  service:
    name: "EFISDataManager"
    displayName: "EFIS Data Manager Service"
    startType: "automatic"
    restartOnFailure: true

macos:
  # File paths
  archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
  demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
  logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
  tempPath: "/tmp/efis-processing"
  backupPath: "/Users/mwalker/EFIS-Backups"
  
  # GRT URLs
  grtUrls:
    baseUrl: "https://grtavionics.com"
    navDatabase: "https://grtavionics.com/downloads/nav-database"
    hxrSoftware: "https://grtavionics.com/downloads/hxr-software"
    miniAPSoftware: "https://grtavionics.com/downloads/mini-ap"
    ahrsSoftware: "https://grtavionics.com/downloads/ahrs"
    servoSoftware: "https://grtavionics.com/downloads/servo"
  
  # Processing settings
  checkInterval: 3600
  navCheckTime: "01:00"
  grtCheckTime: "01:30"
  
  # USB processing
  usbProcessing:
    monitorInterval: 5
    processTimeout: 300
    verifyIntegrity: true
    createBackups: true

# Shared settings
logging:
  logLevel: "INFO"
  logToFile: true
  logToConsole: false
  maxFileSize: 10485760
  backupCount: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

notifications:
  enableDesktop: true
  enableEmail: true
  emailSettings:
    smtpServer: "smtp.gmail.com"
    smtpPort: 587
    useTLS: true
    recipients:
      - "pilot@example.com"

security:
  useKeychain: true
  restrictFileAccess: true
  verifySSLCerts: true
```

## Troubleshooting

### Common Configuration Issues

#### 1. Invalid YAML Syntax

**Error**: `yaml.scanner.ScannerError: while parsing a block mapping`

**Solution**: Check YAML indentation and syntax:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/efis_config.yaml'))"
```

#### 2. Missing Required Keys

**Error**: `ConfigurationError: Missing required key: windows.virtualDriveFile`

**Solution**: Add all required configuration keys:
```yaml
windows:
  virtualDriveFile: "C:/path/to/file.vhd"  # Add missing key
```

#### 3. Invalid File Paths

**Error**: `FileNotFoundError: Virtual drive file not found`

**Solution**: Verify file paths exist and are accessible:
```yaml
windows:
  virtualDriveFile: "C:/Users/fligh/OneDrive/Desktop/virtualEFISUSB.vhd"  # Correct path
```

#### 4. Network Configuration Issues

**Error**: `NetworkError: Cannot connect to macOS system`

**Solution**: Verify network settings and connectivity:
```yaml
windows:
  macbookIP: "192.168.1.100"  # Correct IP address
  syncPort: 22                # Correct SSH port
```

### Configuration Validation Commands

```bash
# Validate configuration
python -m shared.config.validation config/efis_config.yaml

# Test configuration loading
python -c "
from shared.config.config_manager import ConfigManager
config = ConfigManager()
config.load_config('config/efis_config.yaml')
print('Configuration loaded successfully')
"

# Check specific configuration values
python -c "
from shared.config.config_manager import ConfigManager
config = ConfigManager()
config.load_config('config/efis_config.yaml')
print(f'Windows drive: {config.get(\"windows.driveLetter\")}')
print(f'macOS archive: {config.get(\"macos.archivePath\")}')
"
```

### Environment Variable Overrides

Set sensitive values via environment variables:

```bash
# Set email credentials
export EFIS_EMAIL_USERNAME="your-email@gmail.com"
export EFIS_EMAIL_PASSWORD="your-app-password"

# Set SSH key path
export EFIS_SSH_KEY_PATH="/Users/pilot/.ssh/efis_rsa"

# Override configuration values
export EFIS_WINDOWS_MACBOOK_IP="192.168.1.101"
export EFIS_MACOS_ARCHIVE_PATH="/Users/pilot/Custom-Archive"
```

### Configuration File Locations

The system searches for configuration files in this order:

1. Command-line specified path
2. Current directory: `./config/efis_config.yaml`
3. User home directory: `~/.efis/config.yaml`
4. System directory: `/etc/efis/config.yaml` (macOS) or `C:/ProgramData/EFIS/config.yaml` (Windows)

### Debugging Configuration Issues

Enable debug logging to troubleshoot configuration problems:

```yaml
logging:
  logLevel: "DEBUG"
  components:
    config_manager: "DEBUG"
```

This will provide detailed information about configuration loading, validation, and value resolution.