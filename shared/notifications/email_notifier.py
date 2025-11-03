"""
Email notification system for EFIS Data Manager.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
from .notification_types import Notification, NotificationType


class EmailNotifier:
    """Email notification handler."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize email notifier."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Default SMTP settings (can be overridden in config)
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.from_email = self.config.get('from_email', self.username)
        self.to_email = self.config.get('to_email')
        
    def send_notification(self, notification: Notification) -> bool:
        """Send email notification."""
        if not self._validate_config():
            self.logger.error("Email configuration incomplete")
            return False
        
        try:
            # Create message
            msg = self._create_message(notification)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent: {notification.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _validate_config(self) -> bool:
        """Validate email configuration."""
        required_fields = ['username', 'password', 'to_email']
        return all(self.config.get(field) for field in required_fields)
    
    def _create_message(self, notification: Notification) -> MIMEMultipart:
        """Create email message from notification."""
        msg = MIMEMultipart('alternative')
        
        # Set headers
        msg['Subject'] = f"[EFIS Data Manager] {notification.title}"
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Date'] = notification.timestamp.strftime('%a, %d %b %Y %H:%M:%S %z')
        
        # Create text content
        text_content = self._create_text_content(notification)
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Create HTML content
        html_content = self._create_html_content(notification)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        return msg
    
    def _create_text_content(self, notification: Notification) -> str:
        """Create plain text email content."""
        content = f"""
EFIS Data Manager Notification

Title: {notification.title}
Type: {notification.notification_type.value.upper()}
Priority: {notification.priority.name}
Component: {notification.component}
Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{notification.message}
"""
        
        if notification.operation:
            content += f"\nOperation: {notification.operation}"
        
        if notification.details:
            content += "\n\nDetails:"
            for key, value in notification.details.items():
                content += f"\n  {key}: {value}"
        
        content += "\n\n---\nThis is an automated message from EFIS Data Manager."
        
        return content
    
    def _create_html_content(self, notification: Notification) -> str:
        """Create HTML email content."""
        # Color mapping for notification types
        color_map = {
            NotificationType.SUCCESS: "#28a745",
            NotificationType.INFO: "#17a2b8",
            NotificationType.WARNING: "#ffc107",
            NotificationType.ERROR: "#dc3545",
            NotificationType.CRITICAL: "#6f42c1"
        }
        
        color = color_map.get(notification.notification_type, "#6c757d")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>EFIS Data Manager Notification</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">EFIS Data Manager</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">{notification.notification_type.value.upper()} Notification</p>
                </div>
                
                <div style="padding: 20px;">
                    <h2 style="color: #333; margin-top: 0;">{notification.title}</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0;">
                        <p style="margin: 0; color: #495057;">{notification.message}</p>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">Time:</td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; color: #6c757d;">{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">Component:</td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; color: #6c757d;">{notification.component}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">Priority:</td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; color: #6c757d;">{notification.priority.name}</td>
                        </tr>
        """
        
        if notification.operation:
            html += f"""
                        <tr>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; font-weight: bold; color: #495057;">Operation:</td>
                            <td style="padding: 8px 0; border-bottom: 1px solid #dee2e6; color: #6c757d;">{notification.operation}</td>
                        </tr>
            """
        
        html += """
                    </table>
        """
        
        if notification.details:
            html += """
                    <h3 style="color: #333; margin-top: 20px;">Details:</h3>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px;">
            """
            for key, value in notification.details.items():
                html += f"<p style='margin: 5px 0; color: #495057;'><strong>{key}:</strong> {value}</p>"
            html += "</div>"
        
        html += """
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 12px;">
                    This is an automated message from EFIS Data Manager.
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update email configuration."""
        self.config.update(config)
        self.smtp_server = self.config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.from_email = self.config.get('from_email', self.username)
        self.to_email = self.config.get('to_email')
    
    def test_connection(self) -> bool:
        """Test email connection and authentication."""
        if not self._validate_config():
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception as e:
            self.logger.error(f"Email connection test failed: {e}")
            return False