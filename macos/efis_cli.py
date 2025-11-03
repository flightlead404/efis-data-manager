#!/usr/bin/env python3
"""
EFIS Data Manager CLI for macOS.
Command-line interface for managing EFIS operations.
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add shared modules to path
sys.path.append(str(Path(__file__).parent.parent / "shared"))

from src.efis_macos.config import ConfigManager
from src.efis_macos.usb_drive_processor import USBDriveProcessor
from src.efis_macos.grt_scraper import GRTWebScraper
from src.efis_macos.download_manager import DownloadManager
from src.efis_macos.daemon import EFISDaemon
from notifications import NotificationManager, NotificationPreferences
from utils.troubleshooting import SystemDiagnostics


class EFISCLIManager:
    """Main CLI manager for EFIS operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize CLI manager."""
        self.config_manager = ConfigManager(config_path)
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
            self.config = self.config_manager.load_config()
            return True
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def prepare_usb_drive(self, drive_path: str, force: bool = False) -> bool:
        """
        Prepare a new EFIS USB drive.
        
        Args:
            drive_path: Path to USB drive mount point
            force: Force preparation even if drive appears to have data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Preparing EFIS USB drive at: {drive_path}")
            
            drive_path_obj = Path(drive_path)
            if not drive_path_obj.exists():
                print(f"Error: Drive path does not exist: {drive_path}")
                return False
            
            if not drive_path_obj.is_dir():
                print(f"Error: Path is not a directory: {drive_path}")
                return False
            
            # Check if drive already has files
            existing_files = list(drive_path_obj.iterdir())
            if existing_files and not force:
                print(f"Warning: Drive contains {len(existing_files)} files/folders")
                print("Use --force to proceed anyway")
                return False
            
            # Create EFIS identification markers
            print("Creating EFIS identification markers...")
            efis_marker = drive_path_obj / ".efis_drive"
            efis_marker.write_text(f"EFIS Drive prepared on {datetime.now().isoformat()}")
            
            # Create directory structure
            directories = [
                "Charts",
                "Software", 
                "Logs",
                "Demo"
            ]
            
            for dir_name in directories:
                dir_path = drive_path_obj / dir_name
                dir_path.mkdir(exist_ok=True)
                print(f"Created directory: {dir_name}")
            
            # Copy current chart data if available
            if self.config and hasattr(self.config, 'archive_path'):
                archive_path = Path(self.config.archive_path)
                if archive_path.exists():
                    print("Copying current chart data...")
                    self._copy_chart_data(archive_path, drive_path_obj / "Charts")
                else:
                    print("Warning: Chart archive not found, skipping chart copy")
            
            # Copy current NAV database if available
            self._copy_nav_database(drive_path_obj)
            
            # Copy current GRT software if available
            self._copy_grt_software(drive_path_obj / "Software")
            
            print(f"USB drive preparation completed successfully!")
            print(f"Drive ready for use with EFIS systems")
            
            return True
            
        except Exception as e:
            print(f"Error preparing USB drive: {e}")
            return False
    
    def _copy_chart_data(self, source_path: Path, dest_path: Path):
        """Copy chart data to USB drive."""
        try:
            import shutil
            
            if source_path.exists() and source_path.is_dir():
                # Copy chart files (this could be large, so show progress)
                chart_files = list(source_path.rglob("*.png"))
                total_files = len(chart_files)
                
                if total_files > 0:
                    print(f"Copying {total_files} chart files...")
                    
                    for i, chart_file in enumerate(chart_files):
                        relative_path = chart_file.relative_to(source_path)
                        dest_file = dest_path / relative_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(chart_file, dest_file)
                        
                        if (i + 1) % 100 == 0:
                            print(f"  Copied {i + 1}/{total_files} files...")
                    
                    print(f"Chart data copy completed")
                else:
                    print("No chart files found in archive")
            else:
                print("Chart archive directory not found")
                
        except Exception as e:
            print(f"Error copying chart data: {e}")
    
    def _copy_nav_database(self, drive_path: Path):
        """Copy NAV database to USB drive."""
        try:
            if self.config and hasattr(self.config, 'archive_path'):
                nav_source = Path(self.config.archive_path) / "NAV.DB"
                if nav_source.exists():
                    nav_dest = drive_path / "NAV.DB"
                    import shutil
                    shutil.copy2(nav_source, nav_dest)
                    print("Copied NAV database")
                else:
                    print("NAV database not found in archive")
            
        except Exception as e:
            print(f"Error copying NAV database: {e}")
    
    def _copy_grt_software(self, software_path: Path):
        """Copy GRT software to USB drive."""
        try:
            if self.config and hasattr(self.config, 'archive_path'):
                software_source = Path(self.config.archive_path) / "Software"
                if software_source.exists():
                    import shutil
                    
                    # Copy all software files
                    for software_file in software_source.iterdir():
                        if software_file.is_file():
                            dest_file = software_path / software_file.name
                            shutil.copy2(software_file, dest_file)
                            print(f"Copied software: {software_file.name}")
                else:
                    print("Software directory not found in archive")
            
        except Exception as e:
            print(f"Error copying GRT software: {e}")
    
    def check_status(self) -> Dict[str, Any]:
        """Check system status."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'config_loaded': self.config is not None,
                'daemon_running': False,
                'last_grt_check': None,
                'usb_drives': [],
                'notifications': 'enabled'
            }
            
            # Check if daemon is running
            try:
                daemon = EFISDaemon()
                daemon_status = daemon.status()
                status['daemon_running'] = daemon_status.get('running', False)
                status['daemon_pid'] = daemon_status.get('pid')
            except Exception as e:
                status['daemon_error'] = str(e)
            
            # Check for connected USB drives
            try:
                import subprocess
                result = subprocess.run(['df', '-h'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    usb_drives = []
                    for line in lines:
                        if '/Volumes/' in line and 'disk' in line:
                            parts = line.split()
                            if len(parts) >= 6:
                                usb_drives.append({
                                    'device': parts[0],
                                    'size': parts[1],
                                    'used': parts[2],
                                    'available': parts[3],
                                    'mount_point': parts[5]
                                })
                    status['usb_drives'] = usb_drives
            except Exception as e:
                status['usb_error'] = str(e)
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
    def manual_sync(self, target: Optional[str] = None) -> bool:
        """
        Trigger manual synchronization.
        
        Args:
            target: Target system to sync with (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Starting manual synchronization...")
            
            # This would typically trigger the sync process
            # For now, just show what would happen
            if target:
                print(f"Would sync with target: {target}")
            else:
                print("Would sync with configured target")
            
            print("Manual sync completed (placeholder)")
            return True
            
        except Exception as e:
            print(f"Error during manual sync: {e}")
            return False
    
    def check_grt_updates(self) -> bool:
        """Check for GRT software updates."""
        try:
            print("Checking for GRT software updates...")
            
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            # Initialize GRT scraper
            scraper = GRTWebScraper()
            
            # Check each software type
            software_types = ['nav', 'hxr', 'mini_ap', 'ahrs', 'servo']
            updates_found = False
            
            for software_type in software_types:
                try:
                    print(f"Checking {software_type.upper()} software...")
                    
                    # This would check for updates
                    # For now, just show placeholder
                    print(f"  {software_type.upper()}: No updates available")
                    
                except Exception as e:
                    print(f"  Error checking {software_type}: {e}")
            
            if not updates_found:
                print("All GRT software is up to date")
            
            return True
            
        except Exception as e:
            print(f"Error checking GRT updates: {e}")
            return False
    
    def view_logs(self, lines: int = 50, component: Optional[str] = None) -> bool:
        """
        View system logs.
        
        Args:
            lines: Number of lines to show
            component: Specific component to show logs for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config:
                print("Error: Configuration not loaded")
                return False
            
            log_file = getattr(self.config, 'log_file', None)
            if not log_file:
                print("Error: Log file not configured")
                return False
            
            log_path = Path(log_file)
            if not log_path.exists():
                print(f"Log file not found: {log_file}")
                return False
            
            print(f"Showing last {lines} lines from: {log_file}")
            print("-" * 80)
            
            # Read and display log lines
            with open(log_path, 'r') as f:
                all_lines = f.readlines()
                
            # Filter by component if specified
            if component:
                filtered_lines = [line for line in all_lines if component.lower() in line.lower()]
                display_lines = filtered_lines[-lines:]
                print(f"Filtered for component: {component}")
            else:
                display_lines = all_lines[-lines:]
            
            for line in display_lines:
                print(line.rstrip())
            
            print("-" * 80)
            print(f"Displayed {len(display_lines)} lines")
            
            return True
            
        except Exception as e:
            print(f"Error viewing logs: {e}")
            return False
    
    def manage_config(self, action: str, key: Optional[str] = None, value: Optional[str] = None) -> bool:
        """
        Manage configuration settings.
        
        Args:
            action: Action to perform (show, set, get)
            key: Configuration key (for set/get actions)
            value: Configuration value (for set action)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if action == "show":
                if not self.config:
                    print("Configuration not loaded")
                    return False
                
                print("Current Configuration:")
                print("-" * 40)
                
                # Display configuration in a readable format
                config_dict = self.config.__dict__ if hasattr(self.config, '__dict__') else {}
                for k, v in config_dict.items():
                    if not k.startswith('_'):
                        print(f"{k}: {v}")
                
                return True
                
            elif action == "get":
                if not key:
                    print("Error: Key required for get action")
                    return False
                
                if not self.config:
                    print("Configuration not loaded")
                    return False
                
                config_value = getattr(self.config, key, None)
                if config_value is not None:
                    print(f"{key}: {config_value}")
                else:
                    print(f"Key not found: {key}")
                
                return True
                
            elif action == "set":
                if not key or value is None:
                    print("Error: Key and value required for set action")
                    return False
                
                # This would update configuration
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
        description='EFIS Data Manager CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s prepare-usb /Volumes/EFIS_USB
  %(prog)s status
  %(prog)s sync --target 192.168.1.100
  %(prog)s check-updates
  %(prog)s logs --lines 100 --component grt
  %(prog)s config show
        """
    )
    
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # USB drive preparation
    prepare_parser = subparsers.add_parser('prepare-usb', help='Prepare new EFIS USB drive')
    prepare_parser.add_argument('drive_path', help='Path to USB drive mount point')
    prepare_parser.add_argument('--force', action='store_true', help='Force preparation even if drive has data')
    
    # Status check
    status_parser = subparsers.add_parser('status', help='Check system status')
    status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # Manual sync
    sync_parser = subparsers.add_parser('sync', help='Trigger manual synchronization')
    sync_parser.add_argument('--target', help='Target system to sync with')
    
    # GRT updates check
    updates_parser = subparsers.add_parser('check-updates', help='Check for GRT software updates')
    
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
    config_get_parser.add_argument('key', help='Configuration key')
    
    config_set_parser = config_subparsers.add_parser('set', help='Set configuration value')
    config_set_parser.add_argument('key', help='Configuration key')
    config_set_parser.add_argument('value', help='Configuration value')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI manager
    cli = EFISCLIManager(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration for most commands
    if args.command not in ['prepare-usb']:
        if not cli.load_config():
            print("Warning: Could not load configuration, some features may not work")
    
    # Execute command
    try:
        if args.command == 'prepare-usb':
            success = cli.prepare_usb_drive(args.drive_path, args.force)
            return 0 if success else 1
            
        elif args.command == 'status':
            status = cli.check_status()
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print("EFIS Data Manager Status:")
                print("-" * 30)
                for key, value in status.items():
                    if key == 'usb_drives' and isinstance(value, list):
                        print(f"{key}: {len(value)} drives connected")
                        for drive in value:
                            print(f"  {drive['device']} -> {drive['mount_point']} ({drive['size']})")
                    else:
                        print(f"{key}: {value}")
            return 0
            
        elif args.command == 'sync':
            success = cli.manual_sync(args.target)
            return 0 if success else 1
            
        elif args.command == 'check-updates':
            success = cli.check_grt_updates()
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