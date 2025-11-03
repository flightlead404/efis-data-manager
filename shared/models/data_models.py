"""
Data models for EFIS Data Manager.
Defines data structures used across Windows and macOS components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class OperationStatus(Enum):
    """Status of system operations."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    CANCELLED = "cancelled"


class DriveStatus(Enum):
    """Status of virtual or physical drives."""
    MOUNTED = "mounted"
    UNMOUNTED = "unmounted"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class FileMetadata:
    """Metadata for tracked files."""
    path: str
    size: int
    hash: str
    last_modified: datetime
    version: Optional[str] = None
    
    def __post_init__(self):
        """Convert string path to Path object if needed."""
        if isinstance(self.path, str):
            self.path = Path(self.path)


@dataclass
class SyncResult:
    """Result of file synchronization operation."""
    status: OperationStatus
    files_transferred: int = 0
    bytes_transferred: int = 0
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)
        
    def set_failed(self, error: str) -> None:
        """Mark operation as failed with error message."""
        self.status = OperationStatus.FAILED
        self.add_error(error)


@dataclass
class EFISDrive:
    """Represents an EFIS USB drive."""
    mount_path: str
    identifier: str
    capacity: int
    demo_files: List[str] = field(default_factory=list)
    snap_files: List[str] = field(default_factory=list)
    logbook_files: List[str] = field(default_factory=list)
    status: DriveStatus = DriveStatus.UNKNOWN
    
    def __post_init__(self):
        """Convert string path to Path object if needed."""
        if isinstance(self.mount_path, str):
            self.mount_path = Path(self.mount_path)


@dataclass
class VirtualDrive:
    """Represents Windows virtual USB drive."""
    vhd_file: str
    drive_letter: str
    mount_tool: str
    status: DriveStatus = DriveStatus.UNKNOWN
    last_check: Optional[datetime] = None
    
    def __post_init__(self):
        """Convert string paths to Path objects if needed."""
        if isinstance(self.vhd_file, str):
            self.vhd_file = Path(self.vhd_file)
        if isinstance(self.mount_tool, str):
            self.mount_tool = Path(self.mount_tool)


@dataclass
class GRTSoftwareInfo:
    """Information about GRT software versions."""
    software_type: str  # 'nav', 'hxr', 'mini_ap', 'ahrs', 'servo'
    version: str
    download_url: str
    file_size: Optional[int] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    
    
@dataclass
class DownloadResult:
    """Result of file download operation."""
    status: OperationStatus
    file_path: Optional[str] = None
    file_size: int = 0
    download_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)


@dataclass
class ProcessResult:
    """Result of USB drive processing operation."""
    status: OperationStatus
    files_processed: int = 0
    files_moved: int = 0
    files_copied: int = 0
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        self.errors.append(error)


@dataclass
class SystemConfig:
    """System configuration data model."""
    windows: Dict[str, Any] = field(default_factory=dict)
    macos: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    notifications: Dict[str, Any] = field(default_factory=dict)
    transfer: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SystemConfig':
        """Create SystemConfig from dictionary."""
        return cls(
            windows=config_dict.get('windows', {}),
            macos=config_dict.get('macos', {}),
            logging=config_dict.get('logging', {}),
            notifications=config_dict.get('notifications', {}),
            transfer=config_dict.get('transfer', {})
        )


@dataclass
class NetworkStatus:
    """Network connectivity status."""
    is_connected: bool
    target_host: Optional[str] = None
    response_time: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ServiceStatus:
    """Status of system services."""
    service_name: str
    is_running: bool
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    status_message: Optional[str] = None
    
    
@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str
    component: str
    operation: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'component': self.component,
            'operation': self.operation,
            'message': self.message,
            'details': self.details
        }