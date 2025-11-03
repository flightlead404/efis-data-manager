"""
Installation script for EFIS Data Manager Windows Service.
Handles service installation, removal, and management.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from windows_service import EFISDataManagerService, ServiceManager


def setup_logging():
    """Setup logging for installation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('service_install.log')
        ]
    )
    return logging.getLogger(__name__)


def print_usage():
    """Print usage information."""
    print("EFIS Data Manager Service Installer")
    print("Usage:")
    print("  python install_service.py install    - Install the service")
    print("  python install_service.py remove     - Remove the service")
    print("  python install_service.py start      - Start the service")
    print("  python install_service.py stop       - Stop the service")
    print("  python install_service.py restart    - Restart the service")
    print("  python install_service.py status     - Show service status")


def main():
    """Main installation script."""
    logger = setup_logging()
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
        
    command = sys.argv[1].lower()
    service_manager = ServiceManager(logger)
    
    try:
        if command == 'install':
            logger.info("Installing EFIS Data Manager Service...")
            
            # Check if running as administrator
            if not os.access(sys.executable, os.W_OK):
                logger.error("Installation requires administrator privileges")
                logger.error("Please run this script as Administrator")
                sys.exit(1)
                
            if service_manager.install_service():
                logger.info("Service installed successfully")
                logger.info("You can now start the service with: python install_service.py start")
            else:
                logger.error("Service installation failed")
                sys.exit(1)
                
        elif command == 'remove':
            logger.info("Removing EFIS Data Manager Service...")
            
            if service_manager.remove_service():
                logger.info("Service removed successfully")
            else:
                logger.error("Service removal failed")
                sys.exit(1)
                
        elif command == 'start':
            logger.info("Starting EFIS Data Manager Service...")
            
            if service_manager.start_service():
                logger.info("Service started successfully")
            else:
                logger.error("Service start failed")
                sys.exit(1)
                
        elif command == 'stop':
            logger.info("Stopping EFIS Data Manager Service...")
            
            if service_manager.stop_service():
                logger.info("Service stopped successfully")
            else:
                logger.error("Service stop failed")
                sys.exit(1)
                
        elif command == 'restart':
            logger.info("Restarting EFIS Data Manager Service...")
            
            # Stop first
            service_manager.stop_service()
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start again
            if service_manager.start_service():
                logger.info("Service restarted successfully")
            else:
                logger.error("Service restart failed")
                sys.exit(1)
                
        elif command == 'status':
            status = service_manager.get_service_status()
            logger.info(f"Service status: {status}")
            
        else:
            logger.error(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()