#!/usr/bin/env python3
"""
macOS installer for EFIS Data Manager.
Handles launchd daemon configuration, dependency installation, and setup.
"""

import os
import sys
import subprocess
import shutil
import logging
import plistlib
from pathlib import Path
from typing import List, Dict, Any
import argparse
import pwd
import grp

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config.config_manager import ConfigManager


class MacOSInstaller:
    """Handles macOS installation and launchd daemon configuration."""
    
    def __init__(self, install_dir: str = None, config_file: str = None, user: str = None):
        """
        Initialize macOS installer.
        
        Args:
            install_dir: Installation directory (default: /usr/local/efis-data-manager)
            config_file: Configuration file path
            user: User to run daemon as (default: current user)
        """
        self.install_dir = Path(install_dir or "/usr/local/efis-data-manager")
        self.config_file = config_file
        self.user = user or os.getenv("USER", "mwalker")
        self.logger = self._setup_logging()
        
        # Get user info
        try:
            self.user_info = pwd.getpwnam(self.user)
            self.user_home = Path(self.user_info.pw_dir)
        except KeyError:
            raise ValueError(f"User not found: {self.user}")
        
        # Installation paths
        self.daemon_script = self.install_dir / "efis_daemon.py"
        self.config_dir = self.install_dir / "config"
        self.logs_dir = self.user_home / "Library" / "Logs" / "EFIS"
        self.launchd_plist = Path("/Library/LaunchDaemons/com.efis.datamanager.plist")
        self.user_launchd_plist = self.user_home / "Library" / "LaunchAgents" / "com.efis.datamanager.plist"
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for installer."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('efis_install.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def check_prerequisites(self) -> bool:
        """
        Check if all prerequisites are met.
        
        Returns:
            True if all prerequisites are satisfied
        """
        self.logger.info("Checking prerequisites...")
        
        # Check macOS version
        try:
            result = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True)
            version = result.stdout.strip()
            major_version = int(version.split('.')[0])
            
            if major_version < 10:
                self.logger.error("macOS 10.15 or higher is required")
                return False
                
        except Exception as e:
            self.logger.warning(f"Cannot determine macOS version: {e}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.logger.error("Python 3.8 or higher is required")
            return False
        
        # Check if running with appropriate privileges
        if os.geteuid() != 0 and self.install_dir.parts[1] != "Users":
            self.logger.error("Installer must be run with sudo for system-wide installation")
            return False
        
        # Check Homebrew (optional)
        homebrew_path = Path("/opt/homebrew/bin/brew")
        if not homebrew_path.exists():
            homebrew_path = Path("/usr/local/bin/brew")
        
        if not homebrew_path.exists():
            self.logger.warning("Homebrew not found - some dependencies may need manual installation")
        
        self.logger.info("Prerequisites check completed")
        return True
    
    def install_dependencies(self) -> bool:
        """
        Install required dependencies.
        
        Returns:
            True if installation successful
        """
        self.logger.info("Installing dependencies...")
        
        try:
            # Install Python packages
            self._install_python_packages()
            
            # Install system dependencies via Homebrew if available
            self._install_system_dependencies()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def _install_python_packages(self) -> None:
        """Install required Python packages."""
        self.logger.info("Installing Python packages...")
        
        requirements = [
            "pyyaml>=6.0",
            "keyring>=24.0.0",
            "cryptography>=41.0.0",
            "requests>=2.31.0",
            "psutil>=5.9.0",
            "beautifulsoup4>=4.12.0",
            "lxml>=4.9.0"
        ]
        
        for package in requirements:
            self.logger.info(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Failed to install {package}: {result.stderr}")
    
    def _install_system_dependencies(self) -> None:
        """Install system dependencies via Homebrew."""
        homebrew_path = self._find_homebrew()
        if not homebrew_path:
            self.logger.warning("Homebrew not found - skipping system dependencies")
            return
        
        self.logger.info("Installing system dependencies via Homebrew...")
        
        # Dependencies that might be useful
        dependencies = [
            "rsync",  # For file synchronization
            "wget",   # For downloading files
        ]
        
        for dep in dependencies:
            try:
                result = subprocess.run([
                    str(homebrew_path), "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info(f"Installed {dep}")
                else:
                    self.logger.warning(f"Failed to install {dep}: {result.stderr}")
                    
            except Exception as e:
                self.logger.warning(f"Error installing {dep}: {e}")
    
    def _find_homebrew(self) -> Path:
        """Find Homebrew installation."""
        candidates = [
            Path("/opt/homebrew/bin/brew"),  # Apple Silicon
            Path("/usr/local/bin/brew")      # Intel
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        return None
    
    def create_directories(self) -> None:
        """Create necessary directories."""
        self.logger.info("Creating directories...")
        
        directories = [
            self.install_dir,
            self.config_dir,
            self.logs_dir,
            self.user_home / "Library" / "LaunchAgents"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Set appropriate ownership for user directories
            if str(directory).startswith(str(self.user_home)):
                shutil.chown(directory, user=self.user)
            
            self.logger.info(f"Created directory: {directory}")
    
    def copy_files(self) -> None:
        """Copy application files to installation directory."""
        self.logger.info("Copying application files...")
        
        source_dir = Path(__file__).parent
        
        # Files to copy
        files_to_copy = [
            ("src/efis_macos/daemon.py", "efis_daemon.py"),
            ("src/efis_macos/grt_scraper.py", "grt_scraper.py"),
            ("src/efis_macos/download_manager.py", "download_manager.py"),
            ("src/efis_macos/usb_drive_processor.py", "usb_drive_processor.py"),
            ("src/efis_macos/usb_drive_updater.py", "usb_drive_updater.py"),
            ("src/efis_macos/efis_file_processor.py", "efis_file_processor.py"),
            ("src/efis_macos/service_manager.py", "service_manager.py"),
            ("src/efis_macos/config.py", "config.py"),
            ("src/efis_macos/logging_config.py", "logging_config.py"),
            ("efis_cli.py", "efis_cli.py"),
            ("daemon_manager.py", "daemon_manager.py"),
            ("requirements.txt", "requirements.txt")
        ]
        
        for src_file, dest_file in files_to_copy:
            src_path = source_dir / src_file
            dest_path = self.install_dir / dest_file
            
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
                # Make executable if it's a Python script
                if dest_file.endswith('.py'):
                    dest_path.chmod(0o755)
                self.logger.info(f"Copied {src_file} to {dest_file}")
            else:
                self.logger.warning(f"Source file not found: {src_file}")
        
        # Copy shared modules
        shared_src = source_dir.parent / "shared"
        shared_dest = self.install_dir / "shared"
        
        if shared_src.exists():
            shutil.copytree(shared_src, shared_dest, dirs_exist_ok=True)
            self.logger.info("Copied shared modules")
    
    def setup_configuration(self) -> None:
        """Setup configuration files."""
        self.logger.info("Setting up configuration...")
        
        # Create configuration manager
        config_manager = ConfigManager(environment="production")
        
        # Use provided config file or create default
        if self.config_file and Path(self.config_file).exists():
            # Copy provided config
            dest_config = self.config_dir / "efis_config.yaml"
            shutil.copy2(self.config_file, dest_config)
            self.logger.info(f"Copied configuration from {self.config_file}")
        else:
            # Create default configuration
            default_config = self.config_dir / "efis_config.yaml"
            config_manager._create_default_config(default_config)
            
            # Update paths for current user
            config_manager.config_path = str(default_config)
            config_manager.load_config()
            
            # Update user-specific paths
            dropbox_path = self.user_home / "Library" / "CloudStorage" / "Dropbox" / "Flying"
            config_manager.set("macos.archivePath", str(dropbox_path / "EFIS-USB"))
            config_manager.set("macos.demoPath", str(dropbox_path / "EFIS-DEMO"))
            config_manager.set("macos.logbookPath", str(dropbox_path / "Logbooks"))
            
            config_manager.save_config()
            self.logger.info("Created default configuration with user-specific paths")
        
        # Set appropriate ownership
        config_file = self.config_dir / "efis_config.yaml"
        if config_file.exists():
            shutil.chown(config_file, user=self.user)
        
        # Validate configuration
        try:
            config_manager.config_path = str(self.config_dir / "efis_config.yaml")
            config_manager.load_config()
            if config_manager.validate_config():
                self.logger.info("Configuration validation passed")
            else:
                self.logger.warning("Configuration validation failed - manual review required")
        except Exception as e:
            self.logger.warning(f"Configuration validation error: {e}")
    
    def create_launchd_plist(self, system_wide: bool = False) -> bool:
        """
        Create launchd plist file.
        
        Args:
            system_wide: If True, create system-wide daemon, otherwise user agent
            
        Returns:
            True if plist creation successful
        """
        self.logger.info(f"Creating launchd plist ({'system-wide' if system_wide else 'user agent'})...")
        
        try:
            plist_data = {
                "Label": "com.efis.datamanager",
                "ProgramArguments": [
                    sys.executable,
                    str(self.daemon_script)
                ],
                "WorkingDirectory": str(self.install_dir),
                "StandardOutPath": str(self.logs_dir / "efis_daemon.log"),
                "StandardErrorPath": str(self.logs_dir / "efis_daemon_error.log"),
                "RunAtLoad": True,
                "KeepAlive": {
                    "SuccessfulExit": False,
                    "Crashed": True
                },
                "ThrottleInterval": 10,
                "EnvironmentVariables": {
                    "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                    "PYTHONPATH": str(self.install_dir)
                }
            }
            
            if system_wide:
                plist_data["UserName"] = self.user
                plist_data["GroupName"] = "staff"
                plist_path = self.launchd_plist
            else:
                plist_path = self.user_launchd_plist
            
            # Write plist file
            with open(plist_path, 'wb') as f:
                plistlib.dump(plist_data, f)
            
            # Set appropriate permissions
            plist_path.chmod(0o644)
            if system_wide:
                shutil.chown(plist_path, user="root", group="wheel")
            else:
                shutil.chown(plist_path, user=self.user)
            
            self.logger.info(f"Created launchd plist: {plist_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create launchd plist: {e}")
            return False
    
    def load_daemon(self, system_wide: bool = False) -> bool:
        """
        Load daemon with launchctl.
        
        Args:
            system_wide: If True, load system-wide daemon
            
        Returns:
            True if daemon loading successful
        """
        self.logger.info("Loading daemon with launchctl...")
        
        try:
            plist_path = self.launchd_plist if system_wide else self.user_launchd_plist
            
            # Load the daemon
            if system_wide:
                cmd = ["sudo", "launchctl", "load", str(plist_path)]
            else:
                cmd = ["launchctl", "load", str(plist_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Daemon loaded successfully")
                return True
            else:
                self.logger.error(f"Failed to load daemon: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading daemon: {e}")
            return False
    
    def create_cli_symlink(self) -> None:
        """Create symlink for CLI tool."""
        self.logger.info("Creating CLI symlink...")
        
        try:
            cli_source = self.install_dir / "efis_cli.py"
            cli_target = Path("/usr/local/bin/efis")
            
            # Remove existing symlink if it exists
            if cli_target.exists() or cli_target.is_symlink():
                cli_target.unlink()
            
            # Create new symlink
            cli_target.symlink_to(cli_source)
            cli_target.chmod(0o755)
            
            self.logger.info(f"Created CLI symlink: {cli_target} -> {cli_source}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create CLI symlink: {e}")
    
    def create_uninstaller(self) -> None:
        """Create uninstaller script."""
        self.logger.info("Creating uninstaller...")
        
        uninstall_script = self.install_dir / "uninstall.py"
        uninstall_content = f'''#!/usr/bin/env python3
"""
EFIS Data Manager Uninstaller for macOS.
"""

import subprocess
import shutil
from pathlib import Path
import sys

def uninstall():
    """Uninstall EFIS Data Manager."""
    print("Uninstalling EFIS Data Manager...")
    
    # Unload and remove launchd plist
    plist_paths = [
        Path("/Library/LaunchDaemons/com.efis.datamanager.plist"),
        Path.home() / "Library" / "LaunchAgents" / "com.efis.datamanager.plist"
    ]
    
    for plist_path in plist_paths:
        if plist_path.exists():
            try:
                # Unload daemon
                if "LaunchDaemons" in str(plist_path):
                    subprocess.run(["sudo", "launchctl", "unload", str(plist_path)], capture_output=True)
                else:
                    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
                
                # Remove plist file
                plist_path.unlink()
                print(f"Removed launchd plist: {{plist_path}}")
            except Exception as e:
                print(f"Error removing plist {{plist_path}}: {{e}}")
    
    # Remove installation directory
    try:
        install_dir = Path("{self.install_dir}")
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print(f"Removed installation directory: {{install_dir}}")
    except Exception as e:
        print(f"Error removing installation directory: {{e}}")
    
    # Remove CLI symlink
    try:
        cli_symlink = Path("/usr/local/bin/efis")
        if cli_symlink.exists():
            cli_symlink.unlink()
            print("Removed CLI symlink")
    except Exception as e:
        print(f"Error removing CLI symlink: {{e}}")
    
    print("Uninstallation completed")

if __name__ == "__main__":
    uninstall()
'''
        
        with open(uninstall_script, 'w', encoding='utf-8') as f:
            f.write(uninstall_content)
        
        uninstall_script.chmod(0o755)
        self.logger.info(f"Uninstaller created: {uninstall_script}")
    
    def install(self, system_wide: bool = False) -> bool:
        """
        Run complete installation process.
        
        Args:
            system_wide: If True, install as system-wide daemon
            
        Returns:
            True if installation successful
        """
        try:
            self.logger.info("Starting EFIS Data Manager installation...")
            
            # Check prerequisites
            if not self.check_prerequisites():
                return False
            
            # Install dependencies
            if not self.install_dependencies():
                return False
            
            # Create directories
            self.create_directories()
            
            # Copy files
            self.copy_files()
            
            # Setup configuration
            self.setup_configuration()
            
            # Create launchd plist
            if not self.create_launchd_plist(system_wide):
                return False
            
            # Load daemon
            if not self.load_daemon(system_wide):
                self.logger.warning("Daemon loading failed - you may need to load it manually")
            
            # Create CLI symlink
            self.create_cli_symlink()
            
            # Create uninstaller
            self.create_uninstaller()
            
            self.logger.info("Installation completed successfully!")
            self.logger.info(f"Installation directory: {self.install_dir}")
            self.logger.info(f"Configuration: {self.config_dir / 'efis_config.yaml'}")
            self.logger.info(f"Logs: {self.logs_dir}")
            
            if system_wide:
                self.logger.info("System-wide daemon installed")
                self.logger.info("Use 'sudo launchctl start com.efis.datamanager' to start")
            else:
                self.logger.info("User agent installed")
                self.logger.info("Use 'launchctl start com.efis.datamanager' to start")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False


def main():
    """Main installer entry point."""
    parser = argparse.ArgumentParser(description="EFIS Data Manager macOS Installer")
    parser.add_argument(
        "--install-dir", "-d",
        help="Installation directory (default: /usr/local/efis-data-manager)"
    )
    parser.add_argument(
        "--config", "-c",
        help="Configuration file to use"
    )
    parser.add_argument(
        "--user", "-u",
        help="User to run daemon as (default: current user)"
    )
    parser.add_argument(
        "--system-wide", "-s",
        action="store_true",
        help="Install as system-wide daemon (requires sudo)"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall EFIS Data Manager"
    )
    
    args = parser.parse_args()
    
    if args.uninstall:
        # Run uninstaller
        uninstall_script = Path(args.install_dir or "/usr/local/efis-data-manager") / "uninstall.py"
        if uninstall_script.exists():
            subprocess.run([sys.executable, str(uninstall_script)])
        else:
            print("Uninstaller not found")
        return
    
    # Run installer
    installer = MacOSInstaller(args.install_dir, args.config, args.user)
    success = installer.install(args.system_wide)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()