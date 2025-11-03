#!/usr/bin/env python3
"""
Cross-platform deployment script for EFIS Data Manager.
Handles installation on both Windows and macOS platforms.
"""

import os
import sys
import platform
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, Any


class CrossPlatformDeployer:
    """Handles cross-platform deployment of EFIS Data Manager."""
    
    def __init__(self):
        """Initialize deployer."""
        self.platform = platform.system().lower()
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for deployer."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('efis_deploy.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def detect_platform(self) -> str:
        """
        Detect current platform.
        
        Returns:
            Platform name (windows, darwin, linux)
        """
        return self.platform
    
    def check_requirements(self) -> bool:
        """
        Check platform-specific requirements.
        
        Returns:
            True if requirements are met
        """
        self.logger.info(f"Checking requirements for {self.platform}...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.logger.error("Python 3.8 or higher is required")
            return False
        
        # Platform-specific checks
        if self.platform == "windows":
            return self._check_windows_requirements()
        elif self.platform == "darwin":
            return self._check_macos_requirements()
        else:
            self.logger.error(f"Unsupported platform: {self.platform}")
            return False
    
    def _check_windows_requirements(self) -> bool:
        """Check Windows-specific requirements."""
        # Check for administrator privileges
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.logger.error("Administrator privileges required for Windows installation")
                return False
        except Exception as e:
            self.logger.error(f"Cannot check administrator privileges: {e}")
            return False
        
        # Check for PowerShell
        try:
            result = subprocess.run(["powershell", "-Command", "Get-Host"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error("PowerShell is required for Windows installation")
                return False
        except FileNotFoundError:
            self.logger.error("PowerShell not found")
            return False
        
        return True
    
    def _check_macos_requirements(self) -> bool:
        """Check macOS-specific requirements."""
        # Check macOS version
        try:
            result = subprocess.run(["sw_vers", "-productVersion"], 
                                  capture_output=True, text=True)
            version = result.stdout.strip()
            major_version = int(version.split('.')[0])
            
            if major_version < 10:
                self.logger.error("macOS 10.15 or higher is required")
                return False
        except Exception as e:
            self.logger.warning(f"Cannot determine macOS version: {e}")
        
        return True
    
    def create_package(self, output_dir: str = None) -> bool:
        """
        Create deployment package for current platform.
        
        Args:
            output_dir: Output directory for package
            
        Returns:
            True if package creation successful
        """
        self.logger.info(f"Creating deployment package for {self.platform}...")
        
        output_path = Path(output_dir or f"dist/{self.platform}")
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.platform == "windows":
                return self._create_windows_package(output_path)
            elif self.platform == "darwin":
                return self._create_macos_package(output_path)
            else:
                self.logger.error(f"Package creation not supported for {self.platform}")
                return False
                
        except Exception as e:
            self.logger.error(f"Package creation failed: {e}")
            return False
    
    def _create_windows_package(self, output_path: Path) -> bool:
        """Create Windows deployment package."""
        self.logger.info("Creating Windows package...")
        
        # Create package structure
        package_dir = output_path / "efis-data-manager-windows"
        package_dir.mkdir(exist_ok=True)
        
        # Copy Windows files
        windows_src = Path("windows")
        if windows_src.exists():
            import shutil
            shutil.copytree(windows_src, package_dir / "windows", dirs_exist_ok=True)
        
        # Copy shared files
        shared_src = Path("shared")
        if shared_src.exists():
            import shutil
            shutil.copytree(shared_src, package_dir / "shared", dirs_exist_ok=True)
        
        # Copy configuration
        config_src = Path("config")
        if config_src.exists():
            import shutil
            shutil.copytree(config_src, package_dir / "config", dirs_exist_ok=True)
        
        # Create installation script
        install_script = package_dir / "install.bat"
        install_script_content = '''@echo off
echo Installing EFIS Data Manager for Windows...
python windows\\install.py %*
if %ERRORLEVEL% EQU 0 (
    echo Installation completed successfully!
) else (
    echo Installation failed!
    pause
)
'''
        
        with open(install_script, 'w') as f:
            f.write(install_script_content)
        
        # Create README
        readme = package_dir / "README.txt"
        readme_content = '''EFIS Data Manager - Windows Installation Package

Requirements:
- Windows 10 or higher
- Python 3.8 or higher
- Administrator privileges

Installation:
1. Right-click on install.bat and select "Run as administrator"
2. Follow the installation prompts
3. The service will be automatically registered and started

Configuration:
- Edit config\\efis_config.yaml to customize settings
- Use the EFIS CLI tool for management: efis --help

Uninstallation:
- Run the uninstaller from the installation directory
- Or use: python uninstall.py

For support, see the documentation or contact support.
'''
        
        with open(readme, 'w') as f:
            f.write(readme_content)
        
        self.logger.info(f"Windows package created: {package_dir}")
        return True
    
    def _create_macos_package(self, output_path: Path) -> bool:
        """Create macOS deployment package."""
        self.logger.info("Creating macOS package...")
        
        # Create package structure
        package_dir = output_path / "efis-data-manager-macos"
        package_dir.mkdir(exist_ok=True)
        
        # Copy macOS files
        macos_src = Path("macos")
        if macos_src.exists():
            import shutil
            shutil.copytree(macos_src, package_dir / "macos", dirs_exist_ok=True)
        
        # Copy shared files
        shared_src = Path("shared")
        if shared_src.exists():
            import shutil
            shutil.copytree(shared_src, package_dir / "shared", dirs_exist_ok=True)
        
        # Copy configuration
        config_src = Path("config")
        if config_src.exists():
            import shutil
            shutil.copytree(config_src, package_dir / "config", dirs_exist_ok=True)
        
        # Create installation script
        install_script = package_dir / "install.sh"
        install_script_content = '''#!/bin/bash
echo "Installing EFIS Data Manager for macOS..."

# Check if running with sudo for system-wide installation
if [[ $EUID -eq 0 ]]; then
    echo "Installing system-wide daemon..."
    python3 macos/install.py --system-wide "$@"
else
    echo "Installing user agent..."
    python3 macos/install.py "$@"
fi

if [ $? -eq 0 ]; then
    echo "Installation completed successfully!"
else
    echo "Installation failed!"
    exit 1
fi
'''
        
        with open(install_script, 'w') as f:
            f.write(install_script_content)
        
        install_script.chmod(0o755)
        
        # Create README
        readme = package_dir / "README.md"
        readme_content = '''# EFIS Data Manager - macOS Installation Package

## Requirements
- macOS 10.15 or higher
- Python 3.8 or higher
- Homebrew (recommended)

## Installation

### User Installation (Recommended)
```bash
./install.sh
```

### System-wide Installation
```bash
sudo ./install.sh --system-wide
```

## Configuration
- Edit `config/efis_config.yaml` to customize settings
- Use the EFIS CLI tool for management: `efis --help`

## Starting/Stopping the Service

### User Agent
```bash
launchctl start com.efis.datamanager
launchctl stop com.efis.datamanager
```

### System Daemon
```bash
sudo launchctl start com.efis.datamanager
sudo launchctl stop com.efis.datamanager
```

## Uninstallation
Run the uninstaller from the installation directory:
```bash
python3 uninstall.py
```

## Support
For support, see the documentation or contact support.
'''
        
        with open(readme, 'w') as f:
            f.write(readme_content)
        
        self.logger.info(f"macOS package created: {package_dir}")
        return True
    
    def deploy(self, config_file: str = None, install_dir: str = None, **kwargs) -> bool:
        """
        Deploy EFIS Data Manager on current platform.
        
        Args:
            config_file: Configuration file to use
            install_dir: Installation directory
            **kwargs: Additional platform-specific arguments
            
        Returns:
            True if deployment successful
        """
        self.logger.info(f"Deploying EFIS Data Manager on {self.platform}...")
        
        try:
            if self.platform == "windows":
                return self._deploy_windows(config_file, install_dir, **kwargs)
            elif self.platform == "darwin":
                return self._deploy_macos(config_file, install_dir, **kwargs)
            else:
                self.logger.error(f"Deployment not supported for {self.platform}")
                return False
                
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return False
    
    def _deploy_windows(self, config_file: str = None, install_dir: str = None, **kwargs) -> bool:
        """Deploy on Windows."""
        cmd = [sys.executable, "windows/install.py"]
        
        if config_file:
            cmd.extend(["--config", config_file])
        if install_dir:
            cmd.extend(["--install-dir", install_dir])
        
        result = subprocess.run(cmd)
        return result.returncode == 0
    
    def _deploy_macos(self, config_file: str = None, install_dir: str = None, **kwargs) -> bool:
        """Deploy on macOS."""
        cmd = [sys.executable, "macos/install.py"]
        
        if config_file:
            cmd.extend(["--config", config_file])
        if install_dir:
            cmd.extend(["--install-dir", install_dir])
        if kwargs.get("system_wide"):
            cmd.append("--system-wide")
        if kwargs.get("user"):
            cmd.extend(["--user", kwargs["user"]])
        
        result = subprocess.run(cmd)
        return result.returncode == 0


def main():
    """Main deployment entry point."""
    parser = argparse.ArgumentParser(
        description="EFIS Data Manager Cross-Platform Deployer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy on current platform
  python deploy.py install

  # Create deployment package
  python deploy.py package --output dist/

  # Deploy with custom configuration
  python deploy.py install --config my_config.yaml

  # macOS system-wide installation
  python deploy.py install --system-wide
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install EFIS Data Manager")
    install_parser.add_argument("--config", "-c", help="Configuration file to use")
    install_parser.add_argument("--install-dir", "-d", help="Installation directory")
    install_parser.add_argument("--user", "-u", help="User to run as (macOS only)")
    install_parser.add_argument("--system-wide", "-s", action="store_true", 
                               help="System-wide installation (macOS only)")
    
    # Package command
    package_parser = subparsers.add_parser("package", help="Create deployment package")
    package_parser.add_argument("--output", "-o", help="Output directory")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check requirements")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    deployer = CrossPlatformDeployer()
    
    if args.command == "check":
        success = deployer.check_requirements()
        if success:
            print(f"✅ All requirements met for {deployer.platform}")
        else:
            print(f"❌ Requirements check failed for {deployer.platform}")
        return 0 if success else 1
    
    elif args.command == "package":
        success = deployer.create_package(args.output)
        return 0 if success else 1
    
    elif args.command == "install":
        # Check requirements first
        if not deployer.check_requirements():
            return 1
        
        # Deploy
        kwargs = {}
        if hasattr(args, 'system_wide'):
            kwargs['system_wide'] = args.system_wide
        if hasattr(args, 'user'):
            kwargs['user'] = args.user
        
        success = deployer.deploy(args.config, args.install_dir, **kwargs)
        return 0 if success else 1
    
    return 1


if __name__ == "__main__":
    sys.exit(main())