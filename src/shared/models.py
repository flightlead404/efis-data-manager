"""Data models and interfaces for EFIS Data Manager."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path


class SyncStatus(Enum):
    """Status of synchronization operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class DriveStatus(Enum):
    """Status of virtual or USB drive."""
    MOUNTED = "mounted"
    UNMOUNTED = "unmounted"
    ERROR = "error"
    UNKNOWN = "unknown"


class UpdateType(Enum):
    """Type of GRT software update."""
    NAV_DATABASE = "nav_database"
    HXR_SOFTWARE = "hxr_software"
    MINI_AP_SOFTWARE = "mini_ap_software"
    AHRS_SOFTWARE = "ahrs_software"
    SERVO_SOFTWARE = "servo_software"


@dataclass
class FileMetadata:
    """Metadata for tracked files."""
    path: str
    size: int
    hash: str
    last_modified: datetime
    version: Optional[str] = None
    
    def __post_init__(self):
        """Ensure path is normalized."""
        self.path = str(Path(self.path).resolve())


@dataclass
class SyncResult:
    """Result of file synchronization operation."""
    status: SyncStatus
    files_transferred: int
    bytes_transferred: int
    errors: List[str]
    duration: float
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.files_transferred == 0:
            return 0.0
        error_count = len(self.errors)
        total_operations = self.files_transferred + error_count
        return (self.files_transferred / total_operations) * 100


@dataclass
class EFISDrive:
    """Represents an EFIS USB drive."""
    mount_path: str
    identifier: str
    capacity: int
    demo_files: List[str]
    snap_files: List[str]
    logbook_files: List[str]
    status: DriveStatus = DriveStatus.UNKNOWN
    
    @property
    def total_files(self) -> int:
        """Total number of files on drive."""
        return len(self.demo_files) + len(self.snap_files) + len(self.logbook_files)
    
    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get files by type (demo, snap, logbook)."""
        if file_type.lower() == 'demo':
            return self.demo_files
        elif file_type.lower() == 'snap':
            return self.snap_files
        elif file_type.lower() == 'logbook':
            return self.logbook_files
        else:
            return []


@dataclass
class UpdateInfo:
    """Information about available software updates."""
    update_type: UpdateType
    current_version: Optional[str]
    available_version: str
    download_url: str
    file_size: Optional[int] = None
    release_date: Optional[datetime] = None
    description: Optional[str] = None
    
    @property
    def has_update(self) -> bool:
        """Check if update is available."""
        if self.current_version is None:
            return True
        return self.current_version != self.available_version


@dataclass
class DownloadResult:
    """Result of file download operation."""
    success: bool
    file_path: Optional[str]
    file_size: int
    download_time: float
    error_message: Optional[str] = None
    
    @property
    def download_speed_mbps(self) -> float:
        """Calculate download speed in MB/s."""
        if self.download_time == 0:
            return 0.0
        return (self.file_size / (1024 * 1024)) / self.download_time


@dataclass
class ProcessResult:
    """Result of USB drive processing operation."""
    success: bool
    files_processed: int
    files_moved: int
    files_copied: int
    errors: List[str]
    processing_time: float
    
    @property
    def error_count(self) -> int:
        """Number of errors encountered."""
        return len(self.errors)
    
    @property
    def success_rate(self) -> float:
        """Processing success rate as percentage."""
        if self.files_processed == 0:
            return 100.0
        return ((self.files_processed - self.error_count) / self.files_processed) * 100


@dataclass
class SystemStatus:
    """Overall system status information."""
    windows_service_running: bool
    macos_daemon_running: bool
    virtual_drive_mounted: bool
    last_sync_time: Optional[datetime]
    last_sync_status: SyncStatus
    pending_updates: List[UpdateInfo]
    active_usb_drives: List[EFISDrive]
    
    @property
    def is_healthy(self) -> bool:
        """Check if system is in healthy state."""
        return (
            self.windows_service_running and
            self.macos_daemon_running and
            self.virtual_drive_mounted and
            self.last_sync_status in [SyncStatus.SUCCESS, SyncStatus.PENDING]
        )


class IVirtualDriveManager:
    """Interface for virtual drive management."""
    
    def check_mount_status(self) -> bool:
        """Check if virtual drive is mounted."""
        raise NotImplementedError
    
    def mount_drive(self) -> bool:
        """Mount the virtual drive."""
        raise NotImplementedError
    
    def unmount_drive(self) -> bool:
        """Unmount the virtual drive."""
        raise NotImplementedError
    
    def get_drive_contents(self) -> List[FileMetadata]:
        """Get list of files on virtual drive."""
        raise NotImplementedError


class INetworkSyncClient:
    """Interface for network synchronization."""
    
    def check_connectivity(self, target: str) -> bool:
        """Check network connectivity to target."""
        raise NotImplementedError
    
    def sync_files(self, source: str, target: str) -> SyncResult:
        """Synchronize files from source to target."""
        raise NotImplementedError
    
    def get_changed_files(self, since: datetime) -> List[FileMetadata]:
        """Get files changed since specified time."""
        raise NotImplementedError


class IGRTWebScraper:
    """Interface for GRT website scraping."""
    
    def check_for_updates(self) -> List[UpdateInfo]:
        """Check for available updates."""
        raise NotImplementedError
    
    def download_file(self, url: str, destination: str) -> DownloadResult:
        """Download file from URL."""
        raise NotImplementedError
    
    def parse_version_info(self, html: str, update_type: UpdateType) -> Optional[str]:
        """Parse version information from HTML."""
        raise NotImplementedError


class IUSBDriveProcessor:
    """Interface for USB drive processing."""
    
    def detect_efis_drive(self, drive_path: str) -> bool:
        """Detect if drive is an EFIS drive."""
        raise NotImplementedError
    
    def process_efis_files(self, drive: EFISDrive) -> ProcessResult:
        """Process files on EFIS drive."""
        raise NotImplementedError
    
    def update_drive_contents(self, drive: EFISDrive) -> ProcessResult:
        """Update drive with current chart data and software."""
        raise NotImplementedError