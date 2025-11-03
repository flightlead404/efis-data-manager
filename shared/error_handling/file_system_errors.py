"""
Robust file system error handling and recovery for EFIS Data Manager.
"""

import os
import sys
import time
import shutil
import hashlib
import tempfile
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import contextmanager
from enum import Enum


class FileOperationError(Exception):
    """Base exception for file operation errors."""
    pass


class FileLockError(FileOperationError):
    """Exception raised when file is locked."""
    pass


class DiskSpaceError(FileOperationError):
    """Exception raised when insufficient disk space."""
    pass


class PermissionError(FileOperationError):
    """Exception raised when permission denied."""
    pass


class FileSystemErrorType(Enum):
    """Types of file system errors."""
    FILE_LOCKED = "file_locked"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"
    PATH_NOT_FOUND = "path_not_found"
    NETWORK_DRIVE_UNAVAILABLE = "network_drive_unavailable"
    CORRUPTION = "corruption"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class FileOperationResult:
    """Result of a file operation."""
    success: bool
    error_type: Optional[FileSystemErrorType] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    duration: float = 0.0
    bytes_processed: int = 0


@dataclass
class DiskSpaceInfo:
    """Disk space information."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float
    path: str
    timestamp: datetime


class FileSystemErrorHandler:
    """
    Comprehensive file system error handler with retry logic and recovery.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler."""
        self.logger = logger or logging.getLogger(__name__)
        self.retry_delays = [0.1, 0.5, 1.0, 2.0, 5.0]  # Exponential backoff
        self.max_retries = 3
        self.file_locks: Dict[str, threading.Lock] = {}
        self.lock_registry_lock = threading.Lock()
        
    def handle_file_operation(
        self,
        operation: Callable[[], Any],
        operation_name: str,
        file_path: Union[str, Path],
        max_retries: Optional[int] = None,
        custom_retry_delays: Optional[List[float]] = None
    ) -> FileOperationResult:
        """
        Execute file operation with comprehensive error handling and retry logic.
        
        Args:
            operation: Function to execute
            operation_name: Name of operation for logging
            file_path: Path to file being operated on
            max_retries: Maximum retry attempts (overrides default)
            custom_retry_delays: Custom retry delay sequence
            
        Returns:
            FileOperationResult with operation outcome
        """
        start_time = time.time()
        file_path = Path(file_path)
        retry_delays = custom_retry_delays or self.retry_delays
        max_attempts = (max_retries or self.max_retries) + 1
        
        last_error = None
        error_type = FileSystemErrorType.UNKNOWN
        
        for attempt in range(max_attempts):
            try:
                self.logger.debug(f"Attempting {operation_name} on {file_path} (attempt {attempt + 1})")
                
                # Pre-operation checks
                self._pre_operation_checks(file_path, operation_name)
                
                # Execute operation
                result = operation()
                
                # Success
                duration = time.time() - start_time
                self.logger.debug(f"Successfully completed {operation_name} on {file_path} in {duration:.2f}s")
                
                return FileOperationResult(
                    success=True,
                    retry_count=attempt,
                    duration=duration,
                    bytes_processed=self._get_file_size(file_path)
                )
                
            except Exception as e:
                last_error = e
                error_type = self._classify_error(e, file_path)
                
                self.logger.warning(
                    f"{operation_name} failed on {file_path} (attempt {attempt + 1}): {e}",
                    extra={
                        'operation': operation_name,
                        'file_path': str(file_path),
                        'attempt': attempt + 1,
                        'error_type': error_type.value,
                        'error_message': str(e)
                    }
                )
                
                # Check if we should retry
                if attempt < max_attempts - 1 and self._should_retry(error_type, attempt):
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    self.logger.debug(f"Retrying {operation_name} in {delay}s...")
                    time.sleep(delay)
                    
                    # Attempt recovery based on error type
                    self._attempt_recovery(error_type, file_path)
                else:
                    break
        
        # All attempts failed
        duration = time.time() - start_time
        self.logger.error(
            f"Failed {operation_name} on {file_path} after {max_attempts} attempts: {last_error}",
            extra={
                'operation': operation_name,
                'file_path': str(file_path),
                'total_attempts': max_attempts,
                'error_type': error_type.value,
                'duration': duration
            }
        )
        
        return FileOperationResult(
            success=False,
            error_type=error_type,
            error_message=str(last_error),
            retry_count=max_attempts - 1,
            duration=duration
        )
    
    def _pre_operation_checks(self, file_path: Path, operation_name: str) -> None:
        """Perform pre-operation checks."""
        # Check if parent directory exists for write operations
        if operation_name in ['write', 'copy', 'move'] and not file_path.parent.exists():
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise FileOperationError(f"Cannot create parent directory: {e}")
        
        # Check disk space for write operations
        if operation_name in ['write', 'copy', 'move']:
            self._check_disk_space(file_path.parent)
    
    def _classify_error(self, error: Exception, file_path: Path) -> FileSystemErrorType:
        """Classify error type for appropriate handling."""
        error_str = str(error).lower()
        
        if isinstance(error, PermissionError) or 'permission denied' in error_str:
            return FileSystemErrorType.PERMISSION_DENIED
        elif isinstance(error, FileNotFoundError) or 'no such file' in error_str:
            return FileSystemErrorType.PATH_NOT_FOUND
        elif 'no space left' in error_str or 'disk full' in error_str:
            return FileSystemErrorType.DISK_FULL
        elif 'sharing violation' in error_str or 'being used by another process' in error_str:
            return FileSystemErrorType.FILE_LOCKED
        elif 'network' in error_str or 'remote' in error_str:
            return FileSystemErrorType.NETWORK_DRIVE_UNAVAILABLE
        elif 'timeout' in error_str:
            return FileSystemErrorType.TIMEOUT
        elif 'corrupt' in error_str or 'invalid' in error_str:
            return FileSystemErrorType.CORRUPTION
        else:
            return FileSystemErrorType.UNKNOWN
    
    def _should_retry(self, error_type: FileSystemErrorType, attempt: int) -> bool:
        """Determine if operation should be retried based on error type."""
        # Don't retry certain error types
        non_retryable = {
            FileSystemErrorType.PERMISSION_DENIED,
            FileSystemErrorType.DISK_FULL,
            FileSystemErrorType.CORRUPTION
        }
        
        if error_type in non_retryable:
            return False
        
        # Retry transient errors
        return True
    
    def _attempt_recovery(self, error_type: FileSystemErrorType, file_path: Path) -> None:
        """Attempt recovery based on error type."""
        try:
            if error_type == FileSystemErrorType.FILE_LOCKED:
                # Wait for file lock to be released
                self._wait_for_file_unlock(file_path)
            elif error_type == FileSystemErrorType.NETWORK_DRIVE_UNAVAILABLE:
                # Try to reconnect network drive
                self._reconnect_network_drive(file_path)
            elif error_type == FileSystemErrorType.PATH_NOT_FOUND:
                # Try to create missing directories
                if file_path.parent:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.debug(f"Recovery attempt failed: {e}")
    
    def _wait_for_file_unlock(self, file_path: Path, timeout: float = 5.0) -> None:
        """Wait for file to be unlocked."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to open file in exclusive mode
                if file_path.exists():
                    with open(file_path, 'r+b'):
                        pass
                return
            except (PermissionError, OSError):
                time.sleep(0.1)
        
        self.logger.debug(f"File still locked after {timeout}s: {file_path}")
    
    def _reconnect_network_drive(self, file_path: Path) -> None:
        """Attempt to reconnect network drive."""
        # This is platform-specific and would need implementation
        # based on the specific network drive setup
        pass
    
    def _check_disk_space(self, path: Path, min_free_mb: int = 100) -> None:
        """Check available disk space."""
        try:
            stat = shutil.disk_usage(path)
            free_mb = stat.free / (1024 * 1024)
            
            if free_mb < min_free_mb:
                raise DiskSpaceError(f"Insufficient disk space: {free_mb:.1f}MB available, {min_free_mb}MB required")
        except Exception as e:
            if "disk space" in str(e).lower():
                raise
            # If we can't check disk space, log warning but don't fail
            self.logger.warning(f"Could not check disk space for {path}: {e}")
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size safely."""
        try:
            if file_path.exists():
                return file_path.stat().st_size
        except Exception:
            pass
        return 0
    
    def get_file_lock(self, file_path: Union[str, Path]) -> threading.Lock:
        """Get or create a lock for a specific file path."""
        file_path_str = str(file_path)
        
        with self.lock_registry_lock:
            if file_path_str not in self.file_locks:
                self.file_locks[file_path_str] = threading.Lock()
            return self.file_locks[file_path_str]


class AtomicFileOperation:
    """
    Provides atomic file operations with rollback capability.
    """
    
    def __init__(self, error_handler: FileSystemErrorHandler):
        """Initialize atomic file operations."""
        self.error_handler = error_handler
        self.logger = error_handler.logger
        
    @contextmanager
    def atomic_write(self, target_path: Union[str, Path], backup: bool = True):
        """
        Context manager for atomic file writes with rollback.
        
        Args:
            target_path: Final file path
            backup: Whether to create backup of existing file
            
        Yields:
            Temporary file path to write to
        """
        target_path = Path(target_path)
        temp_path = None
        backup_path = None
        
        try:
            # Create temporary file in same directory
            temp_path = target_path.with_suffix(target_path.suffix + '.tmp')
            
            # Create backup if requested and file exists
            if backup and target_path.exists():
                backup_path = target_path.with_suffix(target_path.suffix + '.backup')
                shutil.copy2(target_path, backup_path)
            
            yield temp_path
            
            # Atomic move to final location
            if temp_path.exists():
                temp_path.replace(target_path)
                self.logger.debug(f"Atomic write completed: {target_path}")
            
            # Remove backup on success
            if backup_path and backup_path.exists():
                backup_path.unlink()
                
        except Exception as e:
            # Rollback on error
            if temp_path and temp_path.exists():
                temp_path.unlink()
            
            if backup_path and backup_path.exists():
                if target_path.exists():
                    target_path.unlink()
                backup_path.replace(target_path)
                self.logger.info(f"Rolled back to backup: {target_path}")
            
            raise e
    
    def atomic_copy(self, src_path: Union[str, Path], dst_path: Union[str, Path], 
                   verify: bool = True) -> FileOperationResult:
        """
        Perform atomic file copy with verification.
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            verify: Whether to verify copy integrity
            
        Returns:
            FileOperationResult
        """
        src_path = Path(src_path)
        dst_path = Path(dst_path)
        
        def copy_operation():
            with self.atomic_write(dst_path) as temp_path:
                shutil.copy2(src_path, temp_path)
                
                if verify:
                    if not self._verify_copy(src_path, temp_path):
                        raise FileOperationError("Copy verification failed")
        
        return self.error_handler.handle_file_operation(
            copy_operation,
            "atomic_copy",
            dst_path
        )
    
    def atomic_move(self, src_path: Union[str, Path], dst_path: Union[str, Path]) -> FileOperationResult:
        """
        Perform atomic file move.
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            
        Returns:
            FileOperationResult
        """
        src_path = Path(src_path)
        dst_path = Path(dst_path)
        
        def move_operation():
            # Try direct rename first (fastest if on same filesystem)
            try:
                src_path.rename(dst_path)
                return
            except OSError:
                pass
            
            # Fall back to copy + delete
            with self.atomic_write(dst_path) as temp_path:
                shutil.copy2(src_path, temp_path)
                
                # Verify copy before deleting source
                if self._verify_copy(src_path, temp_path):
                    src_path.unlink()
                else:
                    raise FileOperationError("Move verification failed")
        
        return self.error_handler.handle_file_operation(
            move_operation,
            "atomic_move",
            dst_path
        )
    
    def _verify_copy(self, src_path: Path, dst_path: Path) -> bool:
        """Verify file copy integrity."""
        try:
            # Compare file sizes
            src_size = src_path.stat().st_size
            dst_size = dst_path.stat().st_size
            
            if src_size != dst_size:
                return False
            
            # For larger files, compare checksums
            if src_size > 1024 * 1024:  # 1MB
                return self._compare_checksums(src_path, dst_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Copy verification error: {e}")
            return False
    
    def _compare_checksums(self, file1: Path, file2: Path) -> bool:
        """Compare file checksums."""
        try:
            hash1 = self._calculate_checksum(file1)
            hash2 = self._calculate_checksum(file2)
            return hash1 == hash2
        except Exception:
            return False
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum."""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


class DiskSpaceMonitor:
    """
    Monitors disk space and provides cleanup procedures.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize disk space monitor."""
        self.logger = logger or logging.getLogger(__name__)
        self.monitored_paths: Dict[str, DiskSpaceInfo] = {}
        self.warning_threshold = 0.85  # 85% usage
        self.critical_threshold = 0.95  # 95% usage
        self.cleanup_handlers: List[Callable[[str], int]] = []
        
    def add_path(self, path: Union[str, Path]) -> None:
        """Add path to monitoring."""
        path_str = str(path)
        self.monitored_paths[path_str] = self._get_disk_space_info(path_str)
        self.logger.debug(f"Added path to disk space monitoring: {path_str}")
    
    def check_all_paths(self) -> Dict[str, DiskSpaceInfo]:
        """Check disk space for all monitored paths."""
        results = {}
        
        for path in self.monitored_paths.keys():
            try:
                info = self._get_disk_space_info(path)
                results[path] = info
                self.monitored_paths[path] = info
                
                # Check thresholds
                if info.usage_percent >= self.critical_threshold:
                    self.logger.critical(
                        f"Critical disk space: {path} is {info.usage_percent:.1f}% full",
                        extra={'disk_usage': info.usage_percent, 'path': path}
                    )
                    self._trigger_cleanup(path)
                elif info.usage_percent >= self.warning_threshold:
                    self.logger.warning(
                        f"Low disk space: {path} is {info.usage_percent:.1f}% full",
                        extra={'disk_usage': info.usage_percent, 'path': path}
                    )
                    
            except Exception as e:
                self.logger.error(f"Error checking disk space for {path}: {e}")
        
        return results
    
    def _get_disk_space_info(self, path: str) -> DiskSpaceInfo:
        """Get disk space information for path."""
        stat = shutil.disk_usage(path)
        usage_percent = (stat.used / stat.total) * 100
        
        return DiskSpaceInfo(
            total_bytes=stat.total,
            used_bytes=stat.used,
            free_bytes=stat.free,
            usage_percent=usage_percent,
            path=path,
            timestamp=datetime.now()
        )
    
    def add_cleanup_handler(self, handler: Callable[[str], int]) -> None:
        """
        Add cleanup handler function.
        
        Args:
            handler: Function that takes path and returns bytes freed
        """
        self.cleanup_handlers.append(handler)
    
    def _trigger_cleanup(self, path: str) -> None:
        """Trigger cleanup procedures for path."""
        total_freed = 0
        
        for handler in self.cleanup_handlers:
            try:
                freed = handler(path)
                total_freed += freed
                self.logger.info(f"Cleanup freed {freed} bytes on {path}")
            except Exception as e:
                self.logger.error(f"Cleanup handler failed: {e}")
        
        if total_freed > 0:
            self.logger.info(f"Total cleanup freed {total_freed} bytes on {path}")


class PermissionChecker:
    """
    Checks and manages file system permissions.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize permission checker."""
        self.logger = logger or logging.getLogger(__name__)
        
    def check_permissions(self, path: Union[str, Path], 
                         required_permissions: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if path has required permissions.
        
        Args:
            path: Path to check
            required_permissions: List of permissions ('read', 'write', 'execute')
            
        Returns:
            Tuple of (has_permissions, missing_permissions)
        """
        path = Path(path)
        missing = []
        
        try:
            if not path.exists():
                missing.append("path_not_found")
                return False, missing
            
            for permission in required_permissions:
                if permission == 'read' and not os.access(path, os.R_OK):
                    missing.append('read')
                elif permission == 'write' and not os.access(path, os.W_OK):
                    missing.append('write')
                elif permission == 'execute' and not os.access(path, os.X_OK):
                    missing.append('execute')
            
            return len(missing) == 0, missing
            
        except Exception as e:
            self.logger.error(f"Error checking permissions for {path}: {e}")
            return False, [f"error: {e}"]
    
    def get_permission_guidance(self, path: Union[str, Path], 
                              missing_permissions: List[str]) -> str:
        """
        Get user guidance for fixing permission issues.
        
        Args:
            path: Path with permission issues
            missing_permissions: List of missing permissions
            
        Returns:
            Human-readable guidance string
        """
        path = Path(path)
        platform = sys.platform
        
        if "path_not_found" in missing_permissions:
            return f"Path does not exist: {path}. Please ensure the path is correct."
        
        if platform.startswith('win'):
            return self._get_windows_permission_guidance(path, missing_permissions)
        else:
            return self._get_unix_permission_guidance(path, missing_permissions)
    
    def _get_windows_permission_guidance(self, path: Path, missing: List[str]) -> str:
        """Get Windows-specific permission guidance."""
        guidance = f"Permission denied for {path}.\n"
        
        if 'write' in missing:
            guidance += "- Try running as Administrator\n"
            guidance += "- Check if file is read-only\n"
            guidance += "- Ensure no other program is using the file\n"
        
        if 'read' in missing:
            guidance += "- Check file/folder permissions in Properties\n"
            guidance += "- Ensure you have access to the parent directory\n"
        
        return guidance
    
    def _get_unix_permission_guidance(self, path: Path, missing: List[str]) -> str:
        """Get Unix/macOS-specific permission guidance."""
        guidance = f"Permission denied for {path}.\n"
        
        if 'write' in missing:
            guidance += f"- Try: chmod u+w {path}\n"
            guidance += "- Check if filesystem is read-only\n"
        
        if 'read' in missing:
            guidance += f"- Try: chmod u+r {path}\n"
        
        if 'execute' in missing:
            guidance += f"- Try: chmod u+x {path}\n"
        
        guidance += "- You may need to use sudo for system directories\n"
        
        return guidance