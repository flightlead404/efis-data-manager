"""
Cross-platform notification system for EFIS Data Manager.
"""

from .notification_manager import NotificationManager
from .notification_types import NotificationType, NotificationPriority, Notification, NotificationPreferences
from .email_notifier import EmailNotifier

__all__ = [
    'NotificationManager',
    'NotificationType', 
    'NotificationPriority',
    'Notification',
    'NotificationPreferences',
    'EmailNotifier'
]