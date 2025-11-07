"""
Windows notification service for EFIS Data Manager.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add shared modules to path
shared_path = Path(__file__).parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from notifications import NotificationManager, NotificationPreferences


class WindowsNotificationService:
    """Windows-specific notification service."""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize Windows notification service."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize notification manager
        self._initialize_notifications()
    
    def _initialize_notifications(self):
        """Initialize the notification system."""
        try:
            # Create notification preferences from config
            notification_config = self.config.get('notifications', {})
            
            preferences = NotificationPreferences(
                enable_desktop=notification_config.get('enable_desktop', True),
                enable_email=notification_config.get('enable_email', False),
                email_address=notification_config.get('email_address'),
                min_priority_desktop=notification_config.get('min_priority_desktop', 2),
                min_priority_email=notification_config.get('min_priority_email', 3),
                filter_types=notification_config.get('filter_types', []),
                quiet_hours_start=notification_config.get('quiet_hours_start'),
                quiet_hours_end=notification_config.get('quiet_hours_end')
            )
            
            self.notification_manager = NotificationManager(preferences)
            self.logger.info("Windows notification system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification system: {e}")
            self.notification_manager = None
    
    def notify_sync_started(self, target: str) -> bool:
        """Notify that sync operation has started."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_info(
            "Sync Started",
            f"Starting file synchronization to {target}",
            component="sync_engine",
            operation="sync_start"
        )
    
    def notify_sync_completed(self, files_transferred: int, bytes_transferred: int, duration: float) -> bool:
        """Notify that sync operation completed successfully."""
        if not self.notification_manager:
            return False
        
        size_mb = bytes_transferred / (1024 * 1024)
        message = f"Transferred {files_transferred} files ({size_mb:.1f} MB) in {duration:.1f} seconds"
        
        return self.notification_manager.notify_success(
            "Sync Completed",
            message,
            component="sync_engine",
            operation="sync_complete"
        )
    
    def notify_sync_failed(self, error: str) -> bool:
        """Notify that sync operation failed."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_error(
            "Sync Failed",
            f"File synchronization failed: {error}",
            component="sync_engine",
            operation="sync_error"
        )
    
    def notify_drive_mounted(self, drive_letter: str) -> bool:
        """Notify that virtual drive was mounted."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_success(
            "Virtual Drive Mounted",
            f"Virtual USB drive mounted successfully at {drive_letter}:",
            component="drive_manager",
            operation="mount"
        )
    
    def notify_drive_mount_failed(self, error: str) -> bool:
        """Notify that virtual drive mount failed."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_error(
            "Drive Mount Failed",
            f"Failed to mount virtual USB drive: {error}",
            component="drive_manager",
            operation="mount_error"
        )
    
    def notify_network_error(self, target: str, error: str) -> bool:
        """Notify about network connectivity issues."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_warning(
            "Network Connection Issue",
            f"Cannot connect to {target}: {error}",
            component="network_manager",
            operation="connectivity_check"
        )
    
    def notify_service_started(self) -> bool:
        """Notify that Windows service has started."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_success(
            "EFIS Data Manager Started",
            "Windows service has started successfully",
            component="windows_service",
            operation="startup"
        )
    
    def notify_service_stopped(self) -> bool:
        """Notify that Windows service has stopped."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_info(
            "EFIS Data Manager Stopped",
            "Windows service has been stopped",
            component="windows_service",
            operation="shutdown"
        )
    
    def notify_critical_error(self, error: str) -> bool:
        """Notify about critical system errors."""
        if not self.notification_manager:
            return False
        
        return self.notification_manager.notify_critical(
            "Critical System Error",
            f"A critical error occurred: {error}",
            component="windows_service",
            operation="critical_error"
        )
    
    def update_preferences(self, config: dict) -> None:
        """Update notification preferences."""
        self.config = config
        if self.notification_manager:
            notification_config = config.get('notifications', {})
            
            preferences = NotificationPreferences(
                enable_desktop=notification_config.get('enable_desktop', True),
                enable_email=notification_config.get('enable_email', False),
                email_address=notification_config.get('email_address'),
                min_priority_desktop=notification_config.get('min_priority_desktop', 2),
                min_priority_email=notification_config.get('min_priority_email', 3),
                filter_types=notification_config.get('filter_types', []),
                quiet_hours_start=notification_config.get('quiet_hours_start'),
                quiet_hours_end=notification_config.get('quiet_hours_end')
            )
            
            self.notification_manager.update_preferences(preferences)