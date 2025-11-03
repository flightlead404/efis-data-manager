# EFIS Data Manager User Manual

This comprehensive manual provides instructions for operating the EFIS Data Manager system in your daily aviation workflow.

## Table of Contents

- [System Overview](#system-overview)
- [Daily Operations](#daily-operations)
- [USB Drive Management](#usb-drive-management)
- [Chart Data Updates](#chart-data-updates)
- [GRT Software Updates](#grt-software-updates)
- [Monitoring and Notifications](#monitoring-and-notifications)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)
- [Maintenance Tasks](#maintenance-tasks)

## System Overview

The EFIS Data Manager automates the management of aviation data between your ground systems and aircraft EFIS displays. The system consists of:

### Windows Component
- **Virtual USB Drive Management**: Maintains connection to chart data
- **File Synchronization**: Transfers chart updates to macOS system
- **Scheduled Operations**: Runs automatically in the background

### macOS Component  
- **GRT Software Monitoring**: Checks for navigation and software updates
- **USB Drive Processing**: Handles EFIS USB drives when inserted
- **File Archive Management**: Organizes flight data and maintains backups

### Automated Workflows
- **Chart Synchronization**: Every 30 minutes when systems are online
- **GRT Update Checks**: Daily at 1:00 AM and 1:30 AM
- **USB Drive Processing**: Immediate when EFIS drives are inserted
- **File Organization**: Automatic sorting of demo files, snapshots, and logbooks

## Daily Operations

### Normal System Operation

Under normal conditions, the EFIS Data Manager operates automatically without user intervention:

1. **Windows System**: Maintains virtual drive connection and syncs chart data
2. **macOS System**: Monitors for updates and processes USB drives
3. **Notifications**: Alerts you to important events and updates
4. **Background Processing**: Handles all file transfers and organization

### Checking System Status

**macOS Status Check:**
```bash
./macos/efis status
```

**Windows Status Check:**
```cmd
windows\efis.bat status
```

**Expected Status Indicators:**
- ✅ **All Systems Operational**: Everything working normally
- ⚠️ **Minor Issues**: Non-critical warnings present
- ❌ **Critical Errors**: Immediate attention required
- 🔄 **Operations in Progress**: System busy with tasks#
## Starting Your Flight Day

**Morning Routine:**
1. **Check System Status**: Verify both systems are operational
2. **Review Notifications**: Check for any overnight updates or issues
3. **Prepare USB Drives**: Insert EFIS USB drives for processing if needed
4. **Verify Chart Currency**: Ensure latest chart data is available

**Pre-Flight USB Drive Preparation:**
1. Insert EFIS USB drive into macOS system
2. System automatically detects and processes the drive
3. Wait for completion notification
4. Safely eject drive when processing complete
5. Install drive in aircraft EFIS system

## USB Drive Management

### EFIS USB Drive Detection

The system automatically detects EFIS USB drives when inserted into the macOS system. Detection is based on:

- **Identification Files**: `EFIS_DRIVE.txt` or `GRT_DATA` directory
- **File Patterns**: Presence of demo files, snap files, or logbook files
- **Drive Characteristics**: File system type and capacity

### Automatic Processing Workflow

When an EFIS USB drive is inserted:

1. **Detection**: System identifies the drive as an EFIS drive
2. **File Processing**: 
   - Demo files moved to demo archive
   - Snapshot files moved to demo archive  
   - Logbook files moved to logbook archive with date-based naming
3. **Drive Updates**:
   - Latest chart data copied to drive
   - Current NAV database copied if available
   - Latest GRT software copied if available
4. **Verification**: File integrity checked after copying
5. **Notification**: User notified of completion and any updates applied

### Manual USB Drive Operations

**Prepare New EFIS USB Drive:**
```bash
./macos/efis prepare-usb /Volumes/USB_DRIVE_NAME
```

**Process Existing Drive:**
```bash
./macos/efis process-usb /Volumes/USB_DRIVE_NAME
```

**Check Drive Contents:**
```bash
./macos/efis list-drive /Volumes/USB_DRIVE_NAME
```

### USB Drive File Organization

**Files Removed from USB Drive:**
- `DEMO-YYYYMMDD-HHMMSS.LOG` → Moved to demo archive
- `*.png` (snapshots) → Moved to demo archive
- `*.csv` (logbooks) → Moved to logbook archive

**Files Added to USB Drive:**
- Latest chart data (PNG files in directory structure)
- `NAV.DB` (navigation database, updated every 28 days)
- GRT software files (when updates available)

## Chart Data Updates

### Automatic Chart Updates

**Windows System Process:**
1. Chart Manager updates virtual USB drive with latest charts
2. Windows service detects changes every 5 minutes
3. Modified files synchronized to macOS system every 30 minutes
4. macOS system updates local archive with new chart data

**Monitoring Chart Updates:**
- Check Windows logs for sync operations
- Verify chart data timestamp in macOS archive
- Monitor sync notifications for transfer status

### Manual Chart Synchronization

**Force Immediate Sync (Windows):**
```cmd
windows\efis.bat sync --force
```

**Check Sync Status:**
```cmd
windows\efis.bat sync --status
```

**Verify Chart Data (macOS):**
```bash
./macos/efis verify-charts
```

### Chart Data Locations

**Windows Virtual Drive:**
- Location: `E:\` (or configured drive letter)
- Source: Chart Manager application
- Update Frequency: As configured in Chart Manager

**macOS Archive:**
- Location: `/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB`
- Content: Complete chart data archive
- Update Frequency: Every 30 minutes via sync

## GRT Software Updates

### Automatic Update Monitoring

The system checks for GRT software updates daily:

**NAV Database Check (1:00 AM):**
- Downloads current NAV database
- Compares with previous version
- Notifies if update available
- Archives new version for USB drive updates

**GRT Software Check (1:30 AM):**
- Checks HXr software versions
- Checks Mini A/P software versions  
- Checks AHRS software versions
- Checks servo software versions
- Downloads and archives any updates found

### Manual Update Checks

**Check for All Updates:**
```bash
./macos/efis check-updates
```

**Check Specific Software:**
```bash
./macos/efis check-updates --software nav
./macos/efis check-updates --software hxr
./macos/efis check-updates --software mini-ap
```

**Force Download Updates:**
```bash
./macos/efis check-updates --download
```

### Update Notifications

You'll receive notifications for:
- **NAV Database Updates**: "New NAV database available (Cycle XXXX)"
- **Software Updates**: "GRT HXr software updated to version X.XX"
- **Download Completion**: "Updates downloaded and ready for USB transfer"
- **USB Transfer**: "Updates copied to USB drive"

### GRT Software Archive

**Archive Location:**
`/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/GRT-Software/`

**Archive Structure:**
```
GRT-Software/
├── NAV-Database/
│   ├── NAV-2023-12.DB
│   └── NAV-2024-01.DB
├── HXr-Software/
│   ├── HXr-8.01/
│   └── HXr-8.02/
├── Mini-AP/
│   └── Mini-AP-3.15/
├── AHRS/
│   └── AHRS-2.14/
└── Servo/
    └── Servo-1.08/
```## Mon
itoring and Notifications

### Notification Types

**Desktop Notifications (macOS):**
- System status updates
- USB drive processing completion
- GRT software update availability
- Error conditions requiring attention

**Email Notifications (Optional):**
- Critical system errors
- Weekly status summaries
- Major software updates
- Extended offline periods

### Configuring Notifications

**Enable/Disable Desktop Notifications:**
```yaml
# config/efis_config.yaml
notifications:
  enableDesktop: true
  desktopTimeout: 5000  # 5 seconds
```

**Configure Email Notifications:**
```yaml
notifications:
  enableEmail: true
  emailSettings:
    smtpServer: "smtp.gmail.com"
    smtpPort: 587
    username: "your-email@gmail.com"
    recipients:
      - "pilot@example.com"
```

### System Monitoring

**View Recent Activity:**
```bash
# macOS
./macos/efis logs --lines 50

# Windows  
windows\efis.bat logs --lines 50
```

**Monitor Specific Components:**
```bash
./macos/efis logs --component grt_scraper
./macos/efis logs --component usb_processor
windows\efis.bat logs --component sync_engine
```

**Real-time Log Monitoring:**
```bash
tail -f macos/logs/macos.log
```

### Performance Monitoring

**Check System Resources:**
```bash
./macos/efis diagnostics
windows\efis.bat diagnostics
```

**Monitor Sync Performance:**
- Average sync time: < 5 minutes for typical updates
- Network transfer rate: Depends on chart data size
- Error rate: Should be < 1% under normal conditions

## Troubleshooting Common Issues

### USB Drive Not Detected

**Symptoms:**
- USB drive inserted but no processing notification
- Drive appears in Finder but not processed

**Solutions:**
1. **Check Drive Format**: Ensure drive is FAT32 or exFAT
2. **Add Identification Marker**:
   ```bash
   echo "EFIS Data Drive" > /Volumes/USB_DRIVE/EFIS_DRIVE.txt
   ```
3. **Manual Processing**:
   ```bash
   ./macos/efis process-usb /Volumes/USB_DRIVE --force
   ```

### Chart Data Not Syncing

**Symptoms:**
- Windows shows sync success but macOS doesn't have new files
- Sync operations timing out

**Solutions:**
1. **Check Network Connectivity**:
   ```cmd
   ping 192.168.1.100  # macOS IP
   ```
2. **Verify SSH Access**:
   ```cmd
   ssh mwalker@192.168.1.100
   ```
3. **Force Manual Sync**:
   ```cmd
   windows\efis.bat sync --force
   ```

### GRT Updates Not Downloading

**Symptoms:**
- No update notifications despite known updates
- HTTP errors in logs

**Solutions:**
1. **Check Internet Connection**:
   ```bash
   curl -I https://grtavionics.com
   ```
2. **Manual Update Check**:
   ```bash
   ./macos/efis check-updates --verbose
   ```
3. **Clear Update Cache**:
   ```bash
   rm -rf ~/.efis/cache/grt-*
   ```

### System Performance Issues

**Symptoms:**
- Slow sync operations
- High CPU or memory usage
- Frequent timeouts

**Solutions:**
1. **Check Available Resources**:
   ```bash
   ./macos/efis diagnostics
   ```
2. **Adjust Sync Settings**:
   ```yaml
   windows:
     syncInterval: 3600  # Reduce frequency
     syncTimeout: 600    # Increase timeout
   ```
3. **Monitor Log Files**:
   ```bash
   ./macos/efis logs --component performance
   ```

## Maintenance Tasks

### Weekly Maintenance

**Every Week:**
1. **Check System Status**: Verify both systems operational
2. **Review Logs**: Look for recurring errors or warnings
3. **Verify Backups**: Ensure Dropbox sync is current
4. **Test USB Processing**: Process a test USB drive
5. **Check Available Storage**: Ensure adequate disk space

### Monthly Maintenance

**Every Month:**
1. **Update Software**: Check for EFIS Data Manager updates
2. **Archive Old Logs**: Clean up log files older than 30 days
3. **Verify Configuration**: Review and update settings as needed
4. **Test Recovery**: Verify backup and recovery procedures
5. **Performance Review**: Analyze system performance metrics

### Quarterly Maintenance

**Every Quarter:**
1. **Full System Test**: Test all components end-to-end
2. **Configuration Backup**: Save current configuration
3. **Documentation Review**: Update any custom procedures
4. **Network Security**: Review SSH keys and access
5. **Capacity Planning**: Assess storage and performance needs

### Log File Management

**Automatic Log Rotation:**
- Log files automatically rotate at 10MB
- 5 backup files retained by default
- Older logs automatically deleted

**Manual Log Cleanup:**
```bash
# Remove logs older than 30 days
find logs/ -name "*.log.*" -mtime +30 -delete

# Archive current logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Configuration Backup

**Backup Configuration:**
```bash
# Create configuration backup
cp -r config/ config-backup-$(date +%Y%m%d)/

# Include in version control
git add config/
git commit -m "Update configuration"
```

**Restore Configuration:**
```bash
# Restore from backup
cp -r config-backup-YYYYMMDD/ config/

# Restart services
./macos/efis daemon restart
windows\efis.bat service restart
```

### System Updates

**Check for Updates:**
```bash
git pull origin main
```

**Apply Updates:**
```bash
# Update dependencies
cd macos && pip install -r requirements.txt
cd windows && pip install -r requirements.txt

# Restart services
./macos/efis daemon restart
windows\efis.bat service restart
```

This user manual provides comprehensive guidance for operating the EFIS Data Manager system. For additional support, refer to the troubleshooting guide or contact technical support.