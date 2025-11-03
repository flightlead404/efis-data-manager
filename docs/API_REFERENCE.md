# EFIS Data Manager API Reference

This document provides comprehensive API documentation for all modules in the EFIS Data Manager system.

## Table of Contents

- [Windows Components](#windows-components)
- [macOS Components](#macos-components)
- [Shared Components](#shared-components)
- [Configuration API](#configuration-api)
- [Error Handling](#error-handling)
- [Data Models](#data-models)

## Windows Components

### ImDiskWrapper

Wrapper class for ImDisk virtual drive operations.

```python
from windows.src.imdisk_wrapper import ImDiskWrapper

class ImDiskWrapper:
    """Wrapper for ImDisk MountImg.exe operations."""
    
    def __init__(self, mount_tool_path: str, log_file: str):
        """
        Initialize ImDisk wrapper.
        
        Args:
            mount_tool_path: Path to MountImg.exe
            log_file: Path to log file for operations
        """
    
    def mount_vhd(self, vhd_path: str, drive_letter: str) -> bool:
        """
        Mount VHD file to specified drive letter.
        
        Args:
            vhd_path: Path to VHD file
            drive_letter: Target drive letter (e.g., 'E:')
            
        Returns:
            bool: True if mount successful, False otherwise
            
        Raises:
            FileNotFoundError: If VHD file doesn't exist
            PermissionError: If insufficient privileges
        """
    
    def unmount_drive(self, drive_letter: str) -> bool:
        """
        Unmount drive by drive letter.
        
        Args:
            drive_letter: Drive letter to unmount (e.g., 'E:')
            
        Returns:
            bool: True if unmount successful, False otherwise
        """
    
    def is_drive_mounted(self, drive_letter: str) -> bool:
        """
        Check if drive is currently mounted.
        
        Args:
            drive_letter: Drive letter to check (e.g., 'E:')
            
        Returns:
            bool: True if drive is mounted, False otherwise
        """
    
    def get_drive_info(self, drive_letter: str) -> Dict[str, Any]:
        """
        Get information about mounted drive.
        
        Args:
            drive_letter: Drive letter to query
            
        Returns:
            Dict containing drive information:
            - size: Drive size in bytes
            - free_space: Available space in bytes
            - file_system: File system type
            - mount_point: Mount point path
        """
```

### SyncEngine

File synchronization engine for Windows-to-macOS transfers.

```python
from windows.src.sync_engine import SyncEngine

class SyncEngine:
    """Handles file synchronization between Windows and macOS systems."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize sync engine.
        
        Args:
            config: Configuration dictionary with sync settings
        """
    
    def sync_files(self, source_path: str, target_host: str, 
                   target_path: str) -> SyncResult:
        """
        Synchronize files from source to target.
        
        Args:
            source_path: Local source directory path
            target_host: Target host IP or hostname
            target_path: Remote target directory path
            
        Returns:
            SyncResult: Object containing sync operation results
            
        Raises:
            NetworkError: If connection to target fails
            FileSystemError: If file operations fail
        """
    
    def get_changed_files(self, path: str, since: datetime) -> List[FileMetadata]:
        """
        Get list of files changed since specified time.
        
        Args:
            path: Directory path to scan
            since: Timestamp to compare against
            
        Returns:
            List of FileMetadata objects for changed files
        """
    
    def calculate_sync_size(self, source_path: str, 
                           target_host: str) -> int:
        """
        Calculate total size of files to be synchronized.
        
        Args:
            source_path: Local source directory
            target_host: Target host for comparison
            
        Returns:
            int: Total bytes to be transferred
        """
```

### WindowsService

Main Windows service implementation.

```python
from windows.src.windows_service import WindowsService

class WindowsService:
    """Main Windows service for EFIS Data Manager."""
    
    def __init__(self, config_path: str):
        """
        Initialize Windows service.
        
        Args:
            config_path: Path to configuration file
        """
    
    def start_service(self) -> None:
        """Start the Windows service."""
    
    def stop_service(self) -> None:
        """Stop the Windows service."""
    
    def run_sync_cycle(self) -> None:
        """Execute one synchronization cycle."""
    
    def check_virtual_drive(self) -> bool:
        """
        Check virtual drive status and remount if necessary.
        
        Returns:
            bool: True if drive is available, False otherwise
        """
```

## macOS Components

### GRTScraper

Web scraper for GRT Avionics software updates.

```python
from macos.src.efis_macos.grt_scraper import GRTScraper

class GRTScraper:
    """Web scraper for GRT Avionics software updates."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GRT scraper.
        
        Args:
            config: Configuration dictionary with GRT URLs and settings
        """
    
    def check_nav_database_update(self) -> Optional[GRTSoftwareInfo]:
        """
        Check for NAV database updates.
        
        Returns:
            GRTSoftwareInfo object if update available, None otherwise
        """
    
    def check_software_updates(self) -> List[GRTSoftwareInfo]:
        """
        Check for all GRT software updates.
        
        Returns:
            List of GRTSoftwareInfo objects for available updates
        """
    
    def download_file(self, url: str, local_path: str) -> bool:
        """
        Download file from GRT website.
        
        Args:
            url: Download URL
            local_path: Local file path for download
            
        Returns:
            bool: True if download successful, False otherwise
            
        Raises:
            NetworkError: If download fails
            FileSystemError: If local file operations fail
        """
    
    def parse_version_info(self, html_content: str, 
                          software_type: str) -> Optional[str]:
        """
        Parse version information from HTML content.
        
        Args:
            html_content: HTML content to parse
            software_type: Type of software (hxr, mini_ap, ahrs, servo)
            
        Returns:
            Version string if found, None otherwise
        """
```

### USBDriveProcessor

USB drive detection and processing for EFIS drives.

```python
from macos.src.efis_macos.usb_drive_processor import USBDriveProcessor

class USBDriveProcessor:
    """Handles EFIS USB drive detection and processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize USB drive processor.
        
        Args:
            config: Configuration dictionary with paths and settings
        """
    
    def detect_efis_drive(self, mount_path: str) -> bool:
        """
        Detect if USB drive is an EFIS drive.
        
        Args:
            mount_path: Path where USB drive is mounted
            
        Returns:
            bool: True if EFIS drive detected, False otherwise
        """
    
    def process_efis_files(self, drive_path: str) -> ProcessResult:
        """
        Process files on EFIS USB drive.
        
        Args:
            drive_path: Path to EFIS USB drive
            
        Returns:
            ProcessResult: Object containing processing results
        """
    
    def update_drive_contents(self, drive_path: str) -> UpdateResult:
        """
        Update USB drive with latest chart data and software.
        
        Args:
            drive_path: Path to EFIS USB drive
            
        Returns:
            UpdateResult: Object containing update results
        """
    
    def get_demo_files(self, drive_path: str) -> List[str]:
        """
        Get list of demo files on USB drive.
        
        Args:
            drive_path: Path to USB drive
            
        Returns:
            List of demo file paths
        """
    
    def get_snap_files(self, drive_path: str) -> List[str]:
        """
        Get list of snapshot files on USB drive.
        
        Args:
            drive_path: Path to USB drive
            
        Returns:
            List of snapshot file paths
        """
```

### EFISFileProcessor

File processing engine for EFIS data files.

```python
from macos.src.efis_macos.efis_file_processor import EFISFileProcessor

class EFISFileProcessor:
    """Processes EFIS data files (demo, snap, logbook)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize file processor.
        
        Args:
            config: Configuration dictionary with target paths
        """
    
    def process_demo_files(self, files: List[str], 
                          target_dir: str) -> ProcessResult:
        """
        Process demo files from USB drive.
        
        Args:
            files: List of demo file paths
            target_dir: Target directory for processed files
            
        Returns:
            ProcessResult: Processing operation results
        """
    
    def process_snap_files(self, files: List[str], 
                          target_dir: str) -> ProcessResult:
        """
        Process snapshot files from USB drive.
        
        Args:
            files: List of snapshot file paths
            target_dir: Target directory for processed files
            
        Returns:
            ProcessResult: Processing operation results
        """
    
    def process_logbook_files(self, files: List[str], 
                             target_dir: str) -> ProcessResult:
        """
        Process logbook CSV files from USB drive.
        
        Args:
            files: List of logbook file paths
            target_dir: Target directory for processed files
            
        Returns:
            ProcessResult: Processing operation results
        """
    
    def rename_logbook_file(self, file_path: str) -> str:
        """
        Rename logbook file with date-based format.
        
        Args:
            file_path: Original logbook file path
            
        Returns:
            New file path with date-based name
        """
```

## Shared Components

### ConfigManager

Configuration management system.

```python
from shared.config.config_manager import ConfigManager

class ConfigManager:
    """Manages system configuration across platforms."""
    
    def __init__(self):
        """Initialize configuration manager."""
    
    def load_config(self, config_path: str) -> None:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config validation fails
        """
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'windows.driveLetter')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key
            value: Value to set
        """
    
    def save_config(self, config_path: str = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Optional path to save to (uses loaded path if None)
        """
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration completeness.
        
        Returns:
            List of validation error messages (empty if valid)
        """
```

### NotificationManager

Cross-platform notification system.

```python
from shared.notifications.notification_manager import NotificationManager

class NotificationManager:
    """Manages cross-platform notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notification manager.
        
        Args:
            config: Configuration dictionary with notification settings
        """
    
    def send_notification(self, title: str, message: str, 
                         notification_type: NotificationType = NotificationType.INFO) -> bool:
        """
        Send notification to user.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (INFO, WARNING, ERROR)
            
        Returns:
            bool: True if notification sent successfully
        """
    
    def send_email_notification(self, subject: str, body: str, 
                               recipients: List[str]) -> bool:
        """
        Send email notification.
        
        Args:
            subject: Email subject
            body: Email body
            recipients: List of recipient email addresses
            
        Returns:
            bool: True if email sent successfully
        """
```

## Configuration API

### Configuration Structure

The system uses YAML configuration files with the following structure:

```yaml
windows:
  virtualDriveFile: "C:/Users/fligh/OneDrive/Desktop/virtualEFISUSB.vhd"
  mountTool: "C:/Program Files/ImDisk/MountImg.exe"
  driveLetter: "E:"
  syncInterval: 1800  # seconds
  macbookIP: "192.168.1.100"
  retryAttempts: 3

macos:
  archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
  demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
  logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
  checkInterval: 3600  # seconds
  grtUrls:
    navDatabase: "https://grtavionics.com/downloads/nav-database"
    hxrSoftware: "https://grtavionics.com/downloads/hxr-software"
    miniAPSoftware: "https://grtavionics.com/downloads/mini-ap"
    ahrsSoftware: "https://grtavionics.com/downloads/ahrs"
    servoSoftware: "https://grtavionics.com/downloads/servo"

logging:
  logLevel: "INFO"
  maxFileSize: 10485760  # 10MB
  backupCount: 5
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

notifications:
  enableDesktop: true
  enableEmail: false
  emailSettings:
    smtpServer: "smtp.gmail.com"
    smtpPort: 587
    username: ""
    password: ""
    recipients: []
```

### Configuration Validation

Required configuration keys:
- `windows.virtualDriveFile`
- `windows.mountTool`
- `windows.driveLetter`
- `macos.archivePath`
- `macos.demoPath`
- `macos.logbookPath`

## Error Handling

### Exception Hierarchy

```python
class EFISError(Exception):
    """Base exception for EFIS Data Manager."""
    pass

class NetworkError(EFISError):
    """Network-related errors."""
    pass

class FileSystemError(EFISError):
    """File system operation errors."""
    pass

class ConfigurationError(EFISError):
    """Configuration-related errors."""
    pass

class ValidationError(EFISError):
    """Data validation errors."""
    pass

class MountError(EFISError):
    """Virtual drive mount/unmount errors."""
    pass
```

### Error Handling Patterns

```python
from shared.error_handling.file_system_errors import handle_file_operation

@handle_file_operation(retries=3, backoff=1.0)
def copy_file(source: str, destination: str) -> bool:
    """Copy file with automatic retry on failure."""
    # Implementation with error handling
    pass
```

## Data Models

### Core Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

@dataclass
class FileMetadata:
    """Metadata for tracked files."""
    path: str
    size: int
    hash: str
    last_modified: datetime
    version: Optional[str] = None

@dataclass
class SyncResult:
    """Results of synchronization operation."""
    files_transferred: int
    bytes_transferred: int
    errors: List[str]
    duration: float
    status: OperationStatus

@dataclass
class ProcessResult:
    """Results of file processing operation."""
    files_processed: int
    files_moved: int
    errors: List[str]
    status: OperationStatus

@dataclass
class GRTSoftwareInfo:
    """Information about GRT software."""
    software_type: str
    version: str
    download_url: str
    file_size: int
    release_date: Optional[datetime] = None

class OperationStatus(Enum):
    """Status of operations."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    CANCELLED = "cancelled"

class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
```

## Usage Examples

### Windows Service Usage

```python
from windows.src.windows_service import WindowsService
from shared.config.config_manager import ConfigManager

# Initialize service
config = ConfigManager()
config.load_config('config/efis_config.yaml')
service = WindowsService('config/efis_config.yaml')

# Start service
service.start_service()

# Manual sync
service.run_sync_cycle()
```

### macOS Daemon Usage

```python
from macos.src.efis_macos.daemon import EFISDaemon
from shared.config.config_manager import ConfigManager

# Initialize daemon
config = ConfigManager()
config.load_config('config/efis_config.yaml')
daemon = EFISDaemon(config)

# Start daemon
daemon.start()

# Process USB drive
result = daemon.process_usb_drive('/Volumes/EFIS_USB')
```

### Configuration Management

```python
from shared.config.config_manager import ConfigManager

# Load and modify configuration
config = ConfigManager()
config.load_config('config/efis_config.yaml')

# Get values
drive_letter = config.get('windows.driveLetter')
archive_path = config.get('macos.archivePath')

# Set values
config.set('windows.syncInterval', 3600)
config.save_config()
```

This API reference provides comprehensive documentation for all major components and interfaces in the EFIS Data Manager system. For implementation details and examples, refer to the source code and additional documentation files.