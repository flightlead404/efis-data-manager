#!/usr/bin/env python3
"""
EFIS Data Manager CLI for Windows.
Command-line interface for managing EFIS operations on Windows.
"""

import sys
import argparse
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add shared modules to path
sys.path.append(str(Path(__file__).parent.parent / "shared"))

from src.imdisk_wrapper import VirtualDriveManager
from src.windows_service import EFISDataManagerService, ServiceManager
from src.notification_service import WindowsNotificationService
from utils.troubleshooting import SystemDiagnostics


class WindowsEFISCLI:
    """Windows CLI manager for EFIS operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Windows CLI manager."""
        self.config_path = config_path
        self.config = None
        self.logger = None
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup basic logging for CLI operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> bool:
        """Load configuration."""
        try:
            # Try to find configuration file
            config_paths = [
                Path.cwd() / 'config' / 'windows-config.json',
                Path(__file__).parent.parent / 'config' / 'windows-config.json',
                Path('C:/Scripts/efis-config.json'),
                Path.home() / '.efis' / 'windows-config.json'
            ]
            
            if self.config_path:
                config_paths.insert(0, Path(self.config_path))
            
            config_file = None
            for path in config_paths:
                if path.exists():
                    config_file = path
                    break
            
            if not config_file:
                print("Warning: No configuration file found")
                return False
            
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def check_virtual_drive(self) -> Dict[str, Any]:
        """Check virtual drive status."""
        try:
            if not self.config:
                return {'error': 'Configuration not loaded'}
            
            drive_config = self.config.get('virtualDrive', {})
            
            # Initialize drive manager
            manager_config = {
                'virtualDriveFile': drive_config.get('vhdPath'),
                'mountTool': drive_config.get('mountTool'),
                'driveLetter': drive_config.get('driveLetter'),
                'retryAttempts': 3,
                'retryDelay': 60
            }
            
            drive_manager = VirtualDriveManager(manager_config, self.logger)
            
            # Check drive status
            is_mounted = drive_manager.check_drive_status()
            
            status = {
                'mounted': is_mounted,
                'drive_letter': drive_config.get('driveLetter'),
                'vhd_path': drive_config.get('vhdPath'),
                'mount_tool': drive_config.get('mountTool')
            }
            
            if is_mounted:
                # Get drive information
                drive_letter = drive_config.get('driveLetter', 'E:')
                try:
                    import shutil
                    total, used, free = shutil.disk_usage(drive_letter)
                    status.update({
                        'total_space': total,
                        'used_space': used,
                        'free_space': free,
                        'total_gb': total / (1024**3),
                        'used_gb': used / (1024**3),
                        'free_gb': free / (1024**3)
                    })
                except Exception as e:
                    status['space_error'] = str(e)
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
    def mount_virtual_drive(self, force: bool = False) -> bool:
        """Mount the virtual drive."""
        try:
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            drive_config = self.config.get('virtualDrive', {})
            
            manager_config = {
                'virtualDriveFile': drive_config.get('vhdPath'),
                'mountTool': drive_config.get('mountTool'),
                'driveLetter': drive_config.get('driveLetter'),
                'retryAttempts': 3,
                'retryDelay': 60
            }
            
            drive_manager = VirtualDriveManager(manager_config, self.logger)
            
            # Check if already mounted
            if drive_manager.check_drive_status() and not force:
                print("Virtual drive is already mounted")
                return True
            
            print("Mounting virtual drive...")
            success = drive_manager.ensure_drive_mounted()
            
            if success:
                print(f"Virtual drive mounted successfully at {drive_config.get('driveLetter')}")
                return True
            else:
                print("Failed to mount virtual drive")
                return False
                
        except Exception as e:
            print(f"Error mounting virtual drive: {e}")
            return False
    
    def unmount_virtual_drive(self) -> bool:
        """Unmount the virtual drive."""
        try:
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            drive_config = self.config.get('virtualDrive', {})
            
            manager_config = {
                'virtualDriveFile': drive_config.get('vhdPath'),
                'mountTool': drive_config.get('mountTool'),
                'driveLetter': drive_config.get('driveLetter'),
                'retryAttempts': 3,
                'retryDelay': 60
            }
            
            drive_manager = VirtualDriveManager(manager_config, self.logger)
            
            print("Unmounting virtual drive...")
            # This would call the unmount method when implemented
            print("Unmount functionality not yet implemented")
            return True
            
        except Exception as e:
            print(f"Error unmounting virtual drive: {e}")
            return False
    
    def service_status(self) -> Dict[str, Any]:
        """Get Windows service status."""
        try:
            service_manager = ServiceManager(self.logger)
            status_text = service_manager.get_service_status()
            
            return {
                'service_name': 'EFISDataManager',
                'status': status_text,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def start_service(self) -> bool:
        """Start the Windows service."""
        try:
            print("Starting EFIS Data Manager service...")
            service_manager = ServiceManager(self.logger)
            
            success = service_manager.start_service()
            if success:
                print("Service started successfully")
            else:
                print("Failed to start service")
            
            return success
            
        except Exception as e:
            print(f"Error starting service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the Windows service."""
        try:
            print("Stopping EFIS Data Manager service...")
            service_manager = ServiceManager(self.logger)
            
            success = service_manager.stop_service()
            if success:
                print("Service stopped successfully")
            else:
                print("Failed to stop service")
            
            return success
            
        except Exception as e:
            print(f"Error stopping service: {e}")
            return False
    
    def install_service(self) -> bool:
        """Install the Windows service."""
        try:
            print("Installing EFIS Data Manager service...")
            service_manager = ServiceManager(self.logger)
            
            success = service_manager.install_service()
            if success:
                print("Service installed successfully")
                print("Use 'efis_cli service start' to start the service")
            else:
                print("Failed to install service")
            
            return success
            
        except Exception as e:
            print(f"Error installing service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the Windows service."""
        try:
            print("Uninstalling EFIS Data Manager service...")
            service_manager = ServiceManager(self.logger)
            
            success = service_manager.remove_service()
            if success:
                print("Service uninstalled successfully")
            else:
                print("Failed to uninstall service")
            
            return success
            
        except Exception as e:
            print(f"Error uninstalling service: {e}")
            return False
    
    def manual_sync(self, target: Optional[str] = None) -> bool:
        """Trigger manual synchronization."""
        try:
            print("Starting manual synchronization...")
            
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            # Get sync configuration
            sync_config = self.config.get('sync', {})
            target_ip = target or sync_config.get('macbookIP')
            
            if not target_ip:
                print("Error: No target IP specified")
                return False
            
            print(f"Would sync with target: {target_ip}")
            print("Manual sync functionality not yet fully implemented")
            
            return True
            
        except Exception as e:
            print(f"Error during manual sync: {e}")
            return False
    
    def view_logs(self, lines: int = 50, component: Optional[str] = None) -> bool:
        """View system logs."""
        try:
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            log_file = self.config.get('logging', {}).get('file')
            if not log_file:
                print("Error: Log file not configured")
                return False
            
            log_path = Path(log_file)
            if not log_path.exists():
                print(f"Log file not found: {log_file}")
                return False
            
            print(f"Showing last {lines} lines from: {log_file}")
            print("-" * 80)
            
            # Use PowerShell Get-Content to read last lines
            try:
                cmd = f'Get-Content "{log_path}" -Tail {lines}'
                result = subprocess.run(
                    ['powershell', '-Command', cmd],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    lines_output = result.stdout.strip().split('\n')
                    
                    # Filter by component if specified
                    if component:
                        lines_output = [line for line in lines_output if component.lower() in line.lower()]
                        print(f"Filtered for component: {component}")
                    
                    for line in lines_output:
                        print(line)
                    
                    print("-" * 80)
                    print(f"Displayed {len(lines_output)} lines")
                else:
                    print(f"Error reading log file: {result.stderr}")
                    return False
                
            except subprocess.TimeoutExpired:
                print("Timeout reading log file")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error viewing logs: {e}")
            return False
    
    def check_system_status(self) -> Dict[str, Any]:
        """Check overall system status."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'config_loaded': self.config is not None,
                'virtual_drive': self.check_virtual_drive(),
                'service': self.service_status()
            }
            
            # Check ImDisk availability
            if self.config:
                mount_tool = self.config.get('virtualDrive', {}).get('mountTool')
                if mount_tool:
                    mount_tool_path = Path(mount_tool)
                    status['imdisk_available'] = mount_tool_path.exists()
                else:
                    status['imdisk_available'] = False
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
    def manage_config(self, action: str, key: Optional[str] = None, value: Optional[str] = None) -> bool:
        """Manage configuration settings."""
        try:
            if action == "show":
                if not self.config:
                    print("Configuration not loaded")
                    return False
                
                print("Current Configuration:")
                print("-" * 40)
                print(json.dumps(self.config, indent=2))
                return True
                
            elif action == "get":
                if not key:
                    print("Error: Key required for get action")
                    return False
                
                if not self.config:
                    print("Configuration not loaded")
                    return False
                
                # Navigate nested keys (e.g., "virtualDrive.driveLetter")
                keys = key.split('.')
                config_value = self.config
                
                for k in keys:
                    if isinstance(config_value, dict) and k in config_value:
                        config_value = config_value[k]
                    else:
                        print(f"Key not found: {key}")
                        return False
                
                print(f"{key}: {config_value}")
                return True
                
            elif action == "set":
                if not key or value is None:
                    print("Error: Key and value required for set action")
                    return False
                
                print(f"Would set {key} = {value}")
                print("Configuration update not yet implemented")
                return True
                
            else:
                print(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            print(f"Error managing configuration: {e}")
            return False
    
    def run_diagnostics(self) -> bool:
        """Run system diagnostics."""
        try:
            print("Running EFIS Data Manager diagnostics...")
            print("=" * 50)
            
            diagnostics = SystemDiagnostics(self.logger)
            results = diagnostics.run_full_diagnostics()
            
            # Display results
            print(f"Diagnostics completed at: {results['timestamp']}")
            print(f"Platform: {results['platform']}")
            print()
            
            # System info
            system_info = results.get('system_info', {})
            if 'error' not in system_info:
                print("System Information:")
                print("-" * 20)
                for key, value in system_info.items():
                    print(f"  {key}: {value}")
                print()
            
            # Windows-specific info
            windows_info = results.get('windows_specific', {})
            if windows_info and 'error' not in windows_info:
                print("Windows-Specific Status:")
                print("-" * 25)
                print(f"  ImDisk installed: {'Yes' if windows_info.get('imdisk_installed', False) else 'No'}")
                print(f"  Service installed: {'Yes' if windows_info.get('service_installed', False) else 'No'}")
                print(f"  Scheduled task exists: {'Yes' if windows_info.get('scheduled_task_exists', False) else 'No'}")
                print()
            
            # Disk space
            disk_space = results.get('disk_space', {})
            if disk_space and 'error' not in disk_space:
                print("Disk Space:")
                print("-" * 12)
                for drive, info in disk_space.items():
                    if isinstance(info, dict) and 'error' not in info:
                        print(f"  {drive}: {info['free_gb']:.1f} GB free ({info['usage_percent']:.1f}% used)")
                print()
            
            # Network connectivity
            network = results.get('network_connectivity', {})
            if network and 'error' not in network:
                print("Network Connectivity:")
                print("-" * 20)
                for host, info in network.items():
                    if isinstance(info, dict):
                        status = "✓" if info.get('reachable', False) else "✗"
                        print(f"  {host}: {status}")
                print()
            
            # Log analysis
            log_analysis = results.get('log_analysis', {})
            if log_analysis and 'error' not in log_analysis:
                print("Log Analysis:")
                print("-" * 13)
                print(f"  Errors: {log_analysis.get('error_count', 0)}")
                print(f"  Warnings: {log_analysis.get('warning_count', 0)}")
                print(f"  Last activity: {log_analysis.get('last_activity', 'Unknown')}")
                
                recent_errors = log_analysis.get('recent_errors', [])
                if recent_errors:
                    print("  Recent errors:")
                    for error in recent_errors[:3]:
                        print(f"    {error}")
                print()
            
            # Recommendations
            recommendations = results.get('recommendations', [])
            if recommendations:
                print("Recommendations:")
                print("-" * 15)
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec}")
                print()
            
            return True
            
        except Exception as e:
            print(f"Error running diagnostics: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='EFIS Data Manager CLI for Windows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status
  %(prog)s drive mount
  %(prog)s drive status
  %(prog)s service start
  %(prog)s service status
  %(prog)s sync --target 192.168.1.100
  %(prog)s logs --lines 100
  %(prog)s config show
        """
    )
    
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # System status
    status_parser = subparsers.add_parser('status', help='Check system status')
    status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # Virtual drive management
    drive_parser = subparsers.add_parser('drive', help='Manage virtual drive')
    drive_subparsers = drive_parser.add_subparsers(dest='drive_action', help='Drive actions')
    
    drive_status_parser = drive_subparsers.add_parser('status', help='Check drive status')
    drive_status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    drive_mount_parser = drive_subparsers.add_parser('mount', help='Mount virtual drive')
    drive_mount_parser.add_argument('--force', action='store_true', help='Force mount even if already mounted')
    
    drive_unmount_parser = drive_subparsers.add_parser('unmount', help='Unmount virtual drive')
    
    # Service management
    service_parser = subparsers.add_parser('service', help='Manage Windows service')
    service_subparsers = service_parser.add_subparsers(dest='service_action', help='Service actions')
    
    service_status_parser = service_subparsers.add_parser('status', help='Check service status')
    service_start_parser = service_subparsers.add_parser('start', help='Start service')
    service_stop_parser = service_subparsers.add_parser('stop', help='Stop service')
    service_install_parser = service_subparsers.add_parser('install', help='Install service')
    service_uninstall_parser = service_subparsers.add_parser('uninstall', help='Uninstall service')
    
    # Manual sync
    sync_parser = subparsers.add_parser('sync', help='Trigger manual synchronization')
    sync_parser.add_argument('--target', help='Target IP address to sync with')
    
    # Log viewing
    logs_parser = subparsers.add_parser('logs', help='View system logs')
    logs_parser.add_argument('--lines', '-n', type=int, default=50, help='Number of lines to show')
    logs_parser.add_argument('--component', help='Filter logs by component')
    
    # Configuration management
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_subparsers = config_parser.add_subparsers(dest='config_action', help='Configuration actions')
    
    # Diagnostics
    diagnostics_parser = subparsers.add_parser('diagnostics', help='Run system diagnostics')
    
    config_show_parser = config_subparsers.add_parser('show', help='Show current configuration')
    
    config_get_parser = config_subparsers.add_parser('get', help='Get configuration value')
    config_get_parser.add_argument('key', help='Configuration key (use dots for nested keys)')
    
    config_set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    config_set_parser.add_argument('key', help='Configuration key')
    config_set_parser.add_argument('value', help='Configuration value')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI manager
    cli = WindowsEFISCLI(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration for most commands
    if not cli.load_config():
        print("Warning: Could not load configuration, some features may not work")
    
    # Execute command
    try:
        if args.command == 'status':
            status = cli.check_system_status()
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print("EFIS Data Manager Status:")
                print("-" * 30)
                for key, value in status.items():
                    if isinstance(value, dict):
                        print(f"{key}:")
                        for sub_key, sub_value in value.items():
                            print(f"  {sub_key}: {sub_value}")
                    else:
                        print(f"{key}: {value}")
            return 0
            
        elif args.command == 'drive':
            if not args.drive_action:
                drive_parser.print_help()
                return 1
            
            if args.drive_action == 'status':
                status = cli.check_virtual_drive()
                if args.json:
                    print(json.dumps(status, indent=2))
                else:
                    print("Virtual Drive Status:")
                    print("-" * 25)
                    for key, value in status.items():
                        if key.endswith('_gb'):
                            print(f"{key}: {value:.2f} GB")
                        else:
                            print(f"{key}: {value}")
                return 0
                
            elif args.drive_action == 'mount':
                success = cli.mount_virtual_drive(args.force)
                return 0 if success else 1
                
            elif args.drive_action == 'unmount':
                success = cli.unmount_virtual_drive()
                return 0 if success else 1
            
        elif args.command == 'service':
            if not args.service_action:
                service_parser.print_help()
                return 1
            
            if args.service_action == 'status':
                status = cli.service_status()
                print("Service Status:")
                print("-" * 15)
                for key, value in status.items():
                    print(f"{key}: {value}")
                return 0
                
            elif args.service_action == 'start':
                success = cli.start_service()
                return 0 if success else 1
                
            elif args.service_action == 'stop':
                success = cli.stop_service()
                return 0 if success else 1
                
            elif args.service_action == 'install':
                success = cli.install_service()
                return 0 if success else 1
                
            elif args.service_action == 'uninstall':
                success = cli.uninstall_service()
                return 0 if success else 1
            
        elif args.command == 'sync':
            success = cli.manual_sync(args.target)
            return 0 if success else 1
            
        elif args.command == 'logs':
            success = cli.view_logs(args.lines, args.component)
            return 0 if success else 1
            
        elif args.command == 'config':
            if not args.config_action:
                config_parser.print_help()
                return 1
            
            success = cli.manage_config(
                args.config_action,
                getattr(args, 'key', None),
                getattr(args, 'value', None)
            )
            return 0 if success else 1
            
        elif args.command == 'diagnostics':
            success = cli.run_diagnostics()
            return 0 if success else 1
        """Run system diagnostics."""
        try:
            print("Running EFIS Data Manager diagnostics...")
            print("=" * 50)
            
            diagnostics = SystemDiagnostics(self.logger)
            results = diagnostics.run_full_diagnostics()
            
            # Display results
            print(f"Diagnostics completed at: {results['timestamp']}")
            print(f"Platform: {results['platform']}")
            print()
            
            # System info
            system_info = results.get('system_info', {})
            if 'error' not in system_info:
                print("System Information:")
                print("-" * 20)
                for key, value in system_info.items():
                    print(f"  {key}: {value}")
                print()
            
            # Windows-specific info
            windows_info = results.get('windows_specific', {})
            if windows_info and 'error' not in windows_info:
                print("Windows-Specific Status:")
                print("-" * 25)
                print(f"  ImDisk installed: {'Yes' if windows_info.get('imdisk_installed', False) else 'No'}")
                print(f"  Service installed: {'Yes' if windows_info.get('service_installed', False) else 'No'}")
                print(f"  Scheduled task exists: {'Yes' if windows_info.get('scheduled_task_exists', False) else 'No'}")
                print()
            
            # Disk space
            disk_space = results.get('disk_space', {})
            if disk_space and 'error' not in disk_space:
                print("Disk Space:")
                print("-" * 12)
                for drive, info in disk_space.items():
                    if isinstance(info, dict) and 'error' not in info:
                        print(f"  {drive}: {info['free_gb']:.1f} GB free ({info['usage_percent']:.1f}% used)")
                print()
            
            # Network connectivity
            network = results.get('network_connectivity', {})
            if network and 'error' not in network:
                print("Network Connectivity:")
                print("-" * 20)
                for host, info in network.items():
                    if isinstance(info, dict):
                        status = "✓" if info.get('reachable', False) else "✗"
                        print(f"  {host}: {status}")
                print()
            
            # Log analysis
            log_analysis = results.get('log_analysis', {})
            if log_analysis and 'error' not in log_analysis:
                print("Log Analysis:")
                print("-" * 13)
                print(f"  Errors: {log_analysis.get('error_count', 0)}")
                print(f"  Warnings: {log_analysis.get('warning_count', 0)}")
                print(f"  Last activity: {log_analysis.get('last_activity', 'Unknown')}")
                
                recent_errors = log_analysis.get('recent_errors', [])
                if recent_errors:
                    print("  Recent errors:")
                    for error in recent_errors[:3]:
                        print(f"    {error}")
                print()
            
            # Recommendations
            recommendations = results.get('recommendations', [])
            if recommendations:
                print("Recommendations:")
                print("-" * 15)
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec}")
                print()
            
            return True
            
        except Exception as e:
            print(f"Error running diagnostics: {e}")
            return False
            
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())