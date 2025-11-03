"""
Windows Service for EFIS Data Manager.
Manages virtual drive mounting and chart data synchronization.
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Windows service imports
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False
    # Mock classes for development/testing on non-Windows systems
    class win32serviceutil:
        class ServiceFramework:
            def __init__(self, args): pass
            def SvcStop(self): pass
            def SvcDoRun(self): pass
            def ReportServiceStatus(self, status): pass
    
    class win32service:
        SERVICE_STOPPED = 1
        SERVICE_STOP_PENDING = 3
        SERVICE_RUNNING = 4

# Local imports
from imdisk_wrapper import VirtualDriveManager, MountResult
from drive_monitor import DriveMonitor, DriveHealthChecker, MonitoringState
from network_manager import create_network_manager
from sync_engine import create_sync_engine
from sync_scheduler import create_sync_scheduler
from notification_service import WindowsNotificationService

# Add shared modules to path
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent.parent / 'shared'
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from config.config_manager import ConfigManager
from utils.logging_config import setup_component_logging


class EFISDataManagerService(win32serviceutil.ServiceFramework):
    """
    Windows Service for EFIS Data Manager.
    
    Handles virtual drive management, monitoring, and synchronization tasks.
    """
    
    _svc_name_ = "EFISDataManager"
    _svc_display_name_ = "EFIS Data Manager Service"
    _svc_description_ = "Manages virtual USB drive mounting and chart data synchronization for EFIS systems"
    
    def __init__(self, args):
        """Initialize the service."""
        if WINDOWS_SERVICE_AVAILABLE:
            win32serviceutil.ServiceFramework.__init__(self, args)
        
        # Service control events
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None) if WINDOWS_SERVICE_AVAILABLE else None
        self.is_running = False
        
        # Service components
        self.config_manager = None
        self.config = {}
        self.logger = None
        self.drive_manager = None
        self.drive_monitor = None
        self.health_checker = None
        self.network_manager = None
        self.sync_engine = None
        self.sync_scheduler = None
        self.notification_service = None
        
        # Threading
        self.stop_event = threading.Event()
        
    def SvcStop(self):
        """Handle service stop request."""
        if self.logger:
            self.logger.info("EFIS Data Manager Service stop requested")
        
        # Signal service is stopping
        if WINDOWS_SERVICE_AVAILABLE:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        
        # Set stop event to signal threads
        self.stop_event.set()
        self.is_running = False
        
        # Signal the main service thread
        if WINDOWS_SERVICE_AVAILABLE and self.hWaitStop:
            win32event.SetEvent(self.hWaitStop)
            
    def SvcDoRun(self):
        """Main service execution."""
        try:
            # Initialize service
            self._initialize_service()
            
            if self.logger:
                self.logger.info("EFIS Data Manager Service starting")
                
            # Log service start to Windows Event Log
            if WINDOWS_SERVICE_AVAILABLE:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
            
            # Start service threads
            self._start_service_threads()
            
            # Mark service as running
            self.is_running = True
            if WINDOWS_SERVICE_AVAILABLE:
                self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            
            if self.logger:
                self.logger.info("EFIS Data Manager Service started successfully")
            
            # Send startup notification
            if self.notification_service:
                self.notification_service.notify_service_started()
            
            # Main service loop
            self._run_service_loop()
            
        except Exception as e:
            error_msg = f"Service startup failed: {e}"
            if self.logger:
                self.logger.error(error_msg)
            
            # Log error to Windows Event Log
            if WINDOWS_SERVICE_AVAILABLE:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_ERROR_TYPE,
                    servicemanager.PYS_SERVICE_STOPPED,
                    (self._svc_name_, error_msg)
                )
            raise
        finally:
            # Cleanup
            self._cleanup_service()
            
    def _initialize_service(self):
        """Initialize service components."""
        try:
            # Load configuration
            self._load_configuration()
            
            # Setup logging
            self._setup_logging()
            
            # Initialize notification system
            self._initialize_notifications()
            
            # Initialize drive manager
            self._initialize_drive_manager()
            
            # Perform initial drive check
            self._initial_drive_check()
            
        except Exception as e:
            # Try to log error if logger is available
            if self.logger:
                self.logger.error(f"Service initialization failed: {e}")
            raise
            
    def _load_configuration(self):
        """Load service configuration."""
        # Try to find configuration file
        config_paths = [
            Path.cwd() / 'config' / 'windows-config.json',
            Path(__file__).parent.parent.parent / 'config' / 'windows-config.json',
            Path('C:/Scripts/efis-config.json'),
            Path.home() / '.efis' / 'windows-config.json'
        ]
        
        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break
                
        if not config_file:
            # Create default configuration
            config_file = config_paths[0]
            self._create_default_config(config_file)
            
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            
        # Validate required configuration
        self._validate_configuration()
        
    def _create_default_config(self, config_file: Path):
        """Create default configuration file."""
        default_config = {
            "virtualDrive": {
                "vhdPath": "C:\\Users\\fligh\\OneDrive\\Desktop\\virtualEFISUSB.vhd",
                "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",
                "driveLetter": "E:",
                "logFile": "C:\\Scripts\\MountEFIS.log"
            },
            "sync": {
                "interval": 1800,
                "macbookIP": "192.168.1.100",
                "retryAttempts": 3,
                "retryDelay": 600
            },
            "monitoring": {
                "checkInterval": 300,
                "remountRetryDelay": 60
            },
            "logging": {
                "level": "INFO",
                "file": "C:\\Scripts\\efis-data-manager.log",
                "maxSize": "10MB",
                "backupCount": 5
            }
        }
        
        # Ensure directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default configuration
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        self.config = default_config
        
    def _validate_configuration(self):
        """Validate configuration has required fields."""
        required_fields = [
            ('virtualDrive', 'vhdPath'),
            ('virtualDrive', 'mountTool'),
            ('virtualDrive', 'driveLetter'),
            ('monitoring', 'checkInterval'),
            ('logging', 'level')
        ]
        
        for section, field in required_fields:
            if section not in self.config or field not in self.config[section]:
                raise ValueError(f"Missing required configuration: {section}.{field}")
                
    def _setup_logging(self):
        """Setup service logging."""
        log_config = self.config.get('logging', {})
        
        # Setup component logging
        self.logger = setup_component_logging('windows-service', {'logging': log_config})
        
        # Also setup file handler for service-specific log
        log_file = log_config.get('file', 'C:\\Scripts\\efis-data-manager.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _initialize_notifications(self):
        """Initialize notification system."""
        try:
            self.notification_service = WindowsNotificationService(self.config)
            self.logger.info("Notification system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize notification system: {e}")
            self.notification_service = None
        
    def _initialize_drive_manager(self):
        """Initialize virtual drive manager."""
        drive_config = self.config['virtualDrive']
        
        # Map configuration to expected format
        manager_config = {
            'virtualDriveFile': drive_config['vhdPath'],
            'mountTool': drive_config['mountTool'],
            'driveLetter': drive_config['driveLetter'],
            'retryAttempts': self.config.get('sync', {}).get('retryAttempts', 3),
            'retryDelay': self.config.get('monitoring', {}).get('remountRetryDelay', 60)
        }
        
        self.drive_manager = VirtualDriveManager(manager_config, self.logger)
        
        # Initialize drive monitor
        monitor_config = self.config.get('monitoring', {})
        self.drive_monitor = DriveMonitor(self.drive_manager, monitor_config, self.logger)
        
        # Setup monitor callbacks
        self.drive_monitor.on_mount_success = self._on_drive_mount_success
        self.drive_monitor.on_mount_failure = self._on_drive_mount_failure
        self.drive_monitor.on_drive_lost = self._on_drive_lost
        self.drive_monitor.on_drive_recovered = self._on_drive_recovered
        
        # Initialize health checker
        self.health_checker = DriveHealthChecker(self.drive_manager, self.logger)
        
        # Initialize network and sync components
        self.network_manager = create_network_manager(self.config, self.logger)
        self.sync_engine = create_sync_engine(self.network_manager, self.config, self.logger)
        self.sync_scheduler = create_sync_scheduler(self.sync_engine, self.network_manager, self.config, self.logger)
        
        # Setup sync callbacks
        self.sync_scheduler.on_sync_start = self._on_sync_start
        self.sync_scheduler.on_sync_success = self._on_sync_success
        self.sync_scheduler.on_sync_failure = self._on_sync_failure
        self.sync_scheduler.on_sync_retry = self._on_sync_retry
        
    def _initial_drive_check(self):
        """Perform initial drive mount check."""
        self.logger.info("Performing initial virtual drive check")
        
        try:
            if self.drive_manager.ensure_drive_mounted():
                self.logger.info("Virtual drive is properly mounted")
            else:
                self.logger.error("Failed to mount virtual drive during startup")
                
        except Exception as e:
            self.logger.error(f"Error during initial drive check: {e}")
            
    def _start_service_threads(self):
        """Start service worker threads."""
        # Start drive monitor
        if not self.drive_monitor.start():
            raise RuntimeError("Failed to start drive monitor")
        
        # Start sync scheduler (if sync is configured)
        if self.config.get('sync', {}).get('macbookHostname') or self.config.get('sync', {}).get('macbookIP'):
            if not self.sync_scheduler.start():
                raise RuntimeError("Failed to start sync scheduler")
            
    def _run_service_loop(self):
        """Main service loop."""
        if WINDOWS_SERVICE_AVAILABLE and self.hWaitStop:
            # Wait for stop signal
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        else:
            # Fallback for non-Windows or testing
            while self.is_running and not self.stop_event.is_set():
                time.sleep(1)
                
    def _on_drive_mount_success(self, drive_info):
        """Callback for successful drive mount."""
        self.logger.info(f"Drive mount successful: {drive_info.drive_letter}")
        
        # Log drive information
        if drive_info.free_space_bytes:
            free_gb = drive_info.free_space_bytes / (1024**3)
            self.logger.info(f"Drive space: {free_gb:.2f} GB free")
        
        # Send notification
        if self.notification_service:
            self.notification_service.notify_drive_mounted(drive_info.drive_letter)
            
    def _on_drive_mount_failure(self, error_msg):
        """Callback for failed drive mount."""
        self.logger.error(f"Drive mount failed: {error_msg}")
        
        # Send notification
        if self.notification_service:
            self.notification_service.notify_drive_mount_failed(error_msg)
        
    def _on_drive_lost(self):
        """Callback when drive is lost."""
        self.logger.warning("Virtual drive connection lost")
        
    def _on_drive_recovered(self, drive_info):
        """Callback when drive is recovered."""
        self.logger.info(f"Virtual drive recovered: {drive_info.drive_letter}")
        
    def _on_sync_start(self):
        """Callback when sync starts."""
        self.logger.info("Chart synchronization started")
        
        # Send notification
        if self.notification_service:
            macbook_target = self.config.get('sync', {}).get('macbookIP', 'MacBook')
            self.notification_service.notify_sync_started(macbook_target)
        
    def _on_sync_success(self, sync_result):
        """Callback when sync succeeds."""
        self.logger.info(f"Chart synchronization completed: {sync_result.files_transferred} files, "
                        f"{sync_result.bytes_transferred/(1024*1024):.1f} MB in {sync_result.duration_seconds:.1f}s")
        
        # Send notification
        if self.notification_service:
            self.notification_service.notify_sync_completed(
                sync_result.files_transferred,
                sync_result.bytes_transferred,
                sync_result.duration_seconds
            )
        
    def _on_sync_failure(self, error_message):
        """Callback when sync fails."""
        self.logger.error(f"Chart synchronization failed: {error_message}")
        
        # Send notification
        if self.notification_service:
            self.notification_service.notify_sync_failed(error_message)
        
    def _on_sync_retry(self, attempt, max_attempts):
        """Callback when sync is retrying."""
        self.logger.warning(f"Chart synchronization retry {attempt}/{max_attempts}")
        

        
    def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            self.logger.debug("Performing drive health check")
            
            health_results = self.health_checker.perform_health_check()
            
            # Log health status
            overall_health = health_results.get('overall_health', 'unknown')
            self.logger.info(f"Drive health status: {overall_health}")
            
            # Log any failed checks
            for check_name, check_result in health_results.get('checks', {}).items():
                if check_result['status'] in ['fail', 'warning']:
                    self.logger.warning(f"Health check '{check_name}': {check_result['details']}")
                    
            return health_results
            
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
            return None
            
    def _perform_sync(self):
        """Perform chart data synchronization."""
        try:
            self.logger.info("Starting chart data synchronization")
            
            # Check if drive is mounted first
            if not self.drive_manager.check_drive_status():
                self.logger.warning("Virtual drive not mounted, skipping sync")
                return
                
            # TODO: Implement actual sync logic in task 3
            # For now, just log that sync would happen
            macbook_ip = self.config.get('sync', {}).get('macbookIP')
            self.logger.info(f"Would sync chart data to MacBook at {macbook_ip}")
            
            # Placeholder for sync implementation
            self.logger.info("Chart data synchronization completed (placeholder)")
            
        except Exception as e:
            self.logger.error(f"Error during synchronization: {e}")
            
    def _cleanup_service(self):
        """Cleanup service resources."""
        try:
            if self.logger:
                self.logger.info("EFIS Data Manager Service stopping")
            
            # Stop drive monitor
            if self.drive_monitor:
                self.drive_monitor.stop(timeout=10)
                
            # Stop sync scheduler
            if self.sync_scheduler:
                self.sync_scheduler.stop(timeout=10)
                
            # Log service stop
            if WINDOWS_SERVICE_AVAILABLE:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STOPPED,
                    (self._svc_name_, '')
                )
                
            if self.logger:
                self.logger.info("EFIS Data Manager Service stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during service cleanup: {e}")


class ServiceManager:
    """
    Manager for Windows service operations.
    
    Provides methods to install, remove, start, and stop the service.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize service manager."""
        self.logger = logger or logging.getLogger(__name__)
        
    def install_service(self) -> bool:
        """
        Install the Windows service.
        
        Returns:
            True if installation successful, False otherwise
        """
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                self.logger.error("Windows service modules not available")
                return False
                
            self.logger.info("Installing EFIS Data Manager Service")
            
            # Install service
            win32serviceutil.InstallService(
                EFISDataManagerService._svc_reg_class_,
                EFISDataManagerService._svc_name_,
                EFISDataManagerService._svc_display_name_,
                description=EFISDataManagerService._svc_description_
            )
            
            self.logger.info("Service installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install service: {e}")
            return False
            
    def remove_service(self) -> bool:
        """
        Remove the Windows service.
        
        Returns:
            True if removal successful, False otherwise
        """
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                self.logger.error("Windows service modules not available")
                return False
                
            self.logger.info("Removing EFIS Data Manager Service")
            
            # Stop service first if running
            self.stop_service()
            
            # Remove service
            win32serviceutil.RemoveService(EFISDataManagerService._svc_name_)
            
            self.logger.info("Service removed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove service: {e}")
            return False
            
    def start_service(self) -> bool:
        """
        Start the Windows service.
        
        Returns:
            True if start successful, False otherwise
        """
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                self.logger.error("Windows service modules not available")
                return False
                
            self.logger.info("Starting EFIS Data Manager Service")
            
            win32serviceutil.StartService(EFISDataManagerService._svc_name_)
            
            self.logger.info("Service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
            
    def stop_service(self) -> bool:
        """
        Stop the Windows service.
        
        Returns:
            True if stop successful, False otherwise
        """
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                self.logger.error("Windows service modules not available")
                return False
                
            self.logger.info("Stopping EFIS Data Manager Service")
            
            win32serviceutil.StopService(EFISDataManagerService._svc_name_)
            
            self.logger.info("Service stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop service: {e}")
            return False
            
    def get_service_status(self) -> str:
        """
        Get current service status.
        
        Returns:
            Service status string
        """
        try:
            if not WINDOWS_SERVICE_AVAILABLE:
                return "Windows service modules not available"
                
            status = win32serviceutil.QueryServiceStatus(EFISDataManagerService._svc_name_)
            
            status_map = {
                win32service.SERVICE_STOPPED: "Stopped",
                win32service.SERVICE_START_PENDING: "Starting",
                win32service.SERVICE_STOP_PENDING: "Stopping",
                win32service.SERVICE_RUNNING: "Running",
                win32service.SERVICE_CONTINUE_PENDING: "Continuing",
                win32service.SERVICE_PAUSE_PENDING: "Pausing",
                win32service.SERVICE_PAUSED: "Paused"
            }
            
            return status_map.get(status[1], f"Unknown ({status[1]})")
            
        except Exception as e:
            return f"Error getting status: {e}"


def main():
    """Main entry point for service operations."""
    if len(sys.argv) == 1:
        # No arguments - try to start as service
        if WINDOWS_SERVICE_AVAILABLE:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(EFISDataManagerService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print("Windows service modules not available")
            sys.exit(1)
    else:
        # Handle command line arguments
        if WINDOWS_SERVICE_AVAILABLE:
            win32serviceutil.HandleCommandLine(EFISDataManagerService)
        else:
            print("Windows service modules not available")
            sys.exit(1)


if __name__ == '__main__':
    main()