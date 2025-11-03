# EFIS Data Manager Development Guide

## Project Structure

The EFIS Data Manager is organized as a cross-platform system with separate components for Windows and macOS, plus shared utilities.

```
efis-data-manager/
├── README.md                   # Project overview and quick start
├── .gitignore                  # Git ignore patterns
├── setup_dev_windows.bat       # Windows development setup
├── setup_dev_macos.sh         # macOS development setup
├── config/                     # Global configuration templates
│   └── efis_config.yaml       # Main configuration file
├── shared/                     # Shared utilities and models
│   ├── config/                # Configuration management
│   ├── models/                # Data models
│   └── utils/                 # Utility functions
├── windows/                    # Windows service component
│   ├── src/                   # Python source code
│   ├── config/                # Windows-specific config
│   ├── logs/                  # Log files
│   ├── requirements.txt       # Dependencies
│   └── setup.py              # Installation script
├── macos/                     # macOS daemon component
│   ├── src/                   # Python source code
│   ├── config/                # macOS-specific config
│   ├── logs/                  # Log files
│   ├── requirements.txt       # Dependencies
│   └── setup.py              # Installation script
├── docs/                      # Documentation
└── tests/                     # Test files
```

## Development Environment Setup

### Prerequisites

- **Windows**: Python 3.8+ with pip
- **macOS**: Python 3.8+ with pip
- Git for version control

### Windows Setup

1. Run the setup script:
   ```cmd
   setup_dev_windows.bat
   ```

2. Or manually:
   ```cmd
   cd windows
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   pip install -e .
   ```

### macOS Setup

1. Run the setup script:
   ```bash
   ./setup_dev_macos.sh
   ```

2. Or manually:
   ```bash
   cd macos
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

## Configuration

### Main Configuration File

The system uses `config/efis_config.yaml` for configuration. Key sections:

- **windows**: Virtual drive settings, sync intervals, network configuration
- **macos**: File paths, GRT URLs, daemon settings
- **logging**: Log levels, rotation settings
- **notifications**: Alert preferences
- **transfer**: File transfer settings

### Environment-Specific Configuration

Create local configuration files for development:

- `config/efis_config_local.yaml` - Local overrides (ignored by git)
- `windows/config/local.yaml` - Windows-specific local config
- `macos/config/local.yaml` - macOS-specific local config

## Logging

### Log Configuration

The system uses structured logging with:
- Automatic log rotation (10MB files, 5 backups)
- Colored console output for development
- JSON-structured logs for production
- Component-specific log files

### Log Locations

- Windows: `windows/logs/windows.log`
- macOS: `macos/logs/macos.log`
- Shared utilities: Use component-specific loggers

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

## Data Models

### Core Models

Located in `shared/models/data_models.py`:

- **FileMetadata**: File tracking information
- **SyncResult**: Synchronization operation results
- **EFISDrive**: USB drive representation
- **VirtualDrive**: Windows virtual drive representation
- **GRTSoftwareInfo**: GRT software version information
- **SystemConfig**: Configuration data structure

### Status Enums

- **OperationStatus**: SUCCESS, FAILED, IN_PROGRESS, PENDING, CANCELLED
- **DriveStatus**: MOUNTED, UNMOUNTED, ERROR, UNKNOWN

## Configuration Management

### ConfigManager Class

Located in `shared/config/config_manager.py`:

```python
from shared.config.config_manager import ConfigManager

# Load configuration
config = ConfigManager()
config.load_config('config/efis_config.yaml')

# Get values with dot notation
drive_letter = config.get('windows.driveLetter', 'E:')
archive_path = config.get('macos.archivePath')

# Set values
config.set('windows.syncInterval', 1800)
config.save_config()
```

### Configuration Validation

The ConfigManager includes validation for required keys:
- `windows.virtualDriveFile`
- `windows.mountTool`
- `windows.driveLetter`
- `macos.archivePath`
- `macos.demoPath`
- `macos.logbookPath`

## Development Workflow

### 1. Environment Activation

**Windows:**
```cmd
cd windows
venv\Scripts\activate.bat
```

**macOS:**
```bash
cd macos
source venv/bin/activate
```

### 2. Running Components

**Windows Service (Development):**
```cmd
cd windows
python src/efis_windows/service.py
```

**macOS Daemon (Development):**
```bash
cd macos
python src/efis_macos/daemon.py
```

### 3. Testing Configuration

```python
# Test configuration loading
from shared.config.config_manager import ConfigManager

config = ConfigManager()
config.load_config('config/efis_config.yaml')
print(f"Windows drive: {config.get('windows.driveLetter')}")
print(f"macOS archive: {config.get('macos.archivePath')}")
```

### 4. Testing Logging

```python
# Test logging setup
from shared.utils.logging_config import setup_component_logging

config = {'logging': {'logLevel': 'DEBUG'}}
logger = setup_component_logging('test', config)
logger.info("Test message")
logger.error("Test error")
```

## Code Style and Standards

### Python Standards

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Include docstrings for all classes and functions
- Use dataclasses for data structures
- Handle exceptions appropriately with logging

### File Organization

- Keep platform-specific code in respective directories
- Use shared utilities for common functionality
- Separate configuration, logging, and business logic
- Include comprehensive error handling

### Documentation

- Update README.md for user-facing changes
- Document configuration options in YAML comments
- Include docstrings with parameter and return type information
- Update this development guide for structural changes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and packages installed
2. **Configuration Errors**: Check YAML syntax and required keys
3. **Permission Errors**: Run with appropriate privileges for file system access
4. **Network Errors**: Verify network connectivity and firewall settings

### Debug Mode

Enable debug logging by setting `logLevel: DEBUG` in configuration:

```yaml
logging:
  logLevel: DEBUG
```

### Log Analysis

Check component-specific log files for detailed operation information:
- Windows: `windows/logs/windows.log`
- macOS: `macos/logs/macos.log`

## Next Steps

After completing the project structure setup:

1. Implement Windows virtual drive management (Task 2)
2. Create network synchronization system (Task 3)
3. Develop macOS daemon for GRT management (Task 4)
4. Build USB drive detection and processing (Task 5)
5. Add notification and user interface systems (Task 6)