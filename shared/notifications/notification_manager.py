"""
Cross-platform notification manager for EFIS Data Manager.
"""

import platform
import logging
from typing import Optional, List
from .notification_types import Notification, NotificationPreferences, NotificationType, NotificationPriority
from .email_notifier import EmailNotifier


class NotificationManager:
    """Cross-platform notification manager."""
    
    def __init__(self, preferences: Optional[NotificationPreferences] = None):
        """Initialize notification manager."""
        self.preferences = preferences or NotificationPreferences()
        self.logger = logging.getLogger(__name__)
        self.email_notifier = EmailNotifier() if self.preferences.enable_email else None
        self._platform = platform.system().lower()
        
    def notify(self, notification: Notification) -> bool:
        """Send notification through appropriate channels."""
        success = True
        
        # Desktop notification
        if self.preferences.should_notify_desktop(notification):
            try:
                success &= self._send_desktop_notification(notification)
            except Exception as e:
                self.logger.error(f"Failed to send desktop notification: {e}")
                success = False
        
        # Email notification
        if self.preferences.should_notify_email(notification) and self.email_notifier:
            try:
                success &= self.email_notifier.send_notification(notification)
            except Exception as e:
                self.logger.error(f"Failed to send email notification: {e}")
                success = False
        
        return success
    
    def _send_desktop_notification(self, notification: Notification) -> bool:
        """Send platform-specific desktop notification."""
        if self._platform == "darwin":
            return self._send_macos_notification(notification)
        elif self._platform == "windows":
            return self._send_windows_notification(notification)
        else:
            self.logger.warning(f"Desktop notifications not supported on {self._platform}")
            return False
    
    def _send_macos_notification(self, notification: Notification) -> bool:
        """Send macOS notification using osascript."""
        try:
            import subprocess
            
            # Map notification types to macOS sounds
            sound_map = {
                NotificationType.SUCCESS: "Glass",
                NotificationType.INFO: "Blow",
                NotificationType.WARNING: "Sosumi",
                NotificationType.ERROR: "Basso",
                NotificationType.CRITICAL: "Funk"
            }
            
            sound = sound_map.get(notification.notification_type, "Blow")
            
            # Build AppleScript command
            script = f'''
            display notification "{notification.message}" ¬
                with title "{notification.title}" ¬
                sound name "{sound}"
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.debug(f"macOS notification sent: {notification.title}")
                return True
            else:
                self.logger.error(f"macOS notification failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send macOS notification: {e}")
            return False
    
    def _send_windows_notification(self, notification: Notification) -> bool:
        """Send Windows toast notification."""
        try:
            # Try using win10toast if available
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                
                # Map notification types to icons
                icon_map = {
                    NotificationType.SUCCESS: None,  # Default icon
                    NotificationType.INFO: None,
                    NotificationType.WARNING: None,
                    NotificationType.ERROR: None,
                    NotificationType.CRITICAL: None
                }
                
                duration = 10 if notification.priority.value >= NotificationPriority.HIGH.value else 5
                
                toaster.show_toast(
                    title=notification.title,
                    msg=notification.message,
                    duration=duration,
                    threaded=True
                )
                
                self.logger.debug(f"Windows toast notification sent: {notification.title}")
                return True
                
            except ImportError:
                # Fallback to PowerShell if win10toast not available
                return self._send_windows_powershell_notification(notification)
                
        except Exception as e:
            self.logger.error(f"Failed to send Windows notification: {e}")
            return False
    
    def _send_windows_powershell_notification(self, notification: Notification) -> bool:
        """Send Windows notification using PowerShell."""
        try:
            import subprocess
            
            # PowerShell script for toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastGeneric">
                        <text>{notification.title}</text>
                        <text>{notification.message}</text>
                    </binding>
                </visual>
            </toast>
            "@
            
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("EFIS Data Manager").Show($toast)
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.debug(f"Windows PowerShell notification sent: {notification.title}")
                return True
            else:
                self.logger.error(f"Windows PowerShell notification failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Windows PowerShell notification: {e}")
            return False
    
    def update_preferences(self, preferences: NotificationPreferences) -> None:
        """Update notification preferences."""
        self.preferences = preferences
        if preferences.enable_email and not self.email_notifier:
            self.email_notifier = EmailNotifier()
        elif not preferences.enable_email:
            self.email_notifier = None
    
    # Convenience methods for common notification types
    def notify_success(self, title: str, message: str, component: str = "system", operation: str = None) -> bool:
        """Send success notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.SUCCESS,
            priority=NotificationPriority.NORMAL,
            component=component,
            operation=operation
        )
        return self.notify(notification)
    
    def notify_error(self, title: str, message: str, component: str = "system", operation: str = None) -> bool:
        """Send error notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            component=component,
            operation=operation
        )
        return self.notify(notification)
    
    def notify_warning(self, title: str, message: str, component: str = "system", operation: str = None) -> bool:
        """Send warning notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            priority=NotificationPriority.NORMAL,
            component=component,
            operation=operation
        )
        return self.notify(notification)
    
    def notify_info(self, title: str, message: str, component: str = "system", operation: str = None) -> bool:
        """Send info notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            component=component,
            operation=operation
        )
        return self.notify(notification)
    
    def notify_critical(self, title: str, message: str, component: str = "system", operation: str = None) -> bool:
        """Send critical notification."""
        notification = Notification(
            title=title,
            message=message,
            notification_type=NotificationType.CRITICAL,
            priority=NotificationPriority.URGENT,
            component=component,
            operation=operation
        )
        return self.notify(notification)