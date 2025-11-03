# EFIS Data Manager Troubleshooting Guide and FAQ

This document provides comprehensive troubleshooting information and frequently asked questions for the EFIS Data Manager system.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Windows Issues](#windows-issues)
- [macOS Issues](#macos-issues)
- [Network Issues](#network-issues)
- [USB Drive Issues](#usb-drive-issues)
- [Configuration Issues](#configuration-issues)
- [Performance Issues](#performance-issues)
- [Frequently Asked Questions](#frequently-asked-questions)
- [Log Analysis](#log-analysis)
- [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### System Health Check

Run these commands to quickly assess system health:

**macOS:**
```bash
# Check system status
./macos/efis status

# Run diagnostics
./macos/efis diagnostics

# Check recent logs
./macos/efis logs --lines 50
```

**Windows:**
```cmd
# Check system status
windows\efis.bat status

# Check virtual drive
windows\efis.bat drive status

# Check service status
windows\efis.bat service status
```

### Common Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| ✅ All systems operational | Everything working normally | None |
| ⚠️ Minor issues detected | Some non-critical problems | Review warnings |
| ❌ Critical errors found | System not functioning | Immediate attention needed |
| 🔄 Operations in progress | System is busy | Wait for completion |

## Windows Issues

### Virtual Drive Mount Problems

#### Issue: Virtual drive won't mount

**Symptoms:**
- Drive E: not visible in File Explorer
- Error: "Failed to mount virtual drive"
- ImDisk errors in logs

**Diagnosis:**
```cmd
# Check if ImDisk is installed
"C:\Program Files\ImDisk\MountImg.exe" /?

# Check VHD file exists
dir "C:\Users\fligh\OneDrive\Desktop\virtualEFISUSB.vhd"

# Check current mounts
"C:\Program Files\ImDisk\MountImg.exe" -l
```

**Solutions:**

1. **Install/Reinstall ImDisk:**
   ```cmd
   # Download from: https://www.ltr-data.se/opencode.html/#ImDisk
   # Run installer as Administrator
   ```

2. **Check VHD file integrity:**
   ```cmd
   # Verify file is not corrupted
   chkdsk "C:\Users\fligh\OneDrive\Desktop\virtualEFISUSB.vhd"
   ```

3. **Manual mount test:**
   ```cmd
   # Try manual mount
   "C:\Program Files\ImDisk\MountImg.exe" -a -f "C:\Users\fligh\OneDrive\Desktop\virtualEFISUSB.vhd" -m E:
   ```

4. **Check permissions:**
   ```cmd
   # Run as Administrator
   # Ensure user has full control of VHD file
   ```

#### Issue: Drive mounts but becomes inaccessible

**Symptoms:**
- Drive appears in File Explorer but shows as inaccessible
- "Access denied" errors
- Files appear corrupted

**Solutions:**

1. **Unmount and remount:**
   ```cmd
   windows\efis.bat drive unmount
   windows\efis.bat drive mount
   ```

2. **Check disk for errors:**
   ```cmd
   chkdsk E: /f
   ```

3. **Verify VHD file:**
   ```cmd
   # Check file size and modification time
   dir "C:\Users\fligh\OneDrive\Desktop\virtualEFISUSB.vhd"
   ```

### Windows Service Issues

#### Issue: Service won't start

**Symptoms:**
- Service shows "Stopped" status
- Error 1053: "Service did not respond to start request"
- Python errors in Event Viewer

**Diagnosis:**
```cmd
# Check service status
sc query EFISDataManager

# Check service configuration
sc qc EFISDataManager

# View service logs
windows\efis.bat logs --component service
```

**Solutions:**

1. **Reinstall service:**
   ```cmd
   windows\efis.bat service uninstall
   windows\efis.bat service install
   windows\efis.bat service start
   ```

2. **Check Python environment:**
   ```cmd
   # Verify Python installation
   python --version
   
   # Check required packages
   pip list | findstr efis
   ```

3. **Run in debug mode:**
   ```cmd
   # Run service manually for debugging
   cd windows
   python src/efis_windows/service.py --debug
   ```

### Synchronization Issues

#### Issue: Files not syncing to macOS

**Symptoms:**
- Sync operation reports success but files don't appear on macOS
- Network timeout errors
- SSH connection failures

**Diagnosis:**
```cmd
# Test network connectivity
ping 192.168.1.100

# Test SSH connection
ssh mwalker@192.168.1.100 "echo 'Connection successful'"

# Check sync logs
windows\efis.bat logs --component sync
```

**Solutions:**

1. **Verify network configuration:**
   ```yaml
   # config/efis_config.yaml
   windows:
     macbookIP: "192.168.1.100"  # Correct IP
     syncPort: 22
     syncUser: "mwalker"
   ```

2. **Set up SSH keys:**
   ```cmd
   # Generate SSH key pair
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/efis_rsa
   
   # Copy public key to macOS
   ssh-copy-id -i ~/.ssh/efis_rsa.pub mwalker@192.168.1.100
   ```

3. **Test manual sync:**
   ```cmd
   # Test rsync manually
   rsync -avz -e "ssh -i ~/.ssh/efis_rsa" E:/ mwalker@192.168.1.100:/Users/mwalker/EFIS-Sync/
   ```

## macOS Issues

### Daemon Startup Problems

#### Issue: Daemon won't start

**Symptoms:**
- `launchctl list` doesn't show daemon
- Error: "Service not loaded"
- Permission denied errors

**Diagnosis:**
```bash
# Check daemon status
launchctl list | grep efis

# Check plist file
cat ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist

# Check daemon logs
./macos/efis logs --component daemon
```

**Solutions:**

1. **Reinstall daemon:**
   ```bash
   # Unload existing daemon
   launchctl unload ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
   
   # Reinstall
   cd macos
   python install.py
   
   # Load daemon
   launchctl load ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
   ```

2. **Fix permissions:**
   ```bash
   # Ensure correct ownership
   sudo chown -R $(whoami) ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
   chmod 644 ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
   ```

3. **Check Python environment:**
   ```bash
   # Verify virtual environment
   source macos/venv/bin/activate
   python -c "import efis_macos; print('Import successful')"
   ```

### GRT Website Scraping Issues

#### Issue: Can't download GRT software updates

**Symptoms:**
- HTTP 403/404 errors
- "No updates found" when updates are available
- SSL certificate errors

**Diagnosis:**
```bash
# Test GRT website access
curl -I https://grtavionics.com/downloads/nav-database

# Check scraper logs
./macos/efis logs --component grt_scraper

# Test manual download
./macos/efis check-updates --verbose
```

**Solutions:**

1. **Update User-Agent string:**
   ```yaml
   # config/efis_config.yaml
   macos:
     webScraping:
       userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
   ```

2. **Check SSL certificates:**
   ```bash
   # Update certificates
   /Applications/Python\ 3.x/Install\ Certificates.command
   ```

3. **Verify GRT URLs:**
   ```bash
   # Test each URL manually
   curl -L https://grtavionics.com/downloads/nav-database
   ```

### USB Drive Detection Issues

#### Issue: EFIS USB drives not detected

**Symptoms:**
- USB drive inserted but not processed
- No notification of USB insertion
- Drive appears in Finder but not recognized as EFIS drive

**Diagnosis:**
```bash
# List mounted volumes
ls -la /Volumes/

# Check USB monitoring
./macos/efis logs --component usb_processor

# Test drive detection manually
./macos/efis detect-drive /Volumes/USB_DRIVE_NAME
```

**Solutions:**

1. **Check drive identification markers:**
   ```bash
   # Look for EFIS identification files
   ls -la /Volumes/USB_DRIVE_NAME/EFIS_DRIVE.txt
   ls -la /Volumes/USB_DRIVE_NAME/GRT_DATA/
   ```

2. **Create identification markers:**
   ```bash
   # Manually mark drive as EFIS drive
   echo "EFIS Data Drive" > /Volumes/USB_DRIVE_NAME/EFIS_DRIVE.txt
   mkdir -p /Volumes/USB_DRIVE_NAME/GRT_DATA
   ```

3. **Check file system:**
   ```bash
   # Verify drive is readable
   diskutil info /Volumes/USB_DRIVE_NAME
   ```

## Network Issues

### Connectivity Problems

#### Issue: Windows and macOS systems can't communicate

**Symptoms:**
- Ping fails between systems
- SSH connection refused
- Firewall blocking connections

**Diagnosis:**
```bash
# From Windows
ping 192.168.1.100
telnet 192.168.1.100 22

# From macOS
ping 192.168.1.101
nc -zv 192.168.1.101 22
```

**Solutions:**

1. **Check firewall settings:**
   
   **macOS:**
   ```bash
   # Check firewall status
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   
   # Allow SSH
   sudo systemsetup -setremotelogin on
   ```
   
   **Windows:**
   ```cmd
   # Check Windows Firewall
   netsh advfirewall show allprofiles
   
   # Allow SSH through firewall
   netsh advfirewall firewall add rule name="SSH" dir=in action=allow protocol=TCP localport=22
   ```

2. **Verify network configuration:**
   ```bash
   # Check IP addresses
   ipconfig /all  # Windows
   ifconfig       # macOS
   ```

3. **Test with different ports:**
   ```yaml
   # Try alternative SSH port
   windows:
     syncPort: 2222
   ```

### SSH Authentication Issues

#### Issue: SSH key authentication fails

**Symptoms:**
- Password prompts instead of key authentication
- "Permission denied (publickey)" errors
- Key not accepted by server

**Solutions:**

1. **Generate new SSH keys:**
   ```bash
   # Generate key pair
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/efis_rsa
   
   # Set correct permissions
   chmod 600 ~/.ssh/efis_rsa
   chmod 644 ~/.ssh/efis_rsa.pub
   ```

2. **Install public key on macOS:**
   ```bash
   # Copy public key to authorized_keys
   cat ~/.ssh/efis_rsa.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Test SSH connection:**
   ```bash
   # Test from Windows
   ssh -i ~/.ssh/efis_rsa mwalker@192.168.1.100
   ```

## USB Drive Issues

### File Processing Problems

#### Issue: Demo files not being moved correctly

**Symptoms:**
- Demo files remain on USB drive
- Files moved to wrong location
- File corruption during move

**Diagnosis:**
```bash
# Check demo file patterns
ls -la /Volumes/USB_DRIVE/DEMO-*.LOG

# Check target directory permissions
ls -ld "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"

# Check processing logs
./macos/efis logs --component file_processor
```

**Solutions:**

1. **Verify file patterns:**
   ```python
   # Check demo file naming
   import re
   pattern = r"DEMO-\d{8}-\d{6}(\+\d+)?\.LOG"
   filename = "DEMO-20231201-143022.LOG"
   print(re.match(pattern, filename))  # Should match
   ```

2. **Check target directory:**
   ```bash
   # Ensure target directory exists and is writable
   mkdir -p "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
   chmod 755 "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
   ```

3. **Manual file processing:**
   ```bash
   # Test file processing manually
   ./macos/efis process-files /Volumes/USB_DRIVE --dry-run
   ```

### Drive Update Issues

#### Issue: Chart data not copying to USB drive

**Symptoms:**
- USB drive processed but no new files
- Partial file transfers
- "Insufficient space" errors

**Solutions:**

1. **Check available space:**
   ```bash
   # Check USB drive space
   df -h /Volumes/USB_DRIVE
   
   # Check source archive size
   du -sh "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
   ```

2. **Verify source files:**
   ```bash
   # Check archive contents
   ls -la "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
   ```

3. **Manual copy test:**
   ```bash
   # Test manual copy
   cp -r "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/"* /Volumes/USB_DRIVE/
   ```

## Configuration Issues

### YAML Syntax Errors

#### Issue: Configuration file won't load

**Symptoms:**
- "YAML syntax error" messages
- Configuration validation failures
- System won't start

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   # Check YAML syntax
   python -c "import yaml; yaml.safe_load(open('config/efis_config.yaml'))"
   ```

2. **Common YAML issues:**
   ```yaml
   # Incorrect (mixing tabs and spaces)
   windows:
   	virtualDriveFile: "C:/file.vhd"
       driveLetter: "E:"
   
   # Correct (consistent indentation)
   windows:
     virtualDriveFile: "C:/file.vhd"
     driveLetter: "E:"
   ```

3. **Use YAML validator:**
   ```bash
   # Online validator or
   yamllint config/efis_config.yaml
   ```

### Missing Configuration Values

#### Issue: Required configuration keys missing

**Symptoms:**
- "Missing required key" errors
- System components not starting
- Default values being used unexpectedly

**Solutions:**

1. **Check required keys:**
   ```python
   # Validate configuration
   from shared.config.config_manager import ConfigManager
   config = ConfigManager()
   config.load_config('config/efis_config.yaml')
   errors = config.validate_config()
   print(errors)
   ```

2. **Add missing keys:**
   ```yaml
   # Ensure all required keys are present
   windows:
     virtualDriveFile: "C:/Users/fligh/OneDrive/Desktop/virtualEFISUSB.vhd"
     mountTool: "C:/Program Files/ImDisk/MountImg.exe"
     driveLetter: "E:"
     macbookIP: "192.168.1.100"
   
   macos:
     archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
     demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
     logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
   ```

## Performance Issues

### Slow File Transfers

#### Issue: Synchronization takes too long

**Symptoms:**
- Sync operations timeout
- Very slow transfer speeds
- High CPU/memory usage during sync

**Solutions:**

1. **Optimize sync settings:**
   ```yaml
   windows:
     syncTimeout: 600      # Increase timeout
     compressionLevel: 3   # Reduce compression
     parallelTransfers: 2  # Limit concurrent transfers
   ```

2. **Check network bandwidth:**
   ```bash
   # Test network speed
   iperf3 -c 192.168.1.100
   ```

3. **Monitor system resources:**
   ```bash
   # Check CPU and memory usage
   top -p $(pgrep -f efis)
   ```

### High Memory Usage

#### Issue: System using too much memory

**Symptoms:**
- System becomes slow
- Out of memory errors
- Frequent garbage collection

**Solutions:**

1. **Adjust memory limits:**
   ```yaml
   macos:
     daemon:
       maxMemoryUsage: 256  # Reduce from 512MB
   ```

2. **Enable memory monitoring:**
   ```python
   # Add memory monitoring to logs
   import psutil
   process = psutil.Process()
   memory_mb = process.memory_info().rss / 1024 / 1024
   logger.info(f"Memory usage: {memory_mb:.1f}MB")
   ```

## Frequently Asked Questions

### General Questions

**Q: How often does the system check for updates?**
A: By default, the system checks for GRT updates daily at 1:00 AM and 1:30 AM. File synchronization occurs every 30 minutes when both systems are online.

**Q: Can I run the system on different network configurations?**
A: Yes, the system supports various network setups. Update the `macbookIP` configuration to match your network. VPN connections are also supported.

**Q: What happens if one system is offline for extended periods?**
A: The system queues operations and resumes when connectivity is restored. No data is lost during offline periods.

**Q: Can I use different USB drive brands/sizes?**
A: Yes, any USB drive that can be formatted as FAT32 or exFAT will work. The system automatically detects EFIS drives using identification markers.

### Technical Questions

**Q: How do I backup my configuration?**
A: Copy the entire `config/` directory to a safe location. Configuration files are plain text and can be version controlled.

**Q: Can I run multiple instances of the system?**
A: No, the system is designed to run as a single instance per machine. Multiple instances may cause conflicts.

**Q: How do I migrate to a new computer?**
A: Copy the configuration files and install the system on the new computer. Update IP addresses and file paths as needed.

**Q: What ports does the system use?**
A: By default, SSH (port 22) for file synchronization. HTTPS (port 443) for GRT website access. All ports are configurable.

### Troubleshooting Questions

**Q: Why aren't my notifications working?**
A: Check notification settings in the configuration file. Ensure desktop notifications are enabled in system preferences (macOS) or notification settings (Windows).

**Q: How do I reset the system to defaults?**
A: Delete or rename the configuration file. The system will create a new default configuration on next startup.

**Q: What should I do if the virtual drive becomes corrupted?**
A: Stop the Windows service, unmount the drive, and run `chkdsk` on the VHD file. If corruption persists, restore from backup or recreate the VHD.

## Log Analysis

### Understanding Log Messages

#### Common Log Patterns

```
# Successful operations
INFO - Virtual drive mounted successfully at E:
INFO - Synchronization completed: 45 files, 2.3MB transferred
INFO - USB drive processed: 3 demo files moved

# Warning conditions
WARNING - Network connectivity unstable, retrying in 60 seconds
WARNING - USB drive space low: 15MB remaining
WARNING - GRT website response slow: 5.2 seconds

# Error conditions
ERROR - Failed to mount virtual drive: Access denied
ERROR - SSH connection failed: Connection refused
ERROR - File processing failed: Permission denied
```

#### Log Analysis Commands

```bash
# Find errors in logs
grep "ERROR" logs/efis-data-manager.log

# Count operations by type
grep "Synchronization completed" logs/efis-data-manager.log | wc -l

# Find recent USB operations
grep "USB drive" logs/efis-data-manager.log | tail -10

# Monitor logs in real-time
tail -f logs/efis-data-manager.log
```

### Performance Monitoring

```bash
# Monitor sync performance
grep "Synchronization completed" logs/efis-data-manager.log | \
  awk '{print $NF}' | \
  sort -n

# Check error rates
total_ops=$(grep "operation" logs/efis-data-manager.log | wc -l)
errors=$(grep "ERROR" logs/efis-data-manager.log | wc -l)
echo "Error rate: $(($errors * 100 / $total_ops))%"
```

## Recovery Procedures

### System Recovery

#### Complete System Reset

1. **Stop all services:**
   ```bash
   # macOS
   launchctl unload ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
   
   # Windows
   windows\efis.bat service stop
   ```

2. **Backup current configuration:**
   ```bash
   cp -r config/ config-backup-$(date +%Y%m%d)/
   ```

3. **Reset to defaults:**
   ```bash
   # Remove configuration
   rm config/efis_config.yaml
   
   # Reinstall system
   ./setup_dev_macos.sh    # macOS
   setup_dev_windows.bat   # Windows
   ```

4. **Restore configuration:**
   ```bash
   # Edit and restore configuration
   cp config-backup-*/efis_config.yaml config/
   ```

#### Data Recovery

1. **Recover from Dropbox:**
   ```bash
   # Check Dropbox version history
   # Restore previous versions if needed
   ```

2. **Recover USB drive data:**
   ```bash
   # Use file recovery tools if needed
   # TestDisk, PhotoRec, or similar
   ```

3. **Rebuild chart archive:**
   ```bash
   # Re-sync from Windows virtual drive
   windows\efis.bat sync --force
   ```

### Emergency Procedures

#### System Completely Unresponsive

1. **Force stop all processes:**
   ```bash
   # Kill all EFIS processes
   pkill -f efis
   ```

2. **Check system resources:**
   ```bash
   # Check disk space
   df -h
   
   # Check memory
   free -h
   
   # Check CPU
   top
   ```

3. **Restart in safe mode:**
   ```bash
   # Start with minimal configuration
   ./macos/efis --config config/minimal.yaml
   ```

#### Data Corruption Recovery

1. **Verify file integrity:**
   ```bash
   # Check file checksums
   find /path/to/archive -type f -exec sha256sum {} \; > checksums.txt
   ```

2. **Restore from backup:**
   ```bash
   # Restore from most recent backup
   rsync -av backup/ current/
   ```

3. **Rebuild corrupted data:**
   ```bash
   # Re-download GRT software
   ./macos/efis check-updates --force-download
   
   # Re-sync chart data
   windows\efis.bat sync --full-sync
   ```

This troubleshooting guide covers the most common issues and their solutions. For additional support, check the system logs and use the diagnostic commands provided.