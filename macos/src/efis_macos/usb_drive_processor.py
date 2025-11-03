"""
USB drive detection and processing for EFIS Data Manager.
"""

import os
import re
import time
import shutil
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

from .config import MacOSConfig


@dataclass
class EFISDriveInfo:
    """Information about an EFIS USB drive."""
    mount_path: str
    device_path: str
    capacity: int
    file_system: str
    identifier: str
    demo_files: List[str]
    snap_files: List[str]
    logbook_files: List[str]


@dataclass
class ProcessingResult:
    """Result of USB drive processing operation."""
    success: bool
    files_processed: int
    files_moved: int
    files_copied: int
    errors: List[str]
    warnings: List[str]


class USBDriveDetector:
    """Detects and monitors USB drives on macOS."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._known_drives: Set[str] = set()
    
    def check_permissions(self) -> bool:
        """Check if we have necessary permissions for USB detection."""
        try:
            # Test if we can run diskutil (this should not require special permissions)
            result = subprocess.run(
                ["diskutil", "list"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
    
    def get_mounted_drives(self) -> List[Dict[str, str]]:
        """Get list of currently mounted USB drives only."""
        drives = []
        
        try:
            # Use diskutil to get all disks
            result = subprocess.run(
                ["diskutil", "list", "-plist"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get mount information
            mount_result = subprocess.run(
                ["mount"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse mount output for physical drives only
            for line in mount_result.stdout.split('\n'):
                if '/dev/disk' in line and '/Volumes/' in line:
                    parts = line.split(' on ')
                    if len(parts) >= 2:
                        device = parts[0].strip()
                        mount_info = parts[1].split(' (')
                        mount_path = mount_info[0].strip()
                        
                        # Skip cloud storage and system mounts
                        if self._is_cloud_or_system_mount(mount_path):
                            continue
                        
                        # Only check physical removable drives
                        if self._is_physical_removable_drive(device):
                            drive_info = self._get_drive_info(device, mount_path)
                            if drive_info:
                                drives.append(drive_info)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error getting mounted drives: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error getting drives: {e}")
        
        return drives
    
    def _is_cloud_or_system_mount(self, mount_path: str) -> bool:
        """Check if a mount path is a cloud storage or system mount."""
        cloud_indicators = [
            'icloud', 'onedrive', 'dropbox', 'googledrive', 'box',
            'library/cloudstorage', 'library/mobile documents',
            'com~apple~', '.localized', 'desktop', 'documents',
            'downloads', 'pictures', 'movies', 'music'
        ]
        
        mount_lower = mount_path.lower()
        return any(indicator in mount_lower for indicator in cloud_indicators)
    
    def _is_physical_removable_drive(self, device_path: str) -> bool:
        """Check if a device is a physical removable USB drive."""
        try:
            result = subprocess.run(
                ["diskutil", "info", device_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            output = result.stdout.lower()
            
            # Must be removable media
            if not ('removable media:' in output and 'yes' in output):
                return False
            
            # Must be USB protocol
            if not (('protocol:' in output and 'usb' in output) or 
                   ('bus:' in output and 'usb' in output)):
                return False
            
            # Exclude virtual drives and disk images
            if any(indicator in output for indicator in ['virtual', 'disk image', 'ram disk']):
                return False
            
            return True
            
        except subprocess.CalledProcessError:
            return False
    
    def _get_drive_info(self, device_path: str, mount_path: str) -> Optional[Dict[str, str]]:
        """Get detailed information about a drive."""
        try:
            result = subprocess.run(
                ["diskutil", "info", device_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip().lower()] = value.strip()
            
            # Get capacity in bytes
            capacity = 0
            if 'disk size' in info:
                size_str = info['disk size']
                # Parse size like "7.8 GB (7751073792 Bytes)"
                if '(' in size_str and 'bytes' in size_str.lower():
                    bytes_part = size_str.split('(')[1].split(' ')[0]
                    try:
                        capacity = int(bytes_part)
                    except ValueError:
                        pass
            
            return {
                'device_path': device_path,
                'mount_path': mount_path,
                'capacity': capacity,
                'file_system': info.get('file system personality', 'Unknown'),
                'volume_name': info.get('volume name', 'Unknown')
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.debug(f"Could not get info for {device_path}: {e}")
            return None
    
    def detect_new_drives(self) -> List[Dict[str, str]]:
        """Detect newly connected drives."""
        current_drives = self.get_mounted_drives()
        new_drives = []
        
        current_paths = {drive['mount_path'] for drive in current_drives}
        
        for drive in current_drives:
            if drive['mount_path'] not in self._known_drives:
                new_drives.append(drive)
                self.logger.info(f"Detected new USB drive: {drive['mount_path']}")
        
        # Update known drives
        self._known_drives = current_paths
        
        return new_drives
    
    def monitor_drives(self, callback, interval: int = 2):
        """Monitor for new USB drives and call callback when detected."""
        self.logger.info("Starting USB drive monitoring...")
        
        # Initialize known drives
        initial_drives = self.get_mounted_drives()
        self._known_drives = {drive['mount_path'] for drive in initial_drives}
        
        while True:
            try:
                new_drives = self.detect_new_drives()
                for drive in new_drives:
                    callback(drive)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("USB drive monitoring stopped")
                break
            except Exception as e:
                self.logger.error(f"Error in drive monitoring: {e}")
                time.sleep(interval)


class EFISDriveIdentifier:
    """Identifies EFIS drives using file system markers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # EFIS drive identification markers
        self.efis_markers = [
            'EFIS_DRIVE.txt',  # Custom marker file
            'NAV.DB',          # Navigation database
            'DEMO',            # Demo files directory
            'SNAP'             # Snapshot files directory
        ]
        
        # File patterns for EFIS files
        self.demo_pattern = re.compile(r'DEMO-\d{8}-\d{6}(?:\+\d+)?\.LOG$', re.IGNORECASE)
        self.snap_pattern = re.compile(r'.*\.png$', re.IGNORECASE)
        self.logbook_pattern = re.compile(r'.*logbook.*\.csv$', re.IGNORECASE)
    
    def is_efis_drive(self, drive_info: Dict[str, str]) -> bool:
        """Check if a drive is an EFIS drive using file system markers."""
        mount_path = Path(drive_info['mount_path'])
        
        if not mount_path.exists():
            return False
        
        try:
            # Check for EFIS marker files/directories
            marker_count = 0
            for marker in self.efis_markers:
                marker_path = mount_path / marker
                if marker_path.exists():
                    marker_count += 1
                    self.logger.debug(f"Found EFIS marker: {marker}")
            
            # Consider it an EFIS drive if we find at least 2 markers
            # or if we find specific combinations
            if marker_count >= 2:
                return True
            
            # Check for EFIS-specific file patterns
            efis_files = self._scan_for_efis_files(mount_path)
            if efis_files['demo_files'] or efis_files['snap_files']:
                return True
            
            # Check drive capacity (EFIS drives are typically 8GB or larger)
            capacity_gb = drive_info.get('capacity', 0) / (1024**3)
            if capacity_gb >= 4.0:  # At least 4GB
                # Look for any aviation-related files
                if self._has_aviation_files(mount_path):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking EFIS drive markers: {e}")
            return False
    
    def _scan_for_efis_files(self, mount_path: Path) -> Dict[str, List[str]]:
        """Scan drive for EFIS-specific files with limited depth."""
        efis_files = {
            'demo_files': [],
            'snap_files': [],
            'logbook_files': []
        }
        
        try:
            # Check if we have permission to access the drive
            if not os.access(mount_path, os.R_OK):
                self.logger.warning(f"No read permission for {mount_path}")
                return efis_files
            
            # Limit scanning to 2 levels deep to avoid deep recursion
            max_depth = 2
            
            for root, dirs, files in os.walk(mount_path):
                # Calculate current depth
                depth = len(Path(root).relative_to(mount_path).parts)
                if depth >= max_depth:
                    dirs.clear()  # Don't recurse deeper
                
                root_path = Path(root)
                
                # Skip hidden directories and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ['system volume information', '$recycle.bin']]
                
                for file in files:
                    # Skip hidden files and system files
                    if file.startswith('.') or file.lower() in ['desktop.ini', 'thumbs.db']:
                        continue
                    
                    try:
                        file_path = root_path / file
                        relative_path = str(file_path.relative_to(mount_path))
                        
                        # Check file patterns
                        if self.demo_pattern.match(file):
                            efis_files['demo_files'].append(relative_path)
                        elif self.snap_pattern.match(file):
                            # Only consider PNG files in SNAP directory or root
                            if 'SNAP' in str(root_path).upper() or root_path == mount_path:
                                efis_files['snap_files'].append(relative_path)
                        elif self.logbook_pattern.match(file):
                            efis_files['logbook_files'].append(relative_path)
                    except Exception as e:
                        # Skip files that cause permission errors
                        self.logger.debug(f"Skipping file {file}: {e}")
                        continue
        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing {mount_path}")
        except Exception as e:
            self.logger.error(f"Error scanning for EFIS files: {e}")
        
        return efis_files
    
    def _has_aviation_files(self, mount_path: Path) -> bool:
        """Check for aviation-related files that might indicate an EFIS drive."""
        aviation_indicators = [
            'nav.db', 'navigation', 'charts', 'waypoints',
            'flight', 'aviation', 'grt', 'garmin', 'efis'
        ]
        
        try:
            for root, dirs, files in os.walk(mount_path):
                # Check directory names
                for dir_name in dirs:
                    if any(indicator in dir_name.lower() for indicator in aviation_indicators):
                        return True
                
                # Check file names
                for file_name in files:
                    if any(indicator in file_name.lower() for indicator in aviation_indicators):
                        return True
                    
                    # Check for specific file extensions
                    if file_name.lower().endswith(('.db', '.nav', '.wpt')):
                        return True
        
        except Exception as e:
            self.logger.debug(f"Error checking aviation files: {e}")
        
        return False
    
    def get_efis_drive_info(self, drive_info: Dict[str, str]) -> Optional[EFISDriveInfo]:
        """Get detailed EFIS drive information."""
        if not self.is_efis_drive(drive_info):
            return None
        
        mount_path = Path(drive_info['mount_path'])
        efis_files = self._scan_for_efis_files(mount_path)
        
        # Create unique identifier for this drive
        identifier = self._generate_drive_identifier(drive_info, efis_files)
        
        return EFISDriveInfo(
            mount_path=str(mount_path),
            device_path=drive_info['device_path'],
            capacity=drive_info.get('capacity', 0),
            file_system=drive_info.get('file_system', 'Unknown'),
            identifier=identifier,
            demo_files=efis_files['demo_files'],
            snap_files=efis_files['snap_files'],
            logbook_files=efis_files['logbook_files']
        )
    
    def _generate_drive_identifier(self, drive_info: Dict[str, str], efis_files: Dict[str, List[str]]) -> str:
        """Generate a unique identifier for the EFIS drive."""
        # Use combination of capacity, file count, and volume name
        capacity = drive_info.get('capacity', 0)
        volume_name = drive_info.get('volume_name', 'Unknown')
        file_count = sum(len(files) for files in efis_files.values())
        
        identifier_string = f"{volume_name}_{capacity}_{file_count}"
        return hashlib.md5(identifier_string.encode()).hexdigest()[:8]


class USBDriveValidator:
    """Validates USB drive capacity and file system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Minimum requirements for EFIS drives
        self.min_capacity_gb = 2.0  # Minimum 2GB
        self.max_capacity_gb = 128.0  # Maximum 128GB (reasonable upper limit)
        self.supported_filesystems = ['FAT32', 'exFAT', 'MSDOS', 'MS-DOS FAT32']
    
    def validate_drive(self, drive_info: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate drive capacity and file system."""
        errors = []
        
        try:
            # Check capacity
            capacity_bytes = drive_info.get('capacity', 0)
            capacity_gb = capacity_bytes / (1024**3) if capacity_bytes > 0 else 0
            
            if capacity_gb < self.min_capacity_gb:
                errors.append(f"Drive capacity too small: {capacity_gb:.1f}GB (minimum {self.min_capacity_gb}GB)")
            elif capacity_gb > self.max_capacity_gb:
                errors.append(f"Drive capacity too large: {capacity_gb:.1f}GB (maximum {self.max_capacity_gb}GB)")
            
            # Check file system
            file_system = drive_info.get('file_system', 'Unknown')
            if file_system not in self.supported_filesystems:
                # Check if it's a variant of FAT32
                if 'FAT' not in file_system.upper() and 'MSDOS' not in file_system.upper():
                    errors.append(f"Unsupported file system: {file_system} (supported: {', '.join(self.supported_filesystems)})")
            
            # Check if drive is writable
            mount_path = Path(drive_info['mount_path'])
            if not self._is_writable(mount_path):
                errors.append("Drive is not writable")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating drive: {e}")
            return False, [f"Validation error: {e}"]
    
    def _is_writable(self, mount_path: Path) -> bool:
        """Check if the drive is writable without actually writing."""
        try:
            # Check write permission without creating files
            return os.access(mount_path, os.W_OK)
        except Exception:
            return False


class SafeDriveAccess:
    """Provides safe access to USB drives with error handling."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._access_locks: Dict[str, bool] = {}
    
    def safe_read_file(self, file_path: Path, max_retries: int = 3) -> Optional[bytes]:
        """Safely read a file with retry logic."""
        for attempt in range(max_retries):
            try:
                if not file_path.exists():
                    return None
                
                return file_path.read_bytes()
                
            except (OSError, IOError) as e:
                self.logger.warning(f"Read attempt {attempt + 1} failed for {file_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to read {file_path} after {max_retries} attempts")
        
        return None
    
    def safe_write_file(self, file_path: Path, data: bytes, max_retries: int = 3) -> bool:
        """Safely write a file with retry logic."""
        for attempt in range(max_retries):
            try:
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write to temporary file first
                temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
                temp_path.write_bytes(data)
                
                # Atomic move to final location
                temp_path.rename(file_path)
                
                return True
                
            except (OSError, IOError) as e:
                self.logger.warning(f"Write attempt {attempt + 1} failed for {file_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to write {file_path} after {max_retries} attempts")
        
        return False
    
    def safe_move_file(self, src_path: Path, dst_path: Path, max_retries: int = 3) -> bool:
        """Safely move a file with retry logic."""
        for attempt in range(max_retries):
            try:
                if not src_path.exists():
                    self.logger.warning(f"Source file does not exist: {src_path}")
                    return False
                
                # Ensure destination directory exists
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(src_path), str(dst_path))
                
                return True
                
            except (OSError, IOError, shutil.Error) as e:
                self.logger.warning(f"Move attempt {attempt + 1} failed from {src_path} to {dst_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to move {src_path} after {max_retries} attempts")
        
        return False
    
    def safe_copy_file(self, src_path: Path, dst_path: Path, verify: bool = True, max_retries: int = 3) -> bool:
        """Safely copy a file with optional verification."""
        for attempt in range(max_retries):
            try:
                if not src_path.exists():
                    self.logger.warning(f"Source file does not exist: {src_path}")
                    return False
                
                # Ensure destination directory exists
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(str(src_path), str(dst_path))
                
                # Verify copy if requested
                if verify and not self._verify_file_copy(src_path, dst_path):
                    self.logger.warning(f"File verification failed for {dst_path}")
                    if dst_path.exists():
                        dst_path.unlink()
                    continue
                
                return True
                
            except (OSError, IOError, shutil.Error) as e:
                self.logger.warning(f"Copy attempt {attempt + 1} failed from {src_path} to {dst_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    self.logger.error(f"Failed to copy {src_path} after {max_retries} attempts")
        
        return False
    
    def _verify_file_copy(self, src_path: Path, dst_path: Path) -> bool:
        """Verify that a file was copied correctly by comparing sizes and checksums."""
        try:
            if not dst_path.exists():
                return False
            
            # Compare file sizes
            if src_path.stat().st_size != dst_path.stat().st_size:
                return False
            
            # Compare checksums for files larger than 1MB
            if src_path.stat().st_size > 1024 * 1024:
                src_hash = self._calculate_file_hash(src_path)
                dst_hash = self._calculate_file_hash(dst_path)
                return src_hash == dst_hash
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying file copy: {e}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def is_drive_accessible(self, mount_path: str) -> bool:
        """Check if a drive is accessible."""
        try:
            path = Path(mount_path)
            return path.exists() and path.is_dir() and os.access(path, os.R_OK)
        except Exception:
            return False
    
    def get_available_space(self, mount_path: str) -> int:
        """Get available space on drive in bytes."""
        try:
            stat = shutil.disk_usage(mount_path)
            return stat.free
        except Exception as e:
            self.logger.error(f"Error getting available space for {mount_path}: {e}")
            return 0


class USBDriveProcessor:
    """Main USB drive processing coordinator."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.detector = USBDriveDetector()
        self.identifier = EFISDriveIdentifier()
        self.validator = USBDriveValidator()
        self.safe_access = SafeDriveAccess()
    
    def process_new_drive(self, drive_info: Dict[str, str]) -> ProcessingResult:
        """Process a newly detected USB drive."""
        self.logger.info(f"Processing new USB drive: {drive_info['mount_path']}")
        
        result = ProcessingResult(
            success=False,
            files_processed=0,
            files_moved=0,
            files_copied=0,
            errors=[],
            warnings=[]
        )
        
        try:
            # Validate the drive
            is_valid, validation_errors = self.validator.validate_drive(drive_info)
            if not is_valid:
                result.errors.extend(validation_errors)
                return result
            
            # Check if it's an EFIS drive
            efis_info = self.identifier.get_efis_drive_info(drive_info)
            if not efis_info:
                result.warnings.append("Drive is not recognized as an EFIS drive")
                return result
            
            self.logger.info(f"Identified EFIS drive: {efis_info.identifier}")
            
            # Process EFIS files using the file processor
            from .efis_file_processor import EFISFileProcessor
            from .usb_drive_updater import USBDriveUpdater
            
            file_processor = EFISFileProcessor(self.config)
            processing_results = file_processor.process_efis_drive(efis_info.mount_path)
            
            if processing_results['success']:
                result.files_moved = processing_results['total_files_processed']
                result.files_processed = (
                    processing_results['demo_files']['detected'] +
                    processing_results['snapshots']['detected'] +
                    processing_results['logbooks']['detected']
                )
                
                # Clean up empty directories
                file_processor.cleanup_drive(efis_info.mount_path)
                
                self.logger.info(f"Successfully processed {result.files_moved} files from EFIS drive")
                
                # Update drive with latest files (navigation databases, software updates)
                updater = USBDriveUpdater(self.config)
                update_results = updater.update_drive(
                    efis_info.mount_path, 
                    efis_info.device_path
                )
                
                if update_results['success']:
                    result.files_copied = update_results['files_updated']
                    self.logger.info(f"Updated {result.files_copied} files on EFIS drive")
                else:
                    result.warnings.extend(update_results['warnings'])
                    if update_results['errors']:
                        result.errors.extend(update_results['errors'])
                
                result.success = True
            else:
                result.errors.extend(processing_results['errors'])
                result.warnings.append("Some files could not be processed")
            
        except Exception as e:
            self.logger.error(f"Error processing USB drive: {e}")
            result.errors.append(f"Processing error: {e}")
        
        return result
    
    def start_monitoring(self):
        """Start monitoring for USB drives."""
        self.logger.info("Starting USB drive monitoring...")
        
        def drive_callback(drive_info):
            """Callback for when a new drive is detected."""
            try:
                result = self.process_new_drive(drive_info)
                if result.success:
                    self.logger.info(f"Successfully processed USB drive: {drive_info['mount_path']}")
                else:
                    self.logger.warning(f"Failed to process USB drive: {', '.join(result.errors)}")
            except Exception as e:
                self.logger.error(f"Error in drive callback: {e}")
        
        # Start monitoring in a separate thread
        self.detector.monitor_drives(drive_callback)