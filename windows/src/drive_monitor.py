"""
Drive monitoring and auto-remount logic for EFIS Data Manager.
Provides robust monitoring of virtual drive status with automatic recovery.
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

from imdisk_wrapper import VirtualDriveManager, DriveInfo, MountResult


class MonitoringState(Enum):
    """States for drive monitoring."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class MonitoringStats:
    """Statistics for drive monitoring operations."""
    start_time: datetime
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    mount_attempts: int = 0
    successful_mounts: int = 0
    failed_mounts: int = 0
    last_check_time: Optional[datetime] = None
    last_mount_time: Optional[datetime] = None
    consecutive_failures: int = 0
    
    @property
    def uptime(self) -> timedelta:
        """Get monitoring uptime."""
        return datetime.now() - self.start_time
        
    @property
    def success_rate(self) -> float:
        """Get check success rate as percentage."""
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100
        
    @property
    def mount_success_rate(self) -> float:
        """Get mount success rate as percentage."""
        if self.mount_attempts == 0:
            return 0.0
        return (self.successful_mounts / self.mount_attempts) * 100


class DriveMonitor:
    """
    Advanced drive monitoring with automatic remounting and failure recovery.
    
    Provides continuous monitoring of virtual drive status with configurable
    check intervals, retry logic, and failure handling.
    """
    
    def __init__(self, drive_manager: VirtualDriveManager, config: Dict[str, Any], 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize drive monitor.
        
        Args:
            drive_manager: VirtualDriveManager instance
            config: Configuration dictionary
            logger: Logger instance
        """
        self.drive_manager = drive_manager
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Monitoring configuration
        self.check_interval = config.get('checkInterval', 300)  # 5 minutes default
        self.retry_delay = config.get('remountRetryDelay', 60)  # 1 minute default
        self.max_consecutive_failures = config.get('maxConsecutiveFailures', 5)
        self.failure_escalation_delay = config.get('failureEscalationDelay', 300)  # 5 minutes
        
        # State management
        self.state = MonitoringState.STOPPED
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.monitor_thread = None
        
        # Statistics and tracking
        self.stats = MonitoringStats(start_time=datetime.now())
        self.last_known_good_state = None
        self.failure_timestamps = []
        
        # Callbacks for events
        self.on_mount_success: Optional[Callable[[DriveInfo], None]] = None
        self.on_mount_failure: Optional[Callable[[str], None]] = None
        self.on_drive_lost: Optional[Callable[[], None]] = None
        self.on_drive_recovered: Optional[Callable[[DriveInfo], None]] = None
        
        self.logger.info(f"Drive monitor initialized (check interval: {self.check_interval}s)")
        
    def start(self) -> bool:
        """
        Start drive monitoring.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.state == MonitoringState.RUNNING:
            self.logger.warning("Drive monitor is already running")
            return True
            
        try:
            self.logger.info("Starting drive monitor")
            
            # Reset state
            self.stop_event.clear()
            self.pause_event.clear()
            self.state = MonitoringState.RUNNING
            self.stats = MonitoringStats(start_time=datetime.now())
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="DriveMonitor",
                daemon=True
            )
            self.monitor_thread.start()
            
            self.logger.info("Drive monitor started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start drive monitor: {e}")
            self.state = MonitoringState.ERROR
            return False
            
    def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop drive monitoring.
        
        Args:
            timeout: Timeout in seconds to wait for thread to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if self.state == MonitoringState.STOPPED:
            self.logger.info("Drive monitor is already stopped")
            return True
            
        try:
            self.logger.info("Stopping drive monitor")
            
            # Signal stop
            self.stop_event.set()
            self.state = MonitoringState.STOPPED
            
            # Wait for thread to finish
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=timeout)
                
                if self.monitor_thread.is_alive():
                    self.logger.warning("Drive monitor thread did not stop within timeout")
                    return False
                    
            self.logger.info("Drive monitor stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping drive monitor: {e}")
            return False
            
    def pause(self) -> None:
        """Pause drive monitoring."""
        if self.state == MonitoringState.RUNNING:
            self.logger.info("Pausing drive monitor")
            self.pause_event.set()
            self.state = MonitoringState.PAUSED
            
    def resume(self) -> None:
        """Resume drive monitoring."""
        if self.state == MonitoringState.PAUSED:
            self.logger.info("Resuming drive monitor")
            self.pause_event.clear()
            self.state = MonitoringState.RUNNING
            
    def get_stats(self) -> MonitoringStats:
        """Get current monitoring statistics."""
        return self.stats
        
    def get_state(self) -> MonitoringState:
        """Get current monitoring state."""
        return self.state
        
    def force_check(self) -> bool:
        """
        Force an immediate drive check.
        
        Returns:
            True if check was successful, False otherwise
        """
        try:
            self.logger.info("Performing forced drive check")
            return self._perform_drive_check()
        except Exception as e:
            self.logger.error(f"Error during forced check: {e}")
            return False
            
    def _monitor_loop(self):
        """Main monitoring loop."""
        self.logger.info("Drive monitoring loop started")
        
        try:
            while not self.stop_event.is_set():
                try:
                    # Check if paused
                    if self.pause_event.is_set():
                        self.stop_event.wait(1)  # Check stop event while paused
                        continue
                        
                    # Perform drive check
                    self._perform_drive_check()
                    
                    # Wait for next check interval
                    self.stop_event.wait(self.check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    self.stats.failed_checks += 1
                    self.stats.consecutive_failures += 1
                    
                    # Wait before retrying
                    self.stop_event.wait(min(self.retry_delay, self.check_interval))
                    
        except Exception as e:
            self.logger.error(f"Fatal error in monitoring loop: {e}")
            self.state = MonitoringState.ERROR
        finally:
            self.logger.info("Drive monitoring loop stopped")
            
    def _perform_drive_check(self) -> bool:
        """
        Perform a single drive check with remount if necessary.
        
        Returns:
            True if drive is healthy, False otherwise
        """
        check_start = datetime.now()
        self.stats.total_checks += 1
        self.stats.last_check_time = check_start
        
        try:
            self.logger.debug("Performing drive status check")
            
            # Get current drive status
            drive_info = self.drive_manager.check_drive_status()
            
            if drive_info and drive_info.is_mounted:
                # Drive is mounted and accessible
                self._handle_drive_healthy(drive_info)
                self.stats.successful_checks += 1
                self.stats.consecutive_failures = 0
                return True
            else:
                # Drive is not mounted or not accessible
                self._handle_drive_unhealthy()
                return False
                
        except Exception as e:
            self.logger.error(f"Error during drive check: {e}")
            self.stats.failed_checks += 1
            self.stats.consecutive_failures += 1
            return False
            
    def _handle_drive_healthy(self, drive_info: DriveInfo):
        """Handle case where drive is healthy."""
        self.logger.debug(f"Drive {drive_info.drive_letter} is healthy")
        
        # Check if this is a recovery from previous failure
        if self.last_known_good_state is None:
            # First successful check or recovery
            if self.stats.failed_checks > 0:
                self.logger.info("Drive recovered from previous failures")
                if self.on_drive_recovered:
                    self.on_drive_recovered(drive_info)
                    
        self.last_known_good_state = drive_info
        
        # Log drive space if available and low
        if drive_info.free_space_bytes is not None:
            free_gb = drive_info.free_space_bytes / (1024**3)
            if free_gb < 1.0:  # Less than 1GB free
                self.logger.warning(f"Drive {drive_info.drive_letter} low on space: {free_gb:.2f} GB free")
                
    def _handle_drive_unhealthy(self):
        """Handle case where drive is not healthy."""
        self.logger.warning("Drive is not mounted or accessible")
        
        # Track failure
        self.stats.failed_checks += 1
        self.stats.consecutive_failures += 1
        self.failure_timestamps.append(datetime.now())
        
        # Clean old failure timestamps (keep last hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.failure_timestamps = [ts for ts in self.failure_timestamps if ts > cutoff]
        
        # Check if we should trigger drive lost callback
        if self.last_known_good_state is not None and self.stats.consecutive_failures == 1:
            self.logger.warning("Drive lost, attempting recovery")
            if self.on_drive_lost:
                self.on_drive_lost()
                
        # Attempt to remount if not too many consecutive failures
        if self.stats.consecutive_failures <= self.max_consecutive_failures:
            self._attempt_remount()
        else:
            self.logger.error(f"Too many consecutive failures ({self.stats.consecutive_failures}), "
                            f"waiting {self.failure_escalation_delay} seconds before retry")
            self.stop_event.wait(self.failure_escalation_delay)
            
    def _attempt_remount(self):
        """Attempt to remount the virtual drive."""
        try:
            self.logger.info("Attempting to remount virtual drive")
            
            self.stats.mount_attempts += 1
            
            # Attempt mount with retry logic
            if self.drive_manager.ensure_drive_mounted():
                self.logger.info("Successfully remounted virtual drive")
                self.stats.successful_mounts += 1
                self.stats.last_mount_time = datetime.now()
                
                # Verify mount with a quick check
                drive_info = self.drive_manager.check_drive_status()
                if drive_info and drive_info.is_mounted:
                    if self.on_mount_success:
                        self.on_mount_success(drive_info)
                    return True
                else:
                    self.logger.error("Mount reported success but verification failed")
                    
            else:
                self.logger.error("Failed to remount virtual drive")
                self.stats.failed_mounts += 1
                
                if self.on_mount_failure:
                    self.on_mount_failure("Mount operation failed")
                    
                # Wait before next attempt
                self.stop_event.wait(self.retry_delay)
                
        except Exception as e:
            self.logger.error(f"Error during remount attempt: {e}")
            self.stats.failed_mounts += 1
            
            if self.on_mount_failure:
                self.on_mount_failure(str(e))
                
        return False
        
    def _should_escalate_failure(self) -> bool:
        """
        Determine if failure should be escalated (e.g., notify admin).
        
        Returns:
            True if failure should be escalated
        """
        # Escalate if too many failures in short time
        recent_failures = len([ts for ts in self.failure_timestamps 
                             if ts > datetime.now() - timedelta(minutes=15)])
        
        if recent_failures >= 5:
            return True
            
        # Escalate if consecutive failures exceed threshold
        if self.stats.consecutive_failures >= self.max_consecutive_failures:
            return True
            
        return False


class DriveHealthChecker:
    """
    Additional health checking for virtual drives.
    
    Provides more detailed health checks beyond basic mount status.
    """
    
    def __init__(self, drive_manager: VirtualDriveManager, 
                 logger: Optional[logging.Logger] = None):
        """Initialize health checker."""
        self.drive_manager = drive_manager
        self.logger = logger or logging.getLogger(__name__)
        
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dictionary with health check results
        """
        results = {
            'timestamp': datetime.now(),
            'overall_health': 'unknown',
            'checks': {}
        }
        
        try:
            # Basic mount check
            drive_info = self.drive_manager.check_drive_status()
            results['checks']['mount_status'] = {
                'status': 'pass' if drive_info and drive_info.is_mounted else 'fail',
                'details': drive_info.__dict__ if drive_info else None
            }
            
            if drive_info and drive_info.is_mounted:
                # Disk space check
                results['checks']['disk_space'] = self._check_disk_space(drive_info)
                
                # File system access check
                results['checks']['file_access'] = self._check_file_access(drive_info.drive_letter)
                
                # Performance check
                results['checks']['performance'] = self._check_performance(drive_info.drive_letter)
                
            # Determine overall health
            failed_checks = [name for name, check in results['checks'].items() 
                           if check['status'] == 'fail']
            
            if not failed_checks:
                results['overall_health'] = 'healthy'
            elif len(failed_checks) == 1 and 'performance' in failed_checks:
                results['overall_health'] = 'degraded'
            else:
                results['overall_health'] = 'unhealthy'
                
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            results['overall_health'] = 'error'
            results['error'] = str(e)
            
        return results
        
    def _check_disk_space(self, drive_info: DriveInfo) -> Dict[str, Any]:
        """Check disk space availability."""
        try:
            if drive_info.free_space_bytes is None:
                return {'status': 'unknown', 'details': 'Space information not available'}
                
            free_gb = drive_info.free_space_bytes / (1024**3)
            
            if free_gb < 0.1:  # Less than 100MB
                return {'status': 'fail', 'details': f'Critical: Only {free_gb:.2f} GB free'}
            elif free_gb < 1.0:  # Less than 1GB
                return {'status': 'warning', 'details': f'Low space: {free_gb:.2f} GB free'}
            else:
                return {'status': 'pass', 'details': f'{free_gb:.2f} GB free'}
                
        except Exception as e:
            return {'status': 'error', 'details': str(e)}
            
    def _check_file_access(self, drive_letter: str) -> Dict[str, Any]:
        """Check file system access."""
        try:
            from pathlib import Path
            import tempfile
            
            drive_path = Path(drive_letter + '\\')
            
            # Try to create a temporary file
            test_file = drive_path / 'health_check_temp.txt'
            
            # Write test
            test_file.write_text('health check')
            
            # Read test
            content = test_file.read_text()
            
            # Cleanup
            test_file.unlink()
            
            if content == 'health check':
                return {'status': 'pass', 'details': 'Read/write access confirmed'}
            else:
                return {'status': 'fail', 'details': 'File content mismatch'}
                
        except PermissionError:
            return {'status': 'fail', 'details': 'Permission denied'}
        except Exception as e:
            return {'status': 'fail', 'details': str(e)}
            
    def _check_performance(self, drive_letter: str) -> Dict[str, Any]:
        """Check drive performance."""
        try:
            from pathlib import Path
            import time
            
            drive_path = Path(drive_letter + '\\')
            
            # Simple performance test - list directory contents
            start_time = time.time()
            list(drive_path.iterdir())
            elapsed = time.time() - start_time
            
            if elapsed > 5.0:  # More than 5 seconds to list directory
                return {'status': 'fail', 'details': f'Slow response: {elapsed:.2f}s'}
            elif elapsed > 2.0:  # More than 2 seconds
                return {'status': 'warning', 'details': f'Degraded performance: {elapsed:.2f}s'}
            else:
                return {'status': 'pass', 'details': f'Good performance: {elapsed:.2f}s'}
                
        except Exception as e:
            return {'status': 'error', 'details': str(e)}