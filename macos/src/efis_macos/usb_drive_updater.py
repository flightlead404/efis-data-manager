"""
USB drive update system for copying files to EFIS drives with integrity verification.
"""

import os
import time
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

from .config import MacOSConfig
from .usb_drive_processor import SafeDriveAccess


@dataclass
class UpdateFile:
    """Information about a file to be updated on USB drive."""
    source_path: str
    dest_path: str
    size: int
    checksum: Optional[str] = None
    last_modified: Optional[datetime] = None
    
    @classmethod
    def from_source(cls, source_path: Path, dest_relative_path: str) -> 'UpdateFile':
        """Create UpdateFile from source path."""
        stat = source_path.stat()
        return cls(
            source_path=str(source_path),
            dest_path=dest_relative_path,
            size=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime)
        )


@dataclass
class UpdateProgress:
    """Progress information for USB drive updates."""
    total_files: int
    files_copied: int
    files_verified: int
    files_failed: int
    bytes_copied: int
    total_bytes: int
    current_file: Optional[str] = None
    start_time: Optional[datetime] = None
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_bytes == 0:
            return 100.0
        return (self.bytes_copied / self.total_bytes) * 100.0
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def transfer_rate(self) -> float:
        """Calculate transfer rate in bytes per second."""
        elapsed = self.elapsed_time
        if elapsed == 0:
            return 0.0
        return self.bytes_copied / elapsed


class FileIntegrityVerifier:
    """Handles file integrity verification using checksums."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_checksum(self, file_path: Path, algorithm: str = 'md5') -> str:
        """Calculate checksum for a file."""
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""
    
    def verify_file_integrity(self, source_path: Path, dest_path: Path) -> bool:
        """Verify that source and destination files are identical."""
        try:
            # Quick check: file sizes
            if source_path.stat().st_size != dest_path.stat().st_size:
                return False
            
            # For small files, do full checksum comparison
            if source_path.stat().st_size < 1024 * 1024:  # 1MB
                source_checksum = self.calculate_checksum(source_path)
                dest_checksum = self.calculate_checksum(dest_path)
                return source_checksum == dest_checksum
            
            # For larger files, do sampling verification
            return self._verify_by_sampling(source_path, dest_path)
            
        except Exception as e:
            self.logger.error(f"Error verifying file integrity: {e}")
            return False
    
    def _verify_by_sampling(self, source_path: Path, dest_path: Path, samples: int = 5) -> bool:
        """Verify large files by sampling chunks at different positions."""
        try:
            file_size = source_path.stat().st_size
            chunk_size = 4096
            
            # Sample at beginning, end, and random positions
            positions = [0, file_size - chunk_size]
            
            # Add random positions
            import random
            for _ in range(samples - 2):
                pos = random.randint(chunk_size, file_size - chunk_size)
                positions.append(pos)
            
            with open(source_path, 'rb') as src, open(dest_path, 'rb') as dst:
                for pos in positions:
                    src.seek(pos)
                    dst.seek(pos)
                    
                    src_chunk = src.read(chunk_size)
                    dst_chunk = dst.read(chunk_size)
                    
                    if src_chunk != dst_chunk:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in sampling verification: {e}")
            return False


class IncrementalCopyManager:
    """Manages incremental file copying to USB drives."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.safe_access = SafeDriveAccess()
        self.verifier = FileIntegrityVerifier()
    
    def get_update_files(self, source_dirs: List[str], drive_path: Path) -> List[UpdateFile]:
        """Get list of files that need to be updated on the drive."""
        update_files = []
        
        for source_dir in source_dirs:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue
            
            # Scan for files to update
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path for destination
                    rel_path = file_path.relative_to(source_path)
                    dest_path = drive_path / rel_path
                    
                    # Check if file needs updating
                    if self._needs_update(file_path, dest_path):
                        update_file = UpdateFile.from_source(file_path, str(rel_path))
                        update_files.append(update_file)
        
        return update_files
    
    def _needs_update(self, source_path: Path, dest_path: Path) -> bool:
        """Check if a file needs to be updated on the destination."""
        if not dest_path.exists():
            return True
        
        try:
            source_stat = source_path.stat()
            dest_stat = dest_path.stat()
            
            # Check if source is newer
            if source_stat.st_mtime > dest_stat.st_mtime:
                return True
            
            # Check if sizes differ
            if source_stat.st_size != dest_stat.st_size:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking update need for {source_path}: {e}")
            return True
    
    def copy_files_incremental(self, update_files: List[UpdateFile], drive_path: Path, 
                             progress_callback=None) -> Dict[str, any]:
        """Copy files incrementally with progress tracking."""
        results = {
            'success': True,
            'files_copied': 0,
            'files_verified': 0,
            'files_failed': 0,
            'bytes_copied': 0,
            'errors': [],
            'warnings': []
        }
        
        if not update_files:
            return results
        
        # Initialize progress
        total_bytes = sum(f.size for f in update_files)
        progress = UpdateProgress(
            total_files=len(update_files),
            files_copied=0,
            files_verified=0,
            files_failed=0,
            bytes_copied=0,
            total_bytes=total_bytes,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Starting incremental copy of {len(update_files)} files ({total_bytes / (1024*1024):.1f} MB)")
        
        for update_file in update_files:
            try:
                progress.current_file = update_file.dest_path
                
                if progress_callback:
                    progress_callback(progress)
                
                # Copy the file
                source_path = Path(update_file.source_path)
                dest_path = drive_path / update_file.dest_path
                
                if self._copy_file_with_verification(source_path, dest_path):
                    results['files_copied'] += 1
                    results['files_verified'] += 1
                    progress.files_copied += 1
                    progress.files_verified += 1
                    progress.bytes_copied += update_file.size
                    
                    self.logger.debug(f"Successfully copied: {update_file.dest_path}")
                else:
                    results['files_failed'] += 1
                    progress.files_failed += 1
                    results['errors'].append(f"Failed to copy: {update_file.dest_path}")
                    
            except Exception as e:
                results['files_failed'] += 1
                progress.files_failed += 1
                error_msg = f"Error copying {update_file.dest_path}: {e}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        # Final progress update
        if progress_callback:
            progress_callback(progress)
        
        results['bytes_copied'] = progress.bytes_copied
        results['success'] = results['files_failed'] == 0
        
        self.logger.info(f"Copy complete: {results['files_copied']} copied, {results['files_failed']} failed")
        
        return results
    
    def _copy_file_with_verification(self, source_path: Path, dest_path: Path, max_retries: int = 3) -> bool:
        """Copy a file with integrity verification and retries."""
        for attempt in range(max_retries):
            try:
                # Copy the file
                if self.safe_access.safe_copy_file(source_path, dest_path, verify=False):
                    # Verify integrity
                    if self.verifier.verify_file_integrity(source_path, dest_path):
                        return True
                    else:
                        self.logger.warning(f"Integrity check failed for {dest_path}, attempt {attempt + 1}")
                        if dest_path.exists():
                            dest_path.unlink()
                else:
                    self.logger.warning(f"Copy failed for {dest_path}, attempt {attempt + 1}")
                
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                self.logger.warning(f"Copy attempt {attempt + 1} failed for {dest_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
        
        return False


class SafeEjectManager:
    """Handles safe ejection of USB drives."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def eject_drive(self, drive_path: str, device_path: str) -> bool:
        """Safely eject a USB drive."""
        try:
            self.logger.info(f"Ejecting drive: {drive_path}")
            
            # Sync file system first
            self._sync_filesystem()
            
            # Unmount the drive
            result = subprocess.run(
                ["diskutil", "unmount", drive_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully ejected drive: {drive_path}")
                return True
            else:
                self.logger.error(f"Failed to eject drive: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error ejecting drive: {e}")
            return False
    
    def _sync_filesystem(self):
        """Sync filesystem to ensure all writes are completed."""
        try:
            subprocess.run(["sync"], check=False, timeout=10)
            time.sleep(1)  # Give a moment for sync to complete
        except Exception as e:
            self.logger.debug(f"Sync command failed: {e}")
    
    def is_drive_ejectable(self, drive_path: str) -> bool:
        """Check if a drive can be safely ejected."""
        try:
            # Check if any processes are using the drive
            result = subprocess.run(
                ["lsof", "+D", drive_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # If lsof returns processes, drive is in use
            return result.returncode != 0 or not result.stdout.strip()
            
        except Exception as e:
            self.logger.debug(f"Error checking drive usage: {e}")
            return True  # Assume ejectable if we can't check


class USBDriveUpdater:
    """Main USB drive update system coordinator."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.copy_manager = IncrementalCopyManager(config)
        self.eject_manager = SafeEjectManager()
    
    def update_drive(self, drive_path: str, device_path: str, 
                    update_sources: List[str] = None, 
                    progress_callback=None) -> Dict[str, any]:
        """Update a USB drive with files from specified sources."""
        if update_sources is None:
            update_sources = [
                self.config.archive_path,  # Navigation databases and software
                str(Path(self.config.demo_path).parent / "grt_downloads")  # Downloaded GRT files
            ]
        
        results = {
            'success': False,
            'files_updated': 0,
            'bytes_transferred': 0,
            'errors': [],
            'warnings': [],
            'ejected': False
        }
        
        try:
            drive_path_obj = Path(drive_path)
            
            self.logger.info(f"Starting USB drive update: {drive_path}")
            
            # Check available space
            available_space = self._get_available_space(drive_path)
            if available_space < 100 * 1024 * 1024:  # 100MB minimum
                results['warnings'].append("Low disk space on USB drive")
            
            # Get files to update
            update_files = self.copy_manager.get_update_files(update_sources, drive_path_obj)
            
            if not update_files:
                self.logger.info("No files need updating")
                results['success'] = True
                return results
            
            # Calculate total size needed
            total_size = sum(f.size for f in update_files)
            if total_size > available_space:
                error_msg = f"Insufficient space: need {total_size / (1024*1024):.1f}MB, have {available_space / (1024*1024):.1f}MB"
                results['errors'].append(error_msg)
                return results
            
            # Copy files
            copy_results = self.copy_manager.copy_files_incremental(
                update_files, drive_path_obj, progress_callback
            )
            
            results.update({
                'success': copy_results['success'],
                'files_updated': copy_results['files_copied'],
                'bytes_transferred': copy_results['bytes_copied'],
                'errors': copy_results['errors'],
                'warnings': copy_results['warnings']
            })
            
            if copy_results['success']:
                self.logger.info(f"Drive update completed successfully: {results['files_updated']} files updated")
            else:
                self.logger.warning(f"Drive update completed with errors: {len(results['errors'])} errors")
            
        except Exception as e:
            error_msg = f"Error updating drive: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def eject_drive_safely(self, drive_path: str, device_path: str) -> bool:
        """Safely eject a USB drive after updates."""
        try:
            if not self.eject_manager.is_drive_ejectable(drive_path):
                self.logger.warning(f"Drive is in use, cannot eject safely: {drive_path}")
                return False
            
            return self.eject_manager.eject_drive(drive_path, device_path)
            
        except Exception as e:
            self.logger.error(f"Error ejecting drive: {e}")
            return False
    
    def _get_available_space(self, drive_path: str) -> int:
        """Get available space on drive in bytes."""
        try:
            import shutil
            stat = shutil.disk_usage(drive_path)
            return stat.free
        except Exception as e:
            self.logger.error(f"Error getting available space: {e}")
            return 0
    
    def create_update_manifest(self, drive_path: str, update_files: List[UpdateFile]) -> bool:
        """Create a manifest file listing all updated files with checksums."""
        try:
            manifest_path = Path(drive_path) / ".efis_update_manifest.txt"
            
            with open(manifest_path, 'w') as f:
                f.write(f"# EFIS Drive Update Manifest\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Files: {len(update_files)}\n\n")
                
                for update_file in update_files:
                    f.write(f"{update_file.dest_path}\t{update_file.size}\t{update_file.checksum or 'N/A'}\n")
            
            self.logger.info(f"Created update manifest: {manifest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating update manifest: {e}")
            return False