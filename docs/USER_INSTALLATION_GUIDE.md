# EFIS Data Manager Installation Guide

This guide provides step-by-step instructions for installing and setting up the EFIS Data Manager system on both Windows and macOS platforms.

## Table of Contents

- [System Requirements](#system-requirements)
- [Pre-Installation Checklist](#pre-installation-checklist)
- [Windows Installation](#windows-installation)
- [macOS Installation](#macos-installation)
- [Initial Configuration](#initial-configuration)
- [Verification and Testing](#verification-and-testing)
- [Troubleshooting Installation Issues](#troubleshooting-installation-issues)

## System Requirements

### Windows System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space for installation, 50GB+ for chart data storage
- **Network**: Ethernet or Wi-Fi connection to local network
- **Administrator Access**: Required for service installation

### macOS System Requirements

- **Operating System**: macOS 10.15 (Catalina) or later
- **Python**: Version 3.8 or higher (usually pre-installed)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space for installation, 100GB+ for chart data and archives
- **Network**: Ethernet or Wi-Fi connection to local network
- **Administrator Access**: Required for daemon installation

### Network Requirements

- Both systems must be on the same local network
- SSH access between systems (port 22)
- Internet access for GRT software downloads (HTTPS, port 443)
- Firewall configured to allow communication between systems

## Pre-Installation Checklist

### Before You Begin

1. **Verify Network Connectivity**
   - Ensure both Windows and macOS systems are on the same network
   - Note the IP addresses of both systems
   - Test ping connectivity between systems

2. **Gather Required Information**
   - Windows system IP address
   - macOS system IP address
   - macOS username for SSH access
   - Dropbox or cloud storage paths (if using)

3. **Prepare File Paths**
   - Location for virtual USB drive file (Windows)
   - Archive storage location (macOS)
   - Demo file storage location (macOS)
   - Logbook storage location (macOS)

4. **Download Required Software**
   - ImDisk Toolkit for Windows
   - Git (if not already installed)

## Windows Installation

### Step 1: Install Prerequisites

#### Install Python
1. Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Run the installer **as Administrator**
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

**⚠️ CRITICAL: Fix Windows App Execution Aliases**

If you get "python was not found; run without arguments to install from the microsoft store", you need to disable Windows Store redirects:

1. Open **Settings** → **Apps** → **App execution aliases**
2. Turn **OFF** the toggles for:
   - `App Installer python.exe`
   - `App Installer python3.exe`
3. Close and reopen Command Prompt
4. Test again: `python --version`

This is a common Windows 10/11 issue where the system redirects `python` to the Microsoft Store even when Python is properly installed.

#### Install ImDisk Toolkit
1. Download ImDisk from [LTR Data](https://www.ltr-data.se/opencode.html/#ImDisk)
2. Run the installer **as Administrator**
3. Accept default installation location: `C:\Program Files\ImDisk\`
4. Verify installation:
   ```cmd
   "C:\Program Files\ImDisk\MountImg.exe" /?
   ```

#### Install Git (Optional)
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default settings
3. Verify installation:
   ```cmd
   git --version
   ```

### Step 2: Download and Install EFIS Data Manager

#### Option A: Download Release Package
1. Download the latest release from GitHub
2. Extract to `C:\EFIS\efis-data-manager\`
3. Open Command Prompt **as Administrator**
4. Navigate to installation directory:
   ```cmd
   cd C:\EFIS\efis-data-manager
   ```

#### Option B: Clone from Git
```cmd
# Open Command Prompt as Administrator
cd C:\EFIS\
git clone https://github.com/your-org/efis-data-manager.git
cd efis-data-manager
```

### Step 3: Run Windows Setup Script

```cmd
# Run the automated setup script
setup_dev_windows.bat

# If the script fails, run manual setup:
cd windows
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
pip install -e .
```

### Step 4: Create Virtual USB Drive

1. **Create VHD file location:**
   ```cmd
   mkdir "C:\Users\%USERNAME%\OneDrive\Desktop"
   ```

2. **Create the virtual drive file** (if not already created by Chart Manager):
   - Use Disk Management to create a new VHD
   - Or copy existing `virtualEFISUSB.vhd` file
   - Ensure file is located at: `C:\Users\fligh\OneDrive\Desktop\virtualEFISUSB.vhd`

3. **Test virtual drive mounting:**
   ```cmd
   cd windows
   python src\imdisk_wrapper.py --test
   ```

### Step 5: Configure Windows Settings

Create or edit `config\efis_config.yaml`:

```yaml
windows:
  # Virtual drive configuration
  virtualDriveFile: "C:/path/to/virtualEFISUSB.vhd"
  mountTool: "C:/Program Files/ImDisk/MountImg.exe"
  driveLetter: "E:"
  
  # Network configuration
  macbookHostname: "YourMacName.local"  # Primary - works with DHCP
  macbookIP: "192.168.1.100"            # Fallback if hostname fails
  syncPort: 22
  
  # Timing settings
  syncInterval: 1800  # 30 minutes
  retryAttempts: 3
  retryDelay: 600     # 10 minutes

logging:
  logLevel: "INFO"
```

### Step 6: Install Windows Service

```cmd
# Navigate to windows directory
cd windows

# Install the service
python install.py
```

**If installation fails with "service already exists":**
```cmd
# Delete the existing service first
sc delete EFISDataManager

# Then reinstall
python install.py
```

### Step 7: Start and Verify Service

```cmd
# Start the service
sc start EFISDataManager

# Check service status
sc query EFISDataManager
```

**Expected output when running:**
```
STATE: 4  RUNNING
```

**Service management commands:**
```cmd
# Stop the service
sc stop EFISDataManager

# Check service status
sc query EFISDataManager

# View service configuration
sc qc EFISDataManager
```

**Troubleshooting:**

If service fails to start (error 1053):
1. Test the service script directly:
   ```cmd
   python "C:\Program Files\EFIS Data Manager\efis_service.py"
   ```
2. Check for error messages
3. Verify all dependencies are installed:
   ```cmd
   pip install -r windows\requirements.txt
   ```
4. Check Windows Event Viewer → Windows Logs → Application for detailed errors

### Step 8: Verify Operation



## macOS Installation

### Step 1: Install Prerequisites

#### Verify Python Installation
```bash
# Check Python version
python3 --version

# If Python is not installed or version is < 3.8:
# Install via Homebrew (recommended)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.9
```

#### Install Xcode Command Line Tools
```bash
xcode-select --install
```

### Step 2: Download and Install EFIS Data Manager

#### Option A: Download Release Package
1. Download the latest release from GitHub
2. Extract to `/Users/$(whoami)/efis-data-manager/`
3. Open Terminal
4. Navigate to installation directory:
   ```bash
   cd ~/efis-data-manager
   ```

#### Option B: Clone from Git
```bash
cd ~
git clone https://github.com/your-org/efis-data-manager.git
cd efis-data-manager
```

### Step 3: Run macOS Setup Script

```bash
# Make script executable and run
chmod +x setup_dev_macos.sh
./setup_dev_macos.sh

# If the script fails, run manual setup:
cd macos
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Step 4: Create Required Directories

```bash
# Create archive directories (adjust paths as needed)
mkdir -p "/Users/$(whoami)/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
mkdir -p "/Users/$(whoami)/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
mkdir -p "/Users/$(whoami)/Library/CloudStorage/Dropbox/Flying/Logbooks"

# Or create local directories if not using Dropbox
mkdir -p "/Users/$(whoami)/EFIS-Archive/USB"
mkdir -p "/Users/$(whoami)/EFIS-Archive/Demo"
mkdir -p "/Users/$(whoami)/EFIS-Archive/Logbooks"
```

### Step 5: Install macOS Daemon

```bash
# Install the daemon
cd macos
python install.py

# Or use the CLI tool
./macos/efis daemon install
```

### Step 6: Configure macOS Settings

Create or edit `config/efis_config.yaml`:

```yaml
macos:
  # File storage paths - UPDATE WITH YOUR ACTUAL PATHS
  archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
  demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
  logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
  
  # GRT website URLs (usually don't need to change)
  grtUrls:
    navDatabase: "https://grtavionics.com/downloads/nav-database"
    hxrSoftware: "https://grtavionics.com/downloads/hxr-software"
    miniAPSoftware: "https://grtavionics.com/downloads/mini-ap"
    ahrsSoftware: "https://grtavionics.com/downloads/ahrs"
    servoSoftware: "https://grtavionics.com/downloads/servo"
  
  # Timing settings
  checkInterval: 3600    # 1 hour
  navCheckTime: "01:00"  # 1:00 AM daily
  grtCheckTime: "01:30"  # 1:30 AM daily

logging:
  logLevel: "INFO"
  logToFile: true
  logFile: "logs/macos.log"
```

### Step 7: Set Up SSH Access

#### Generate SSH Key Pair
```bash
# Generate SSH key for Windows to connect to macOS
ssh-keygen -t rsa -b 4096 -f ~/.ssh/efis_rsa

# Add public key to authorized_keys
cat ~/.ssh/efis_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### Copy Private Key to Windows
1. Copy the private key file `~/.ssh/efis_rsa` to Windows system
2. Place it in `C:\Users\%USERNAME%\.ssh\efis_rsa`
3. Set appropriate permissions on Windows

## Initial Configuration

### Step 1: Network Configuration

#### Find IP Addresses

**Windows:**
```cmd
ipconfig
# Note the IPv4 Address
```

**macOS:**
```bash
ifconfig | grep "inet "
# Note the IP address (usually 192.168.x.x)
```

#### Test Network Connectivity

**From Windows to macOS:**
```cmd
ping 192.168.1.100  # Replace with actual macOS IP
```

**From macOS to Windows:**
```bash
ping 192.168.1.101  # Replace with actual Windows IP
```

### Step 2: SSH Configuration

#### Test SSH Connection from Windows
```cmd
# Test SSH connection (replace IP and username)
ssh -i C:\Users\%USERNAME%\.ssh\efis_rsa mwalker@192.168.1.100
```

If successful, you should see the macOS terminal prompt.

### Step 3: Update Configuration Files

#### Update Windows Configuration
Edit `config/efis_config.yaml` on Windows:
```yaml
windows:
  macbookIP: "192.168.1.100"  # Actual macOS IP
  syncUser: "mwalker"         # Actual macOS username
```

#### Update macOS Configuration
Edit `config/efis_config.yaml` on macOS:
```yaml
macos:
  # Update paths to match your system
  archivePath: "/Users/yourusername/path/to/archive"
  demoPath: "/Users/yourusername/path/to/demo"
  logbookPath: "/Users/yourusername/path/to/logbooks"
```

## Verification and Testing

### Step 1: Test Windows Components

```cmd
# Check Windows service status
windows\efis.bat service status

# Test virtual drive mounting
windows\efis.bat drive status
windows\efis.bat drive mount

# Test system status
windows\efis.bat status
```

### Step 2: Test macOS Components

```bash
# Check daemon status
./macos/efis daemon status

# Test GRT website access
./macos/efis check-updates

# Test system status
./macos/efis status
```

### Step 3: Test Cross-Platform Communication

```cmd
# From Windows, test sync to macOS
windows\efis.bat sync --test
```

### Step 4: Test USB Drive Processing (macOS)

1. Insert a USB drive
2. Create test files:
   ```bash
   # Create EFIS identification marker
   echo "EFIS Data Drive" > /Volumes/USB_DRIVE/EFIS_DRIVE.txt
   
   # Create test demo file
   echo "test data" > /Volumes/USB_DRIVE/DEMO-20231201-143022.LOG
   ```
3. Test processing:
   ```bash
   ./macos/efis process-usb /Volumes/USB_DRIVE --dry-run
   ```

## Troubleshooting Installation Issues

### Common Windows Issues

#### Issue: Python not found
**Error:** "python was not found; run without arguments to install from the microsoft store"

**Most Common Solution - Windows App Execution Aliases:**
1. Open **Settings** → **Apps** → **App execution aliases**
2. Turn **OFF** these toggles:
   - `App Installer python.exe`
   - `App Installer python3.exe`
3. Close and reopen Command Prompt
4. Test: `python --version`

**Alternative Solutions:**
```cmd
# Try the Python Launcher instead
py --version

# Reinstall Python with PATH option checked
# Or manually add to PATH:
set PATH=%PATH%;C:\Python39;C:\Python39\Scripts

# Use full path as workaround
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe" --version
```

#### Issue: ImDisk installation fails
**Solution:**
- Run installer as Administrator
- Disable antivirus temporarily during installation
- Download from official LTR Data website

#### Issue: Service installation fails
**Solution:**
```cmd
# Run Command Prompt as Administrator
cd windows
python install.py --force
```

### Common macOS Issues

#### Issue: Permission denied errors
**Solution:**
```bash
# Fix permissions
sudo chown -R $(whoami) ~/efis-data-manager
chmod +x setup_dev_macos.sh
```

#### Issue: Daemon won't start
**Solution:**
```bash
# Check daemon status
launchctl list | grep efis

# Reload daemon
launchctl unload ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
launchctl load ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
```

#### Issue: SSH connection fails
**Solution:**
```bash
# Enable SSH on macOS
sudo systemsetup -setremotelogin on

# Check SSH service
sudo launchctl list | grep ssh
```

### Network Issues

#### Issue: Systems can't communicate
**Solutions:**
1. Check firewall settings on both systems
2. Verify both systems are on same network
3. Try different IP addresses if using DHCP
4. Test with ping and telnet

#### Issue: SSH authentication fails
**Solutions:**
1. Regenerate SSH keys
2. Check file permissions on keys
3. Verify public key is in authorized_keys
4. Test SSH connection manually

### Configuration Issues

#### Issue: Configuration file errors
**Solutions:**
1. Validate YAML syntax online
2. Check file paths exist
3. Verify IP addresses are correct
4. Use absolute paths for file locations

### Getting Help

If you encounter issues not covered here:

1. **Check the logs:**
   - Windows: `windows/logs/windows.log`
   - macOS: `macos/logs/macos.log`

2. **Run diagnostics:**
   ```bash
   # macOS
   ./macos/efis diagnostics
   
   # Windows
   windows\efis.bat diagnostics
   ```

3. **Review troubleshooting guide:** See `docs/TROUBLESHOOTING_FAQ.md`

4. **Contact support:** Create an issue on GitHub with:
   - Operating system and version
   - Error messages from logs
   - Steps to reproduce the issue
   - Configuration file (with sensitive data removed)

## Next Steps

After successful installation:

1. **Read the User Manual:** `docs/USER_MANUAL.md`
2. **Learn USB Drive Preparation:** `docs/USB_DRIVE_GUIDE.md`
3. **Set up Backup Procedures:** `docs/BACKUP_RECOVERY_GUIDE.md`
4. **Configure Notifications:** Update email settings in configuration

The system should now be running and automatically managing your EFIS data!