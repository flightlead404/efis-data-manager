"""
Service management utilities for macOS launchd integration.
"""

import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any


class LaunchdServiceManager:
    """Manages launchd service installation and control."""
    
    def __init__(self, service_name: str = "com.efis-data-manager.daemon"):
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)
        
        # Paths
        self.user_agents_dir = Path.home() / "Library" / "LaunchAgents"
        self.plist_path = self.user_agents_dir / f"{service_name}.plist"
        self.source_plist = Path(__file__).parent.parent.parent / "config" / f"{service_name}.plist"
    
    def install_service(self) -> bool:
        """Install the launchd service."""
        try:
            # Ensure LaunchAgents directory exists
            self.user_agents_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy plist file
            if not self.source_plist.exists():
                self.logger.error(f"Source plist file not found: {self.source_plist}")
                return False
            
            shutil.copy2(self.source_plist, self.plist_path)
            self.logger.info(f"Copied service plist to: {self.plist_path}")
            
            # Set proper permissions
            os.chmod(self.plist_path, 0o644)
            
            # Load the service
            return self.load_service()
            
        except Exception as e:
            self.logger.error(f"Failed to install service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the launchd service."""
        try:
            # Unload service first
            self.unload_service()
            
            # Remove plist file
            if self.plist_path.exists():
                self.plist_path.unlink()
                self.logger.info(f"Removed service plist: {self.plist_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall service: {e}")
            return False
    
    def load_service(self) -> bool:
        """Load the service with launchctl."""
        try:
            result = subprocess.run(
                ["launchctl", "load", str(self.plist_path)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Service loaded successfully: {self.service_name}")
                return True
            else:
                self.logger.error(f"Failed to load service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading service: {e}")
            return False
    
    def unload_service(self) -> bool:
        """Unload the service with launchctl."""
        try:
            result = subprocess.run(
                ["launchctl", "unload", str(self.plist_path)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Service unloaded successfully: {self.service_name}")
                return True
            else:
                # Service might not be loaded, which is okay for unload
                self.logger.debug(f"Service unload result: {result.stderr}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error unloading service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the service."""
        try:
            result = subprocess.run(
                ["launchctl", "start", self.service_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Service started: {self.service_name}")
                return True
            else:
                self.logger.error(f"Failed to start service: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the service."""
        try:
            result = subprocess.run(
                ["launchctl", "stop", self.service_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                self.logger.info(f"Service stopped: {self.service_name}")
                return True
            else:
                self.logger.debug(f"Service stop result: {result.stderr}")
                return True  # Service might already be stopped
                
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of the service."""
        try:
            result = subprocess.run(
                ["launchctl", "list", self.service_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse launchctl output
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 1:
                    parts = lines[0].split('\t')
                    if len(parts) >= 3:
                        return {
                            'loaded': True,
                            'pid': parts[0] if parts[0] != '-' else None,
                            'last_exit_code': parts[1] if parts[1] != '-' else None,
                            'label': parts[2]
                        }
            
            return {'loaded': False}
            
        except Exception as e:
            self.logger.error(f"Error getting service status: {e}")
            return {'loaded': False, 'error': str(e)}
    
    def is_service_running(self) -> bool:
        """Check if the service is currently running."""
        status = self.get_service_status()
        return status.get('loaded', False) and status.get('pid') is not None