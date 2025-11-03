#!/usr/bin/env python3
"""
Command-line utility for managing the EFIS Data Manager macOS daemon.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from efis_macos.daemon import EFISDaemon
from efis_macos.service_manager import LaunchdServiceManager
from efis_macos.config import ConfigManager


def setup_basic_logging():
    """Set up basic logging for the CLI utility."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )


def cmd_install(args):
    """Install the daemon service."""
    print("Installing EFIS Data Manager daemon...")
    
    service_manager = LaunchdServiceManager()
    
    if service_manager.install_service():
        print("✓ Daemon service installed successfully")
        print(f"  Service file: {service_manager.plist_path}")
        
        # Create default config if it doesn't exist
        config_manager = ConfigManager(args.config)
        if not Path(config_manager.config_path).exists():
            config_manager.save_default_config()
            print(f"✓ Created default configuration: {config_manager.config_path}")
        
        return True
    else:
        print("✗ Failed to install daemon service")
        return False


def cmd_uninstall(args):
    """Uninstall the daemon service."""
    print("Uninstalling EFIS Data Manager daemon...")
    
    service_manager = LaunchdServiceManager()
    
    if service_manager.uninstall_service():
        print("✓ Daemon service uninstalled successfully")
        return True
    else:
        print("✗ Failed to uninstall daemon service")
        return False


def cmd_start(args):
    """Start the daemon service."""
    print("Starting EFIS Data Manager daemon...")
    
    service_manager = LaunchdServiceManager()
    
    if service_manager.start_service():
        print("✓ Daemon service started")
        return True
    else:
        print("✗ Failed to start daemon service")
        return False


def cmd_stop(args):
    """Stop the daemon service."""
    print("Stopping EFIS Data Manager daemon...")
    
    service_manager = LaunchdServiceManager()
    
    if service_manager.stop_service():
        print("✓ Daemon service stopped")
        return True
    else:
        print("✗ Failed to stop daemon service")
        return False


def cmd_restart(args):
    """Restart the daemon service."""
    print("Restarting EFIS Data Manager daemon...")
    
    service_manager = LaunchdServiceManager()
    
    # Stop first
    service_manager.stop_service()
    
    # Start again
    if service_manager.start_service():
        print("✓ Daemon service restarted")
        return True
    else:
        print("✗ Failed to restart daemon service")
        return False


def cmd_status(args):
    """Show daemon service status."""
    service_manager = LaunchdServiceManager()
    status = service_manager.get_service_status()
    
    print("EFIS Data Manager Daemon Status:")
    print(f"  Service loaded: {'Yes' if status.get('loaded', False) else 'No'}")
    
    if status.get('loaded'):
        pid = status.get('pid')
        if pid:
            print(f"  Running (PID): {pid}")
        else:
            print("  Not running")
        
        exit_code = status.get('last_exit_code')
        if exit_code:
            print(f"  Last exit code: {exit_code}")
    
    if status.get('error'):
        print(f"  Error: {status['error']}")
    
    return True


def cmd_run(args):
    """Run the daemon in foreground mode."""
    print("Running EFIS Data Manager daemon in foreground...")
    
    daemon = EFISDaemon(args.config)
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        daemon.stop()
    
    return True


def cmd_create_config(args):
    """Create a default configuration file."""
    config_manager = ConfigManager(args.config)
    config_manager.save_default_config()
    print(f"✓ Created default configuration: {config_manager.config_path}")
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='EFIS Data Manager macOS Daemon Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s install          Install the daemon service
  %(prog)s start            Start the daemon
  %(prog)s status           Show daemon status
  %(prog)s run              Run daemon in foreground
  %(prog)s create-config    Create default configuration
        """
    )
    
    parser.add_argument('--config', '-c', 
                       help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    subparsers.add_parser('install', help='Install daemon service')
    
    # Uninstall command
    subparsers.add_parser('uninstall', help='Uninstall daemon service')
    
    # Start command
    subparsers.add_parser('start', help='Start daemon service')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop daemon service')
    
    # Restart command
    subparsers.add_parser('restart', help='Restart daemon service')
    
    # Status command
    subparsers.add_parser('status', help='Show daemon status')
    
    # Run command
    subparsers.add_parser('run', help='Run daemon in foreground')
    
    # Create config command
    subparsers.add_parser('create-config', help='Create default configuration file')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_basic_logging()
    
    # Command dispatch
    commands = {
        'install': cmd_install,
        'uninstall': cmd_uninstall,
        'start': cmd_start,
        'stop': cmd_stop,
        'restart': cmd_restart,
        'status': cmd_status,
        'run': cmd_run,
        'create-config': cmd_create_config,
    }
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command not in commands:
        print(f"Unknown command: {args.command}")
        return 1
    
    try:
        success = commands[args.command](args)
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())