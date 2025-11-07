"""
Main daemon process for macOS EFIS Data Manager.
"""

import os
import sys
import signal
import time
import threading
import atexit
from pathlib import Path
from typing import Optional
import logging

# Add directories to path for imports when run as script
install_dir = Path(__file__).parent

# Import local modules using importlib to avoid conflicts with shared/config
import importlib.util
spec = importlib.util.spec_from_file_location("local_config", install_dir / "config.py")
local_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_config)
ConfigManager = local_config.ConfigManager
MacOSConfig = local_config.MacOSConfig

spec = importlib.util.spec_from_file_location("logging_config", install_dir / "logging_config.py")
logging_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logging_config_module)
setup_daemon_logging = logging_config_module.setup_daemon_logging

# Add shared directory for shared modules
sys.path.insert(0, str(install_dir / "shared"))
from notifications import NotificationManager, NotificationPreferences


class EFISDaemon:
    """Main daemon class for EFIS Data Manager on macOS."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config: Optional[MacOSConfig] = None
        self.logger: Optional[logging.Logger] = None
        self.running = False
        self.pid_file: Optional[str] = None
        
        # Notification system
        self.notification_manager: Optional[NotificationManager] = None
        
        # Threading
        self._stop_event = threading.Event()
        self._threads = []
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        if self.logger:
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def _create_pid_file(self):
        """Create PID file for daemon process."""
        try:
            pid = os.getpid()
            pid_dir = os.path.dirname(self.config.pid_file)
            Path(pid_dir).mkdir(parents=True, exist_ok=True)
            
            with open(self.config.pid_file, 'w') as f:
                f.write(str(pid))
            
            self.pid_file = self.config.pid_file
            self.logger.info(f"Created PID file: {self.pid_file} (PID: {pid})")
            
        except Exception as e:
            self.logger.error(f"Failed to create PID file: {e}")
    
    def _remove_pid_file(self):
        """Remove PID file."""
        if self.pid_file and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                self.logger.info(f"Removed PID file: {self.pid_file}")
            except Exception as e:
                self.logger.error(f"Failed to remove PID file: {e}")
    
    def _check_existing_process(self) -> bool:
        """Check if another daemon process is already running."""
        if not os.path.exists(self.config.pid_file):
            return False
        
        try:
            with open(self.config.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                os.remove(self.config.pid_file)
                return False
                
        except (ValueError, FileNotFoundError):
            # Invalid or missing PID file
            return False
    
    def initialize(self) -> bool:
        """Initialize the daemon."""
        try:
            # Load configuration
            self.config = self.config_manager.load_config()
            
            # Set up logging
            logging_manager = setup_daemon_logging(
                self.config.log_file, 
                self.config.log_level
            )
            self.logger = logging_manager.get_logger(__name__)
            
            self.logger.info("EFIS Data Manager daemon initializing...")
            
            # Check for existing process
            if self._check_existing_process():
                self.logger.error("Another daemon process is already running")
                return False
            
            # Create PID file
            self._create_pid_file()
            
            # Initialize notification system
            self._initialize_notifications()
            
            self.logger.info("Daemon initialization complete")
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize daemon: {e}")
            else:
                print(f"Failed to initialize daemon: {e}", file=sys.stderr)
            return False
    
    def start(self):
        """Start the daemon process."""
        if not self.initialize():
            sys.exit(1)
        
        self.logger.info("Starting EFIS Data Manager daemon...")
        self.running = True
        
        try:
            # Start main daemon loop
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Daemon error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the daemon process."""
        if not self.running:
            return
        
        if self.logger:
            self.logger.info("Stopping daemon...")
        
        self.running = False
        self._stop_event.set()
        
        # Wait for threads to finish
        for thread in self._threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        self.cleanup()
        
        if self.logger:
            self.logger.info("Daemon stopped")
    
    def cleanup(self):
        """Clean up daemon resources."""
        self._remove_pid_file()
    
    def _initialize_notifications(self):
        """Initialize the notification system."""
        try:
            # Create notification preferences from config
            notification_config = getattr(self.config, 'notifications', {})
            
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
            
            # Send startup notification
            self.notification_manager.notify_success(
                "EFIS Data Manager Started",
                "macOS daemon has started successfully",
                component="daemon",
                operation="startup"
            )
            
            self.logger.info("Notification system initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize notification system: {e}")
            self.notification_manager = None
    
    def _main_loop(self):
        """Main daemon event loop."""
        self.logger.info("Daemon main loop started")
        
        # Initialize GRT management components
        try:
            from grt_scraper import GRTWebScraper
            from download_manager import DownloadManager
            
            # Initialize scraper and download manager
            self.grt_scraper = GRTWebScraper()
            self.download_manager = DownloadManager(self.config)
            
            self.logger.info("GRT management components initialized")
            
        except ImportError as e:
            self.logger.warning(f"GRT management components not available: {e}")
            self.grt_scraper = None
            self.download_manager = None
        
        # Initialize USB drive processor
        try:
            from usb_drive_processor import USBDriveProcessor
            
            self.usb_processor = USBDriveProcessor(self.config)
            
            # Start USB monitoring in a separate thread
            usb_thread = threading.Thread(
                target=self.usb_processor.start_monitoring,
                name="USBMonitor",
                daemon=True
            )
            usb_thread.start()
            self._threads.append(usb_thread)
            
            self.logger.info("USB drive monitoring started")
            
        except ImportError as e:
            self.logger.warning(f"USB drive processor not available: {e}")
            self.usb_processor = None
        
        # Main daemon loop
        while self.running and not self._stop_event.is_set():
            try:
                # Basic health check
                self.logger.debug("Daemon heartbeat")
                
                # TODO: Add scheduled GRT update checks here
                # This will be implemented in future tasks
                
                # Wait for stop event or timeout
                if self._stop_event.wait(timeout=self.config.check_interval):
                    break
                    
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Brief pause before continuing
    
    def status(self) -> dict:
        """Get daemon status information."""
        status_info = {
            'running': self.running,
            'pid': os.getpid() if self.running else None,
            'config_file': self.config_manager.config_path,
            'log_file': self.config.log_file if self.config else None,
            'pid_file': self.config.pid_file if self.config else None
        }
        
        return status_info


def main():
    """Main entry point for the daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description='EFIS Data Manager macOS Daemon')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run as daemon')
    parser.add_argument('--stop', action='store_true', help='Stop running daemon')
    parser.add_argument('--status', action='store_true', help='Show daemon status')
    parser.add_argument('--create-config', action='store_true', help='Create default configuration file')
    
    args = parser.parse_args()
    
    daemon = EFISDaemon(args.config)
    
    if args.create_config:
        daemon.config_manager.save_default_config()
        print(f"Created default configuration: {daemon.config_manager.config_path}")
        return
    
    if args.stop:
        # TODO: Implement proper daemon stop via signal
        print("Stop functionality not yet implemented")
        return
    
    if args.status:
        # TODO: Implement status check
        print("Status functionality not yet implemented")
        return
    
    if args.daemon:
        # TODO: Implement proper daemonization (fork, etc.)
        print("Daemonization not yet implemented, running in foreground")
    
    # Start the daemon
    try:
        daemon.start()
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == '__main__':
    main()