"""
Command-line interface for EFIS Data Manager drive operations.
Provides tools for testing and managing virtual drive operations.
"""

import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from imdisk_wrapper import VirtualDriveManager, ImDiskWrapper, MountResult
from drive_monitor import DriveMonitor, DriveHealthChecker, MonitoringState


def setup_logging(verbose: bool = False):
    """Setup logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def load_config():
    """Load configuration from file."""
    config_paths = [
        Path.cwd() / 'config' / 'windows-config.json',
        Path(__file__).parent / 'config' / 'windows-config.json',
        Path('C:/Scripts/efis-config.json')
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
                
    # Return default config if no file found
    return {
        "virtualDrive": {
            "vhdPath": "C:\\Users\\fligh\\OneDrive\\Desktop\\virtualEFISUSB.vhd",
            "mountTool": "C:\\Program Files\\ImDisk\\MountImg.exe",
            "driveLetter": "E:"
        },
        "monitoring": {
            "checkInterval": 300,
            "remountRetryDelay": 60
        }
    }


def cmd_status(args, logger):
    """Show drive status."""
    config = load_config()
    drive_config = config['virtualDrive']
    
    # Create drive manager
    manager_config = {
        'virtualDriveFile': drive_config['vhdPath'],
        'mountTool': drive_config['mountTool'],
        'driveLetter': drive_config['driveLetter']
    }
    
    drive_manager = VirtualDriveManager(manager_config, logger)
    
    # Get drive status
    drive_info = drive_manager.check_drive_status()
    
    if drive_info:
        print(f"Drive Status: MOUNTED")
        print(f"Drive Letter: {drive_info.drive_letter}")
        print(f"VHD Path: {drive_info.vhd_path}")
        print(f"File System: {drive_info.file_system or 'Unknown'}")
        
        if drive_info.size_bytes:
            size_gb = drive_info.size_bytes / (1024**3)
            print(f"Total Size: {size_gb:.2f} GB")
            
        if drive_info.free_space_bytes:
            free_gb = drive_info.free_space_bytes / (1024**3)
            print(f"Free Space: {free_gb:.2f} GB")
    else:
        print("Drive Status: NOT MOUNTED")
        
    return 0


def cmd_mount(args, logger):
    """Mount the virtual drive."""
    config = load_config()
    drive_config = config['virtualDrive']
    
    manager_config = {
        'virtualDriveFile': drive_config['vhdPath'],
        'mountTool': drive_config['mountTool'],
        'driveLetter': drive_config['driveLetter']
    }
    
    drive_manager = VirtualDriveManager(manager_config, logger)
    
    print(f"Mounting {drive_config['vhdPath']} to {drive_config['driveLetter']}...")
    
    if drive_manager.ensure_drive_mounted():
        print("Mount successful!")
        return 0
    else:
        print("Mount failed!")
        return 1


def cmd_unmount(args, logger):
    """Unmount the virtual drive."""
    config = load_config()
    drive_config = config['virtualDrive']
    
    manager_config = {
        'virtualDriveFile': drive_config['vhdPath'],
        'mountTool': drive_config['mountTool'],
        'driveLetter': drive_config['driveLetter']
    }
    
    drive_manager = VirtualDriveManager(manager_config, logger)
    
    print(f"Unmounting {drive_config['driveLetter']}...")
    
    if drive_manager.unmount_drive(force=args.force):
        print("Unmount successful!")
        return 0
    else:
        print("Unmount failed!")
        return 1


def cmd_health(args, logger):
    """Perform health check."""
    config = load_config()
    drive_config = config['virtualDrive']
    
    manager_config = {
        'virtualDriveFile': drive_config['vhdPath'],
        'mountTool': drive_config['mountTool'],
        'driveLetter': drive_config['driveLetter']
    }
    
    drive_manager = VirtualDriveManager(manager_config, logger)
    health_checker = DriveHealthChecker(drive_manager, logger)
    
    print("Performing health check...")
    results = health_checker.perform_health_check()
    
    print(f"\nHealth Check Results ({results['timestamp']})")
    print(f"Overall Health: {results['overall_health'].upper()}")
    print("\nDetailed Results:")
    
    for check_name, check_result in results.get('checks', {}).items():
        status_symbol = {
            'pass': '✓',
            'warning': '⚠',
            'fail': '✗',
            'error': '!',
            'unknown': '?'
        }.get(check_result['status'], '?')
        
        print(f"  {status_symbol} {check_name}: {check_result['details']}")
        
    return 0 if results['overall_health'] in ['healthy', 'degraded'] else 1


def cmd_monitor(args, logger):
    """Start drive monitoring."""
    config = load_config()
    drive_config = config['virtualDrive']
    monitor_config = config.get('monitoring', {})
    
    manager_config = {
        'virtualDriveFile': drive_config['vhdPath'],
        'mountTool': drive_config['mountTool'],
        'driveLetter': drive_config['driveLetter']
    }
    
    drive_manager = VirtualDriveManager(manager_config, logger)
    drive_monitor = DriveMonitor(drive_manager, monitor_config, logger)
    
    # Setup callbacks for console output
    def on_mount_success(drive_info):
        print(f"[{datetime.now()}] Drive mounted successfully: {drive_info.drive_letter}")
        
    def on_mount_failure(error_msg):
        print(f"[{datetime.now()}] Mount failed: {error_msg}")
        
    def on_drive_lost():
        print(f"[{datetime.now()}] Drive connection lost!")
        
    def on_drive_recovered(drive_info):
        print(f"[{datetime.now()}] Drive recovered: {drive_info.drive_letter}")
        
    drive_monitor.on_mount_success = on_mount_success
    drive_monitor.on_mount_failure = on_mount_failure
    drive_monitor.on_drive_lost = on_drive_lost
    drive_monitor.on_drive_recovered = on_drive_recovered
    
    print(f"Starting drive monitor (check interval: {monitor_config.get('checkInterval', 300)}s)")
    print("Press Ctrl+C to stop monitoring...")
    
    try:
        if drive_monitor.start():
            # Monitor loop
            while True:
                try:
                    import time
                    time.sleep(1)
                    
                    # Print stats periodically
                    if args.stats:
                        stats = drive_monitor.get_stats()
                        if stats.total_checks > 0 and stats.total_checks % 10 == 0:
                            print(f"Stats: {stats.total_checks} checks, "
                                f"{stats.success_rate:.1f}% success rate")
                            
                except KeyboardInterrupt:
                    break
                    
        else:
            print("Failed to start drive monitor")
            return 1
            
    finally:
        print("\nStopping drive monitor...")
        drive_monitor.stop()
        
        # Print final stats
        stats = drive_monitor.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  Total Checks: {stats.total_checks}")
        print(f"  Success Rate: {stats.success_rate:.1f}%")
        print(f"  Mount Attempts: {stats.mount_attempts}")
        print(f"  Mount Success Rate: {stats.mount_success_rate:.1f}%")
        print(f"  Uptime: {stats.uptime}")
        
    return 0


def cmd_list(args, logger):
    """List all mounted ImDisk drives."""
    config = load_config()
    drive_config = config['virtualDrive']
    
    imdisk = ImDiskWrapper(drive_config['mountTool'], logger)
    
    print("Mounted ImDisk drives:")
    drives = imdisk.list_mounted_drives()
    
    if not drives:
        print("  No ImDisk drives found")
    else:
        for drive in drives:
            print(f"  {drive.drive_letter} -> {drive.vhd_path}")
            if drive.size_bytes:
                size_gb = drive.size_bytes / (1024**3)
                free_gb = (drive.free_space_bytes or 0) / (1024**3)
                print(f"    Size: {size_gb:.2f} GB, Free: {free_gb:.2f} GB")
                
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EFIS Data Manager Drive Operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show drive status')
    
    # Mount command
    subparsers.add_parser('mount', help='Mount virtual drive')
    
    # Unmount command
    unmount_parser = subparsers.add_parser('unmount', help='Unmount virtual drive')
    unmount_parser.add_argument('-f', '--force', action='store_true',
                               help='Force unmount even if drive is in use')
    
    # Health command
    subparsers.add_parser('health', help='Perform health check')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start drive monitoring')
    monitor_parser.add_argument('-s', '--stats', action='store_true',
                               help='Show periodic statistics')
    
    # List command
    subparsers.add_parser('list', help='List all mounted ImDisk drives')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Execute command
    commands = {
        'status': cmd_status,
        'mount': cmd_mount,
        'unmount': cmd_unmount,
        'health': cmd_health,
        'monitor': cmd_monitor,
        'list': cmd_list
    }
    
    try:
        return commands[args.command](args, logger)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())