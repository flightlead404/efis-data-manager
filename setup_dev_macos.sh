#!/bin/bash
# Development setup script for macOS EFIS Data Manager component

set -e

echo "Setting up macOS EFIS Data Manager development environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or later:"
    echo "  - Using Homebrew: brew install python"
    echo "  - Or download from: https://python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Found Python $python_version"

# Navigate to macOS component directory
cd macos

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install in development mode
echo "Installing macOS component in development mode..."
pip install -e .

echo ""
echo "macOS EFIS Data Manager development environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  cd macos"
echo "  source venv/bin/activate"
echo ""
echo "To run the daemon in development mode:"
echo "  python src/efis_macos/daemon.py"
echo ""