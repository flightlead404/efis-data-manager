#!/usr/bin/env python3
"""
Development environment setup script for EFIS Data Manager.
Sets up virtual environment, installs dependencies, and configures development tools.
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path
import argparse
import logging


class EnvironmentSetup:
    """Handles development environment setup."""
    
    def __init__(self, venv_dir: str = None):
        """
        Initialize environment setup.
        
        Args:
            venv_dir: Virtual environment directory (default: venv)
        """
        self.venv_dir = Path(venv_dir or "venv")
        self.platform = platform.system().lower()
        self.logger = self._setup_logging()
        
        # Platform-specific paths
        if self.platform == "windows":
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
            self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"
            self.venv_pip = self.venv_dir / "bin" / "pip"
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for environment setup."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        return logging.getLogger(__name__)
    
    def check_python_version(self) -> bool:
        """
        Check if Python version meets requirements.
        
        Returns:
            True if Python version is acceptable
        """
        if sys.version_info < (3, 8):
            self.logger.error("Python 3.8 or higher is required")
            return False
        
        self.logger.info(f"Python version: {sys.version}")
        return True
    
    def create_virtual_environment(self) -> bool:
        """
        Create virtual environment.
        
        Returns:
            True if virtual environment creation successful
        """
        self.logger.info(f"Creating virtual environment: {self.venv_dir}")
        
        try:
            if self.venv_dir.exists():
                self.logger.info("Virtual environment already exists")
                return True
            
            # Create virtual environment
            venv.create(self.venv_dir, with_pip=True)
            
            self.logger.info("Virtual environment created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self, dev_mode: bool = False) -> bool:
        """
        Install project dependencies.
        
        Args:
            dev_mode: If True, install development dependencies
            
        Returns:
            True if installation successful
        """
        self.logger.info("Installing dependencies...")
        
        try:
            # Upgrade pip first
            self._run_pip(["install", "--upgrade", "pip"])
            
            # Install deployment requirements
            self._run_pip(["install", "-r", "requirements-deployment.txt"])
            
            # Install platform-specific requirements
            if self.platform == "windows":
                if Path("requirements-windows.txt").exists():
                    self._run_pip(["install", "-r", "requirements-windows.txt"])
            elif self.platform == "darwin":
                if Path("requirements-macos.txt").exists():
                    self._run_pip(["install", "-r", "requirements-macos.txt"])
            
            # Install development dependencies if requested
            if dev_mode:
                dev_packages = [
                    "pytest>=7.4.0",
                    "pytest-cov>=4.1.0",
                    "black>=23.0.0",
                    "flake8>=6.0.0",
                    "mypy>=1.5.0",
                    "pre-commit>=3.0.0"
                ]
                
                for package in dev_packages:
                    self._run_pip(["install", package])
            
            self.logger.info("Dependencies installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def _run_pip(self, args: list) -> None:
        """Run pip command in virtual environment."""
        cmd = [str(self.venv_pip)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Pip command failed: {' '.join(args)}\\n{result.stderr}")
    
    def setup_pre_commit(self) -> bool:
        """
        Setup pre-commit hooks.
        
        Returns:
            True if setup successful
        """
        self.logger.info("Setting up pre-commit hooks...")
        
        try:
            # Create .pre-commit-config.yaml if it doesn't exist
            precommit_config = Path(".pre-commit-config.yaml")
            if not precommit_config.exists():
                config_content = '''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]
'''
                
                with open(precommit_config, 'w') as f:
                    f.write(config_content)
            
            # Install pre-commit hooks
            cmd = [str(self.venv_python), "-m", "pre_commit", "install"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Pre-commit setup failed: {result.stderr}")
                return False
            
            self.logger.info("Pre-commit hooks installed successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"Pre-commit setup failed: {e}")
            return False
    
    def create_development_config(self) -> None:
        """Create development configuration files."""
        self.logger.info("Creating development configuration...")
        
        # Create development directories
        dev_dirs = [
            Path("tmp/efis-dev/EFIS-USB"),
            Path("tmp/efis-dev/EFIS-DEMO"),
            Path("tmp/efis-dev/Logbooks"),
            Path("logs")
        ]
        
        for dev_dir in dev_dirs:
            dev_dir.mkdir(parents=True, exist_ok=True)
        
        # Create .env file for development
        env_file = Path(".env")
        if not env_file.exists():
            env_content = '''# EFIS Data Manager Development Environment
EFIS_ENV=development
EFIS_CONFIG_FILE=config/efis_config.development.yaml
PYTHONPATH=.
'''
            
            with open(env_file, 'w') as f:
                f.write(env_content)
        
        self.logger.info("Development configuration created")
    
    def setup_ide_config(self) -> None:
        """Setup IDE configuration files."""
        self.logger.info("Setting up IDE configuration...")
        
        # VS Code settings
        vscode_dir = Path(".vscode")
        vscode_dir.mkdir(exist_ok=True)
        
        # VS Code settings.json
        settings_file = vscode_dir / "settings.json"
        if not settings_file.exists():
            settings_content = '''{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "88"],
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/venv": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ]
}'''
            
            with open(settings_file, 'w') as f:
                f.write(settings_content)
        
        # VS Code launch.json
        launch_file = vscode_dir / "launch.json"
        if not launch_file.exists():
            launch_content = '''{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "EFIS Daemon (macOS)",
            "type": "python",
            "request": "launch",
            "program": "macos/src/efis_macos/daemon.py",
            "console": "integratedTerminal",
            "env": {
                "EFIS_ENV": "development"
            }
        },
        {
            "name": "EFIS Service (Windows)",
            "type": "python",
            "request": "launch",
            "program": "windows/src/windows_service.py",
            "console": "integratedTerminal",
            "env": {
                "EFIS_ENV": "development"
            }
        },
        {
            "name": "Configuration CLI",
            "type": "python",
            "request": "launch",
            "module": "shared.config.config_cli",
            "args": ["show"],
            "console": "integratedTerminal"
        }
    ]
}'''
            
            with open(launch_file, 'w') as f:
                f.write(launch_content)
        
        self.logger.info("IDE configuration created")
    
    def run_tests(self) -> bool:
        """
        Run test suite to verify setup.
        
        Returns:
            True if tests pass
        """
        self.logger.info("Running tests to verify setup...")
        
        try:
            cmd = [str(self.venv_python), "-m", "pytest", "tests/", "-v"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("All tests passed!")
                return True
            else:
                self.logger.warning(f"Some tests failed:\\n{result.stdout}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Could not run tests: {e}")
            return False
    
    def setup(self, dev_mode: bool = False, run_tests: bool = False) -> bool:
        """
        Run complete environment setup.
        
        Args:
            dev_mode: If True, install development dependencies
            run_tests: If True, run tests after setup
            
        Returns:
            True if setup successful
        """
        try:
            self.logger.info("Setting up EFIS Data Manager development environment...")
            
            # Check Python version
            if not self.check_python_version():
                return False
            
            # Create virtual environment
            if not self.create_virtual_environment():
                return False
            
            # Install dependencies
            if not self.install_dependencies(dev_mode):
                return False
            
            # Setup development tools
            if dev_mode:
                self.setup_pre_commit()
                self.create_development_config()
                self.setup_ide_config()
            
            # Run tests if requested
            if run_tests:
                self.run_tests()
            
            self.logger.info("Environment setup completed successfully!")
            self.logger.info(f"Virtual environment: {self.venv_dir}")
            
            # Provide activation instructions
            if self.platform == "windows":
                activate_cmd = f"{self.venv_dir}\\Scripts\\activate"
            else:
                activate_cmd = f"source {self.venv_dir}/bin/activate"
            
            self.logger.info(f"To activate: {activate_cmd}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Environment setup failed: {e}")
            return False


def main():
    """Main setup entry point."""
    parser = argparse.ArgumentParser(description="EFIS Data Manager Environment Setup")
    parser.add_argument(
        "--venv-dir", "-v",
        default="venv",
        help="Virtual environment directory (default: venv)"
    )
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="Install development dependencies and tools"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run tests after setup"
    )
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup(args.venv_dir)
    success = setup.setup(args.dev, args.test)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()