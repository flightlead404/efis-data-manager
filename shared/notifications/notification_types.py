"""
Notification types and data structures for EFIS Data Manager.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Notification:
    """Notification data structure."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    component: str = "system"
    operation: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            'title': self.title,
            'message': self.message,
            'type': self.notification_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'operation': self.operation,
            'details': self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary."""
        return cls(
            title=data['title'],
            message=data['message'],
            notification_type=NotificationType(data.get('type', 'info')),
            priority=NotificationPriority(data.get('priority', 2)),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            component=data.get('component', 'system'),
            operation=data.get('operation'),
            details=data.get('details')
        )


@dataclass
class NotificationPreferences:
    """User notification preferences."""
    enable_desktop: bool = True
    enable_email: bool = False
    email_address: Optional[str] = None
    min_priority_desktop: NotificationPriority = NotificationPriority.NORMAL
    min_priority_email: NotificationPriority = NotificationPriority.HIGH
    filter_types: list = field(default_factory=list)  # Types to exclude
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    
    def should_notify_desktop(self, notification: Notification) -> bool:
        """Check if desktop notification should be sent."""
        if not self.enable_desktop:
            return False
        if notification.priority.value < self.min_priority_desktop.value:
            return False
        if notification.notification_type in self.filter_types:
            return False
        return not self._is_quiet_hours()
    
    def should_notify_email(self, notification: Notification) -> bool:
        """Check if email notification should be sent."""
        if not self.enable_email or not self.email_address:
            return False
        if notification.priority.value < self.min_priority_email.value:
            return False
        if notification.notification_type in self.filter_types:
            return False
        return True
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = datetime.now().time()
        start = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end