"""
Sync scheduling and retry logic for EFIS Data Manager.
Manages periodic synchronization with exponential backoff retry logic.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sync_engine import SyncEngine, SyncResult
from network_manager import NetworkManager, ConnectionStatus


class SyncState(Enum):
    """Synchronization scheduler states."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    SYNCING = "syncing"
    RETRYING = "retrying"
    ERROR = "error"


@dataclass
class SyncStats:
    """Statistics for synchronization operations."""
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    total_files_transferred: int = 0
    total_bytes_transferred: int = 0
    last_sync_time: Optional[datetime] = None
    last_successful_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate sync success rate as percentage."""
        if self.total_syncs == 0:
            return 0.0
        return (self.successful_syncs / self.total_syncs) * 100
        
    @property
    def average_transfer_size_mb(self) -> float:
        """Calculate average transfer size in MB."""
        if self.successful_syncs == 0:
            return 0.0
        return (self.total_bytes_transferred / (1024 * 1024)) / self.successful_syncs


class SyncScheduler:
    """
    Manages periodic chart synchronization with retry logic.
    
    Provides configurable sync intervals, exponential backoff for failures,
    and graceful handling of extended offline periods.
    """
    
    def __init__(self, sync_engine: SyncEngine, network_manager: NetworkManager,
                 config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize sync scheduler.
        
        Args:
            sync_engine: SyncEngine for performing synchronization
            network_manager: NetworkManager for connectivity checking
            config: Configuration dictionary
            logger: Logger instance
        """
        self.sync_engine = sync_engine
        self.network_manager = network_manager
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Scheduling configuration
        self.sync_interval = config.get('interval', 1800)  # 30 minutes default
        self.retry_attempts = config.get('retryAttempts', 3)
        self.retry_base_delay = config.get('retryDelay', 300)  # 5 minutes base delay
        self.max_retry_delay = config.get('maxRetryDelay', 3600)  # 1 hour max delay
        self.offline_check_interval = config.get('offlineCheckInterval', 300)  # 5 minutes
        
        # State management
        self.state = SyncState.STOPPED
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.scheduler_thread = None
        
        # Statistics and tracking
        self.stats = SyncStats()
        self.last_sync_attempt = None
        self.current_retry_count = 0
        self.next_sync_time = None
        
        # Callbacks for events
        self.on_sync_start: Optional[Callable[[], None]] = None
        self.on_sync_success: Optional[Callable[[SyncResult], None]] = None
        self.on_sync_failure: Optional[Callable[[str], None]] = None
        self.on_sync_retry: Optional[Callable[[int, int], None]] = None  # (attempt, max_attempts)
        self.on_network_offline: Optional[Callable[[], None]] = None
        self.on_network_online: Optional[Callable[[], None]] = None
        
        self.logger.info(f"Sync scheduler initialized (interval: {self.sync_interval}s, "
                        f"retry attempts: {self.retry_attempts})")
        
    def start(self) -> bool:
        """
        Start the sync scheduler.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.state == SyncState.RUNNING:
            self.logger.warning("Sync scheduler is already running")
            return True
            
        try:
            self.logger.info("Starting sync scheduler")
            
            # Reset state
            self.stop_event.clear()
            self.pause_event.clear()
            self.state = SyncState.RUNNING
            self.current_retry_count = 0
            self.next_sync_time = datetime.now() + timedelta(seconds=60)  # First sync in 1 minute
            
            # Start scheduler thread
            self.scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                name="SyncScheduler",
                daemon=True
            )
            self.scheduler_thread.start()
            
            self.logger.info("Sync scheduler started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start sync scheduler: {e}")
            self.state = SyncState.ERROR
            return False
            
    def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the sync scheduler.
        
        Args:
            timeout: Timeout in seconds to wait for thread to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if self.state == SyncState.STOPPED:
            self.logger.info("Sync scheduler is already stopped")
            return True
            
        try:
            self.logger.info("Stopping sync scheduler")
            
            # Signal stop
            self.stop_event.set()
            self.state = SyncState.STOPPED
            
            # Wait for thread to finish
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=timeout)
                
                if self.scheduler_thread.is_alive():
                    self.logger.warning("Sync scheduler thread did not stop within timeout")
                    return False
                    
            self.logger.info("Sync scheduler stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping sync scheduler: {e}")
            return False
            
    def pause(self) -> None:
        """Pause sync scheduling (current sync will complete)."""
        if self.state == SyncState.RUNNING:
            self.logger.info("Pausing sync scheduler")
            self.pause_event.set()
            self.state = SyncState.PAUSED
            
    def resume(self) -> None:
        """Resume sync scheduling."""
        if self.state == SyncState.PAUSED:
            self.logger.info("Resuming sync scheduler")
            self.pause_event.clear()
            self.state = SyncState.RUNNING
            
    def force_sync(self) -> SyncResult:
        """
        Force an immediate synchronization.
        
        Returns:
            SyncResult from the synchronization attempt
        """
        self.logger.info("Forcing immediate synchronization")
        return self._perform_sync()
        
    def get_stats(self) -> SyncStats:
        """Get current synchronization statistics."""
        return self.stats
        
    def get_state(self) -> SyncState:
        """Get current scheduler state."""
        return self.state
        
    def get_next_sync_time(self) -> Optional[datetime]:
        """Get the scheduled time for the next sync."""
        return self.next_sync_time
        
    def get_time_until_next_sync(self) -> Optional[timedelta]:
        """Get time remaining until next sync."""
        if self.next_sync_time:
            return max(timedelta(0), self.next_sync_time - datetime.now())
        return None
        
    def _scheduler_loop(self):
        """Main scheduler loop."""
        self.logger.info("Sync scheduler loop started")
        
        try:
            while not self.stop_event.is_set():
                try:
                    # Check if paused
                    if self.pause_event.is_set():
                        self.stop_event.wait(1)  # Check stop event while paused
                        continue
                        
                    # Check if it's time for a sync
                    now = datetime.now()
                    if self.next_sync_time and now >= self.next_sync_time:
                        self._handle_scheduled_sync()
                        
                    # Sleep for a short interval
                    self.stop_event.wait(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in scheduler loop: {e}")
                    self.state = SyncState.ERROR
                    self.stop_event.wait(60)  # Wait before retrying
                    
        except Exception as e:
            self.logger.error(f"Fatal error in scheduler loop: {e}")
            self.state = SyncState.ERROR
        finally:
            self.logger.info("Sync scheduler loop stopped")
            
    def _handle_scheduled_sync(self):
        """Handle a scheduled synchronization."""
        # Check network connectivity first
        if not self._check_network_connectivity():
            self.logger.warning("Network offline, scheduling connectivity check")
            self._schedule_offline_check()
            return
            
        # Perform synchronization
        sync_result = self._perform_sync_with_retry()
        
        # Schedule next sync based on result
        if sync_result.success:
            self._schedule_next_sync()
            self.current_retry_count = 0
        else:
            self._handle_sync_failure()
            
    def _perform_sync_with_retry(self) -> SyncResult:
        """
        Perform synchronization with retry logic.
        
        Returns:
            Final SyncResult after all retry attempts
        """
        last_result = None
        
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.info(f"Sync attempt {attempt}/{self.retry_attempts}")
                
                # Notify retry callback
                if attempt > 1 and self.on_sync_retry:
                    self.on_sync_retry(attempt, self.retry_attempts)
                    
                # Perform sync
                result = self._perform_sync()
                
                if result.success:
                    self.logger.info(f"Sync successful on attempt {attempt}")
                    return result
                else:
                    self.logger.warning(f"Sync failed on attempt {attempt}: {result.error_message}")
                    last_result = result
                    
                    # Wait before retry (except on last attempt)
                    if attempt < self.retry_attempts:
                        retry_delay = self._calculate_retry_delay(attempt)
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        self.stop_event.wait(retry_delay)
                        
                        # Check if we should stop
                        if self.stop_event.is_set():
                            break
                            
            except Exception as e:
                self.logger.error(f"Sync attempt {attempt} error: {e}")
                last_result = SyncResult(
                    success=False,
                    files_transferred=0,
                    bytes_transferred=0,
                    files_skipped=0,
                    files_failed=0,
                    duration_seconds=0,
                    error_message=str(e)
                )
                
        # All attempts failed
        self.logger.error(f"All {self.retry_attempts} sync attempts failed")
        return last_result or SyncResult(
            success=False,
            files_transferred=0,
            bytes_transferred=0,
            files_skipped=0,
            files_failed=0,
            duration_seconds=0,
            error_message="All retry attempts failed"
        )
        
    def _perform_sync(self) -> SyncResult:
        """
        Perform a single synchronization attempt.
        
        Returns:
            SyncResult from the synchronization
        """
        self.state = SyncState.SYNCING
        self.last_sync_attempt = datetime.now()
        
        try:
            # Notify sync start
            if self.on_sync_start:
                self.on_sync_start()
                
            # Perform synchronization
            result = self.sync_engine.sync_charts()
            
            # Update statistics
            self._update_stats(result)
            
            # Notify callbacks
            if result.success:
                self.logger.info(f"Sync completed: {result.files_transferred} files, "
                               f"{result.bytes_transferred/(1024*1024):.1f} MB")
                if self.on_sync_success:
                    self.on_sync_success(result)
            else:
                self.logger.error(f"Sync failed: {result.error_message}")
                if self.on_sync_failure:
                    self.on_sync_failure(result.error_message or "Unknown error")
                    
            return result
            
        except Exception as e:
            error_msg = f"Sync error: {e}"
            self.logger.error(error_msg)
            
            result = SyncResult(
                success=False,
                files_transferred=0,
                bytes_transferred=0,
                files_skipped=0,
                files_failed=0,
                duration_seconds=0,
                error_message=str(e)
            )
            
            self._update_stats(result)
            
            if self.on_sync_failure:
                self.on_sync_failure(str(e))
                
            return result
        finally:
            self.state = SyncState.RUNNING
            
    def _check_network_connectivity(self) -> bool:
        """
        Check if network connectivity to MacBook is available.
        
        Returns:
            True if MacBook is reachable, False otherwise
        """
        try:
            network_info = self.network_manager.check_connectivity()
            return network_info.status == ConnectionStatus.CONNECTED
        except Exception as e:
            self.logger.debug(f"Network connectivity check error: {e}")
            return False
            
    def _schedule_next_sync(self):
        """Schedule the next regular synchronization."""
        self.next_sync_time = datetime.now() + timedelta(seconds=self.sync_interval)
        self.logger.debug(f"Next sync scheduled for: {self.next_sync_time}")
        
    def _schedule_offline_check(self):
        """Schedule a connectivity check when network is offline."""
        self.next_sync_time = datetime.now() + timedelta(seconds=self.offline_check_interval)
        self.logger.debug(f"Next connectivity check scheduled for: {self.next_sync_time}")
        
    def _handle_sync_failure(self):
        """Handle synchronization failure and schedule retry or next attempt."""
        self.current_retry_count += 1
        
        if self.current_retry_count < self.retry_attempts:
            # Schedule retry with exponential backoff
            retry_delay = self._calculate_retry_delay(self.current_retry_count)
            self.next_sync_time = datetime.now() + timedelta(seconds=retry_delay)
            self.state = SyncState.RETRYING
            self.logger.info(f"Scheduling retry {self.current_retry_count}/{self.retry_attempts} "
                           f"in {retry_delay} seconds")
        else:
            # All retries exhausted, schedule next regular sync
            self._schedule_next_sync()
            self.current_retry_count = 0
            self.logger.warning("All retry attempts exhausted, scheduling next regular sync")
            
    def _calculate_retry_delay(self, attempt: int) -> int:
        """
        Calculate retry delay with exponential backoff.
        
        Args:
            attempt: Current retry attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ (attempt - 1))
        delay = self.retry_base_delay * (2 ** (attempt - 1))
        
        # Cap at maximum delay
        delay = min(delay, self.max_retry_delay)
        
        return delay
        
    def _update_stats(self, result: SyncResult):
        """Update synchronization statistics."""
        self.stats.total_syncs += 1
        self.stats.last_sync_time = datetime.now()
        
        if result.success:
            self.stats.successful_syncs += 1
            self.stats.total_files_transferred += result.files_transferred
            self.stats.total_bytes_transferred += result.bytes_transferred
            self.stats.last_successful_sync = self.stats.last_sync_time
            self.stats.consecutive_failures = 0
            self.stats.last_error = None
        else:
            self.stats.failed_syncs += 1
            self.stats.consecutive_failures += 1
            self.stats.last_error = result.error_message


def create_sync_scheduler(sync_engine: SyncEngine, network_manager: NetworkManager,
                         config: Dict[str, Any], logger: Optional[logging.Logger] = None) -> SyncScheduler:
    """
    Factory function to create a configured SyncScheduler.
    
    Args:
        sync_engine: SyncEngine instance
        network_manager: NetworkManager instance
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Configured SyncScheduler instance
    """
    sync_config = config.get('sync', {})
    
    # Map configuration to scheduler settings
    scheduler_config = {
        'interval': sync_config.get('interval', 1800),  # 30 minutes
        'retryAttempts': sync_config.get('retryAttempts', 3),
        'retryDelay': sync_config.get('retryDelay', 300),  # 5 minutes
        'maxRetryDelay': sync_config.get('maxRetryDelay', 3600),  # 1 hour
        'offlineCheckInterval': sync_config.get('offlineCheckInterval', 300)  # 5 minutes
    }
    
    return SyncScheduler(sync_engine, network_manager, scheduler_config, logger)