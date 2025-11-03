# EFIS Data Manager Backup and Recovery Guide

This guide provides comprehensive procedures for backing up your EFIS Data Manager system and recovering from various failure scenarios.

## Table of Contents

- [Backup Strategy Overview](#backup-strategy-overview)
- [Configuration Backup](#configuration-backup)
- [Data Archive Backup](#data-archive-backup)
- [System State Backup](#system-state-backup)
- [Recovery Procedures](#recovery-procedures)
- [Disaster Recovery](#disaster-recovery)
- [Backup Verification](#backup-verification)

## Backup Strategy Overview

### Backup Components

The EFIS Data Manager system has several critical components that require backup:

**Configuration Files:**
- System configuration (`config/efis_config.yaml`)
- Platform-specific configurations
- SSH keys and credentials
- Service/daemon configurations

**Data Archives:**
- Chart data archive (macOS)
- Flight demo files archive
- Logbook files archive
- GRT software archive

**System State:**
- Installed software versions
- Service/daemon registration
- Log files and operational history
- User preferences and customizations

### Backup Frequency

**Daily Backups (Automatic):**
- Configuration files via cloud sync
- Flight data via Dropbox/cloud storage
- System logs (rotated automatically)

**Weekly Backups (Manual/Automated):**
- Complete system configuration
- Verification of cloud backup integrity
- Archive of recent operational logs

**Monthly Backups (Manual):**
- Complete system state snapshot
- Offline backup verification
- Recovery procedure testing

## Configuration Backup

### Automatic Configuration Backup

**Using Git Version Control:**
```bash
# Initialize git repository for configuration
cd config/
git init
git add .
git commit -m "Initial configuration backup"

# Set up remote repository (optional)
git remote add origin https://github.com/your-org/efis-config-backup.git
git push -u origin main
```

**Daily Configuration Backup Script:**
```bash
#!/bin/bash
# save as: backup_config.sh

BACKUP_DIR="/Users/$(whoami)/EFIS-Backups/config"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration files
cp -r config/ "$BACKUP_DIR/config-$DATE/"

# Backup SSH keys
cp -r ~/.ssh/efis_* "$BACKUP_DIR/ssh-keys-$DATE/" 2>/dev/null || true

# Backup service configurations
if [[ "$OSTYPE" == "darwin"* ]]; then
    cp ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist "$BACKUP_DIR/daemon-$DATE.plist" 2>/dev/null || true
fi

# Create archive
tar -czf "$BACKUP_DIR/efis-config-$DATE.tar.gz" -C "$BACKUP_DIR" "config-$DATE" "ssh-keys-$DATE"

# Clean up old backups (keep 30 days)
find "$BACKUP_DIR" -name "efis-config-*.tar.gz" -mtime +30 -delete

echo "Configuration backup completed: $BACKUP_DIR/efis-config-$DATE.tar.gz"
```

### Manual Configuration Backup

**Backup Current Configuration:**
```bash
# Create backup directory
mkdir -p ~/EFIS-Backups/$(date +%Y%m%d)

# Backup configuration files
cp -r config/ ~/EFIS-Backups/$(date +%Y%m%d)/

# Backup platform-specific configs
cp -r windows/config/ ~/EFIS-Backups/$(date +%Y%m%d)/windows-config/ 2>/dev/null || true
cp -r macos/config/ ~/EFIS-Backups/$(date +%Y%m%d)/macos-config/ 2>/dev/null || true

# Backup SSH keys
cp ~/.ssh/efis_* ~/EFIS-Backups/$(date +%Y%m%d)/ 2>/dev/null || true

# Create documentation
echo "Backup created: $(date)" > ~/EFIS-Backups/$(date +%Y%m%d)/backup_info.txt
echo "System: $(uname -a)" >> ~/EFIS-Backups/$(date +%Y%m%d)/backup_info.txt
echo "EFIS Version: $(git describe --tags 2>/dev/null || echo 'unknown')" >> ~/EFIS-Backups/$(date +%Y%m%d)/backup_info.txt
```

### Configuration Restore

**Restore from Backup:**
```bash
# Stop services first
./macos/efis daemon stop 2>/dev/null || true
windows\efis.bat service stop 2>/dev/null || true

# Restore configuration
BACKUP_DATE="20231201"  # Replace with actual backup date
cp -r ~/EFIS-Backups/$BACKUP_DATE/config/ ./

# Restore SSH keys
cp ~/EFIS-Backups/$BACKUP_DATE/efis_* ~/.ssh/ 2>/dev/null || true
chmod 600 ~/.ssh/efis_*

# Restart services
./macos/efis daemon start
windows\efis.bat service start

echo "Configuration restored from backup: $BACKUP_DATE"
```

## Data Archive Backup

### Cloud Storage Backup (Primary)

**Dropbox Integration:**
The system is designed to use Dropbox for primary data backup:

```yaml
# config/efis_config.yaml
macos:
  archivePath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB"
  demoPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO"
  logbookPath: "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks"
```

**Verify Dropbox Sync:**
```bash
# Check Dropbox sync status
ls -la "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/"

# Verify recent files are synced
find "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/" -mtime -1 -type f
```

### Local Backup (Secondary)

**Create Local Archive Backup:**
```bash
#!/bin/bash
# save as: backup_archives.sh

BACKUP_DIR="/Users/$(whoami)/EFIS-Backups/archives"
DATE=$(date +%Y%m%d)
SOURCE_DIR="/Users/mwalker/Library/CloudStorage/Dropbox/Flying"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup chart data
echo "Backing up chart data..."
rsync -av --progress "$SOURCE_DIR/EFIS-USB/" "$BACKUP_DIR/charts-$DATE/"

# Backup demo files
echo "Backing up demo files..."
rsync -av --progress "$SOURCE_DIR/EFIS-DEMO/" "$BACKUP_DIR/demo-$DATE/"

# Backup logbooks
echo "Backing up logbooks..."
rsync -av --progress "$SOURCE_DIR/Logbooks/" "$BACKUP_DIR/logbooks-$DATE/"

# Create compressed archive
echo "Creating compressed archive..."
tar -czf "$BACKUP_DIR/efis-archives-$DATE.tar.gz" -C "$BACKUP_DIR" \
    "charts-$DATE" "demo-$DATE" "logbooks-$DATE"

# Clean up uncompressed directories
rm -rf "$BACKUP_DIR/charts-$DATE" "$BACKUP_DIR/demo-$DATE" "$BACKUP_DIR/logbooks-$DATE"

# Clean up old backups (keep 90 days)
find "$BACKUP_DIR" -name "efis-archives-*.tar.gz" -mtime +90 -delete

echo "Archive backup completed: $BACKUP_DIR/efis-archives-$DATE.tar.gz"
```

### External Backup (Tertiary)

**USB Drive Backup:**
```bash
# Backup to external USB drive
EXTERNAL_DRIVE="/Volumes/EFIS_BACKUP"
DATE=$(date +%Y%m%d)

if [ -d "$EXTERNAL_DRIVE" ]; then
    echo "Creating external backup..."
    
    # Create backup structure
    mkdir -p "$EXTERNAL_DRIVE/EFIS-Backups/$DATE"
    
    # Copy configuration
    cp -r config/ "$EXTERNAL_DRIVE/EFIS-Backups/$DATE/"
    
    # Copy recent archives
    rsync -av --progress ~/EFIS-Backups/archives/ "$EXTERNAL_DRIVE/EFIS-Backups/$DATE/archives/"
    
    # Copy system information
    ./macos/efis diagnostics > "$EXTERNAL_DRIVE/EFIS-Backups/$DATE/system_info.txt"
    
    echo "External backup completed: $EXTERNAL_DRIVE/EFIS-Backups/$DATE"
else
    echo "External drive not found: $EXTERNAL_DRIVE"
fi
```

## System State Backup

### Complete System Snapshot

**Create System Snapshot:**
```bash
#!/bin/bash
# save as: system_snapshot.sh

SNAPSHOT_DIR="/Users/$(whoami)/EFIS-Backups/snapshots"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$SNAPSHOT_DIR/$DATE"

# System information
echo "Creating system snapshot: $DATE"

# Configuration
cp -r config/ "$SNAPSHOT_DIR/$DATE/"

# Installed packages
pip list > "$SNAPSHOT_DIR/$DATE/pip_packages.txt"

# System information
uname -a > "$SNAPSHOT_DIR/$DATE/system_info.txt"
sw_vers >> "$SNAPSHOT_DIR/$DATE/system_info.txt" 2>/dev/null || true

# Service status
./macos/efis status > "$SNAPSHOT_DIR/$DATE/service_status.txt" 2>/dev/null || true

# Recent logs
tail -1000 macos/logs/macos.log > "$SNAPSHOT_DIR/$DATE/recent_logs.txt" 2>/dev/null || true

# Network configuration
ifconfig > "$SNAPSHOT_DIR/$DATE/network_config.txt"

# Disk usage
df -h > "$SNAPSHOT_DIR/$DATE/disk_usage.txt"

# Process list
ps aux | grep efis > "$SNAPSHOT_DIR/$DATE/processes.txt"

# Create archive
tar -czf "$SNAPSHOT_DIR/system-snapshot-$DATE.tar.gz" -C "$SNAPSHOT_DIR" "$DATE"
rm -rf "$SNAPSHOT_DIR/$DATE"

echo "System snapshot completed: $SNAPSHOT_DIR/system-snapshot-$DATE.tar.gz"
```

## Recovery Procedures

### Configuration Recovery

**Scenario: Configuration files corrupted or lost**

**Recovery Steps:**
1. **Stop all services:**
   ```bash
   ./macos/efis daemon stop
   windows\efis.bat service stop
   ```

2. **Restore configuration from backup:**
   ```bash
   # Find most recent backup
   ls -la ~/EFIS-Backups/config/
   
   # Restore configuration
   BACKUP_DATE="20231201"
   cp -r ~/EFIS-Backups/$BACKUP_DATE/config/ ./
   ```

3. **Verify configuration:**
   ```bash
   # Test configuration loading
   python -c "
   from shared.config.config_manager import ConfigManager
   config = ConfigManager()
   config.load_config('config/efis_config.yaml')
   print('Configuration loaded successfully')
   "
   ```

4. **Restart services:**
   ```bash
   ./macos/efis daemon start
   windows\efis.bat service start
   ```

### Data Archive Recovery

**Scenario: Local data archives lost or corrupted**

**Recovery from Cloud Storage:**
```bash
# Verify Dropbox sync status
ls -la "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/"

# Force Dropbox resync if needed
# (Restart Dropbox application)

# Verify data integrity
find "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/" -name "*.LOG" | head -10
```

**Recovery from Local Backup:**
```bash
# Find most recent archive backup
ls -la ~/EFIS-Backups/archives/

# Extract backup
BACKUP_DATE="20231201"
cd ~/EFIS-Backups/archives/
tar -xzf "efis-archives-$BACKUP_DATE.tar.gz"

# Restore archives
rsync -av "charts-$BACKUP_DATE/" "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/"
rsync -av "demo-$BACKUP_DATE/" "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO/"
rsync -av "logbooks-$BACKUP_DATE/" "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks/"
```

### Service Recovery

**Scenario: System services not starting**

**macOS Daemon Recovery:**
```bash
# Check daemon status
launchctl list | grep efis

# Unload and reload daemon
launchctl unload ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist
launchctl load ~/Library/LaunchAgents/com.efis-data-manager.daemon.plist

# If plist is missing, reinstall
cd macos
python install.py
```

**Windows Service Recovery:**
```cmd
# Check service status
sc query EFISDataManager

# Restart service
net stop EFISDataManager
net start EFISDataManager

# If service is missing, reinstall
cd windows
python install.py
```

## Disaster Recovery

### Complete System Rebuild

**Scenario: Complete system failure requiring rebuild**

**Recovery Steps:**

1. **Install base system:**
   - Fresh OS installation
   - Install Python, Git, and prerequisites
   - Download EFIS Data Manager

2. **Restore configuration:**
   ```bash
   # Restore from backup
   cp -r backup/config/ ./config/
   cp backup/efis_* ~/.ssh/
   chmod 600 ~/.ssh/efis_*
   ```

3. **Restore data archives:**
   ```bash
   # Restore from cloud storage or backup
   # Verify Dropbox sync or restore from external backup
   ```

4. **Reinstall services:**
   ```bash
   # macOS
   cd macos
   ./setup_dev_macos.sh
   python install.py
   
   # Windows
   cd windows
   setup_dev_windows.bat
   python install.py
   ```

5. **Verify system operation:**
   ```bash
   ./macos/efis status
   ./macos/efis diagnostics
   ```

### Network Configuration Recovery

**Scenario: Network settings lost or changed**

**Recovery Steps:**
1. **Identify current network configuration:**
   ```bash
   ifconfig  # macOS
   ipconfig  # Windows
   ```

2. **Update configuration files:**
   ```yaml
   # config/efis_config.yaml
   windows:
     macbookIP: "192.168.1.100"  # Update with current IP
   ```

3. **Test connectivity:**
   ```bash
   ping 192.168.1.100
   ssh mwalker@192.168.1.100
   ```

4. **Restart services:**
   ```bash
   ./macos/efis daemon restart
   windows\efis.bat service restart
   ```

## Backup Verification

### Automated Backup Testing

**Backup Verification Script:**
```bash
#!/bin/bash
# save as: verify_backups.sh

echo "Verifying EFIS Data Manager backups..."

# Check configuration backups
CONFIG_BACKUP_DIR="~/EFIS-Backups/config"
if [ -d "$CONFIG_BACKUP_DIR" ]; then
    LATEST_CONFIG=$(ls -t "$CONFIG_BACKUP_DIR"/efis-config-*.tar.gz | head -1)
    if [ -n "$LATEST_CONFIG" ]; then
        echo "✓ Latest configuration backup: $(basename "$LATEST_CONFIG")"
    else
        echo "✗ No configuration backups found"
    fi
else
    echo "✗ Configuration backup directory not found"
fi

# Check archive backups
ARCHIVE_BACKUP_DIR="~/EFIS-Backups/archives"
if [ -d "$ARCHIVE_BACKUP_DIR" ]; then
    LATEST_ARCHIVE=$(ls -t "$ARCHIVE_BACKUP_DIR"/efis-archives-*.tar.gz | head -1)
    if [ -n "$LATEST_ARCHIVE" ]; then
        echo "✓ Latest archive backup: $(basename "$LATEST_ARCHIVE")"
    else
        echo "✗ No archive backups found"
    fi
else
    echo "✗ Archive backup directory not found"
fi

# Check cloud storage sync
DROPBOX_DIR="/Users/mwalker/Library/CloudStorage/Dropbox/Flying"
if [ -d "$DROPBOX_DIR" ]; then
    RECENT_FILES=$(find "$DROPBOX_DIR" -mtime -7 -type f | wc -l)
    echo "✓ Dropbox sync active: $RECENT_FILES files modified in last 7 days"
else
    echo "✗ Dropbox directory not accessible"
fi

echo "Backup verification completed."
```

### Manual Backup Testing

**Monthly Backup Test Procedure:**

1. **Test configuration restore:**
   ```bash
   # Create test directory
   mkdir -p /tmp/efis-test
   cd /tmp/efis-test
   
   # Extract latest backup
   tar -xzf ~/EFIS-Backups/config/efis-config-*.tar.gz
   
   # Test configuration loading
   python -c "
   import sys
   sys.path.append('/path/to/efis-data-manager/shared')
   from config.config_manager import ConfigManager
   config = ConfigManager()
   config.load_config('config-*/efis_config.yaml')
   print('Configuration test: PASSED')
   "
   ```

2. **Test data archive integrity:**
   ```bash
   # Check file counts and sizes
   find "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB" -type f | wc -l
   du -sh "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/"*
   ```

3. **Test recovery procedures:**
   - Document recovery time estimates
   - Verify all required backup components are available
   - Test network connectivity requirements

This backup and recovery guide ensures your EFIS Data Manager system can be quickly restored from various failure scenarios. Regular testing of these procedures is essential for maintaining system reliability.