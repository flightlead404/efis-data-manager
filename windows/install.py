#!/usr/bin/env python3
"""
Windows installer for EFIS Data Manager.
Handles service registration, dependency installation, and configuration setup.
"""

import os
import sys
import subprocess
import winreg
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
import argparse
import json

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config.config_manager import ConfigManager


class WindowsInstaller:
    """Handles Windows installation and service registration."""
    
    def __init__(self, install_dir: str = None, config_file: str = None):
        """
        Initialize Windows installer.
        
        Args:
            install_dir: Installation directory (default: C:\\Program Files\\EFIS Data Manager)
            config_file: Configuration file path
        """
        self.install_dir = Path(install_dir or "C:\\Program Files\\EFIS Data Manager")
        self.config_file = config_file
        self.logger = self._setup_logging()
        
        # Installation paths
        self.service_exe = self.install_dir / "efis_service.exe"
        self.config_dir = self.install_dir / "config"
        self.logs_dir = self.install_dir / "logs"
        self.scripts_dir = Path("C:\\Scripts")
        
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
        
        # Check if running as administrator
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.logger.error("Installer must be run as administrator")
                return False
        except Exception as e:
            self.logger.error(f"Cannot check administrator privileges: {e}")
            return False
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.logger.error("Python 3.8 or higher is required")
            return False
        
        # Check for ImDisk
        imdisk_path = Path("C:\\Program Files\\ImDisk\\MountImg.exe")
        if not imdisk_path.exists():
            self.logger.warning("ImDisk not found - will attempt to install")
        
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
            
            # Install ImDisk if not present
            if not self._check_imdisk():
                self._install_imdisk()
            
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
            "pywin32>=306"
        ]
        
        for package in requirements:
            self.logger.info(f"Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Failed to install {package}: {result.stderr}")
    
    def _check_imdisk(self) -> bool:
        """Check if ImDisk is installed."""
        imdisk_path = Path("C:\\Program Files\\ImDisk\\MountImg.exe")
        return imdisk_path.exists()
    
    def _install_imdisk(self) -> None:
        """Install ImDisk virtual disk driver."""
        self.logger.info("Installing ImDisk...")
        
        # Download ImDisk installer
        import requests
        
        imdisk_url = "https://sourceforge.net/projects/imdisk-toolkit/files/latest/download"
        installer_path = Path.cwd() / "imdisk_installer.exe"
        
        try:
            response = requests.get(imdisk_url, stream=True)
            response.raise_for_status()
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Run installer silently
            result = subprocess.run([
                str(installer_path), "/S"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ImDisk installation failed: {result.stderr}")
            
            self.logger.info("ImDisk installed successfully")
            
        finally:
            # Clean up installer
            if installer_path.exists():
                installer_path.unlink()
    
    def create_directories(self) -> None:
        """Create necessary directories."""
        self.logger.info("Creating directories...")
        
        directories = [
            self.install_dir,
            self.config_dir,
            self.logs_dir,
            self.scripts_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {directory}")
    
    def copy_files(self) -> None:
        """Copy application files to installation directory."""
        self.logger.info("Copying application files...")
        
        source_dir = Path(__file__).parent
        
        # Files to copy
        files_to_copy = [
            ("src/windows_service.py", "efis_service.py"),
            ("src/imdisk_wrapper.py", "imdisk_wrapper.py"),
            ("src/network_manager.py", "network_manager.py"),
            ("src/sync_engine.py", "sync_engine.py"),
            ("src/sync_scheduler.py", "sync_scheduler.py"),
            ("src/drive_monitor.py", "drive_monitor.py"),
            ("src/notification_service.py", "notification_service.py"),
            ("efis_cli.py", "efis_cli.py"),
            ("requirements.txt", "requirements.txt")
        ]
        
        for src_file, dest_file in files_to_copy:
            src_path = source_dir / src_file
            dest_path = self.install_dir / dest_file
            
            if src_path.exists():
                shutil.copy2(src_path, dest_path)
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
            self.logger.info("Created default configuration")
        
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
    
    def register_service(self) -> bool:
        """
        Register Windows service.
        
        Returns:
            True if service registration successful
        """
        self.logger.info("Registering Windows service...")
        
        try:
            # Create service using sc command
            service_name = "EFISDataManager"
            service_display_name = "EFIS Data Manager Service"
            service_description = "Manages EFIS chart data synchronization and virtual USB drive mounting"
            
            # Service executable command
            service_cmd = f'"{sys.executable}" "{self.install_dir / "efis_service.py"}"'
            
            # Create service
            create_cmd = [
                "sc", "create", service_name,
                "binPath=", service_cmd,
                "DisplayName=", service_display_name,
                "start=", "auto",
                "type=", "own"
            ]
            
            result = subprocess.run(create_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Service creation failed: {result.stderr}")
            
            # Set service description
            desc_cmd = [
                "sc", "description", service_name, service_description
            ]
            subprocess.run(desc_cmd, capture_output=True, text=True)
            
            # Set service recovery options
            recovery_cmd = [
                "sc", "failure", service_name,
                "reset=", "86400",  # Reset failure count after 24 hours
                "actions=", "restart/60000/restart/60000/restart/60000"  # Restart after 1 minute
            ]
            subprocess.run(recovery_cmd, capture_output=True, text=True)
            
            self.logger.info(f"Service '{service_name}' registered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register service: {e}")
            return False
    
    def setup_scheduled_tasks(self) -> None:
        """Setup scheduled tasks for backup and maintenance."""
        self.logger.info("Setting up scheduled tasks...")
        
        # Create PowerShell script for mount verification
        mount_script = self.scripts_dir / "MountEFIS.ps1"
        mount_script_content = '''
# EFIS Virtual Drive Mount Script
$VHDPath = "C:\\Users\\fligh\\OneDrive\\Desktop\\virtualEFISUSB.vhd"
$DriveLetter = "E:"
$LogFile = "C:\\Scripts\\MountEFIS.log"

function Write-Log {
    param($Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Timestamp - $Message" | Out-File -FilePath $LogFile -Append
}

try {
    # Check if drive is already mounted
    if (Get-PSDrive -Name "E" -ErrorAction SilentlyContinue) {
        Write-Log "Drive E: is already mounted"
        exit 0
    }
    
    # Mount the VHD
    $MountResult = & "C:\\Program Files\\ImDisk\\MountImg.exe" -a -f $VHDPath -m $DriveLetter
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Successfully mounted VHD to $DriveLetter"
    } else {
        Write-Log "Failed to mount VHD: $MountResult"
        exit 1
    }
} catch {
    Write-Log "Error mounting VHD: $($_.Exception.Message)"
    exit 1
}
'''
        
        with open(mount_script, 'w', encoding='utf-8') as f:
            f.write(mount_script_content)
        
        # Create scheduled task for mount verification
        task_cmd = [
            "schtasks", "/create",
            "/tn", "MountEFIS",
            "/tr", f"powershell.exe -File \"{mount_script}\"",
            "/sc", "onstart",
            "/delay", "0001:00",  # 1 minute delay
            "/ru", "SYSTEM",
            "/rl", "HIGHEST",
            "/f"  # Force overwrite if exists
        ]
        
        result = subprocess.run(task_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            self.logger.info("Scheduled task 'MountEFIS' created successfully")
        else:
            self.logger.warning(f"Failed to create scheduled task: {result.stderr}")
    
    def create_uninstaller(self) -> None:
        """Create uninstaller script."""
        self.logger.info("Creating uninstaller...")
        
        uninstall_script = self.install_dir / "uninstall.py"
        uninstall_content = f'''#!/usr/bin/env python3
"""
EFIS Data Manager Uninstaller for Windows.
"""

import subprocess
import shutil
from pathlib import Path
import sys

def uninstall():
    """Uninstall EFIS Data Manager."""
    print("Uninstalling EFIS Data Manager...")
    
    # Stop and remove service
    try:
        subprocess.run(["sc", "stop", "EFISDataManager"], capture_output=True)
        subprocess.run(["sc", "delete", "EFISDataManager"], capture_output=True)
        print("Service removed")
    except Exception as e:
        print(f"Error removing service: {{e}}")
    
    # Remove scheduled task
    try:
        subprocess.run(["schtasks", "/delete", "/tn", "MountEFIS", "/f"], capture_output=True)
        print("Scheduled task removed")
    except Exception as e:
        print(f"Error removing scheduled task: {{e}}")
    
    # Remove installation directory
    try:
        install_dir = Path("{self.install_dir}")
        if install_dir.exists():
            shutil.rmtree(install_dir)
            print(f"Removed installation directory: {{install_dir}}")
    except Exception as e:
        print(f"Error removing installation directory: {{e}}")
    
    # Remove scripts directory (optional)
    scripts_dir = Path("C:\\\\Scripts")
    if scripts_dir.exists():
        try:
            for file in scripts_dir.glob("*EFIS*"):
                file.unlink()
            print("Removed EFIS scripts")
        except Exception as e:
            print(f"Error removing scripts: {{e}}")
    
    print("Uninstallation completed")

if __name__ == "__main__":
    uninstall()
'''
        
        with open(uninstall_script, 'w', encoding='utf-8') as f:
            f.write(uninstall_content)
        
        self.logger.info(f"Uninstaller created: {uninstall_script}")
    
    def install(self) -> bool:
        """
        Run complete installation process.
        
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
            
            # Register service
            if not self.register_service():
                return False
            
            # Setup scheduled tasks
            self.setup_scheduled_tasks()
            
            # Create uninstaller
            self.create_uninstaller()
            
            self.logger.info("Installation completed successfully!")
            self.logger.info(f"Installation directory: {self.install_dir}")
            self.logger.info("Service 'EFISDataManager' has been registered")
            self.logger.info("Use 'sc start EFISDataManager' to start the service")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed: {e}")
            return False


def main():
    """Main installer entry point."""
    parser = argparse.ArgumentParser(description="EFIS Data Manager Windows Installer")
    parser.add_argument(
        "--install-dir", "-d",
        help="Installation directory (default: C:\\Program Files\\EFIS Data Manager)"
    )
    parser.add_argument(
        "--config", "-c",
        help="Configuration file to use"
    )
    parser.add_argument(
        "--uninstall", "-u",
        action="store_true",
        help="Uninstall EFIS Data Manager"
    )
    
    args = parser.parse_args()
    
    if args.uninstall:
        # Run uninstaller
        uninstall_script = Path(args.install_dir or "C:\\Program Files\\EFIS Data Manager") / "uninstall.py"
        if uninstall_script.exists():
            subprocess.run([sys.executable, str(uninstall_script)])
        else:
            print("Uninstaller not found")
        return
    
    # Run installer
    installer = WindowsInstaller(args.install_dir, args.config)
    success = installer.install()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()