# EFIS USB Drive Preparation and Management Guide

This guide provides detailed instructions for preparing, managing, and troubleshooting EFIS USB drives used with the GRT Avionics systems.

## Table of Contents

- [USB Drive Requirements](#usb-drive-requirements)
- [Preparing New EFIS USB Drives](#preparing-new-efis-usb-drives)
- [USB Drive File Structure](#usb-drive-file-structure)
- [Processing Existing USB Drives](#processing-existing-usb-drives)
- [Troubleshooting USB Drive Issues](#troubleshooting-usb-drive-issues)
- [Best Practices](#best-practices)

## USB Drive Requirements

### Hardware Requirements

**Recommended USB Drive Specifications:**
- **Capacity**: 32GB or larger (64GB recommended for complete chart sets)
- **Speed**: USB 3.0 or faster for better transfer performance
- **Format**: FAT32 or exFAT (required for GRT compatibility)
- **Quality**: Use reliable brands (SanDisk, Kingston, Samsung, etc.)
- **Physical**: Standard USB-A connector for aircraft compatibility

**Compatibility Notes:**
- GRT systems require FAT32 or exFAT file systems
- NTFS is not supported by GRT avionics
- USB-C drives require adapter for most aircraft installations
- Very large drives (>128GB) may have slower formatting times

### File System Requirements

**FAT32 (Recommended for drives ≤32GB):**
- Maximum file size: 4GB
- Maximum partition size: 32GB
- Best compatibility with older GRT systems
- Faster formatting and file operations

**exFAT (Required for drives >32GB):**
- No practical file size limit
- Supports larger partitions
- Required for drives larger than 32GB
- Supported by newer GRT systems (check compatibility)

## Preparing New EFIS USB Drives

### Automatic Preparation (Recommended)

The EFIS Data Manager can automatically prepare new USB drives with all current data:

```bash
# Insert USB drive into macOS system
# Run automatic preparation
./macos/efis prepare-usb /Volumes/USB_DRIVE_NAME

# For drives that need formatting
./macos/efis prepare-usb /Volumes/USB_DRIVE_NAME --format

# Force preparation even if drive has existing data
./macos/efis prepare-usb /Volumes/USB_DRIVE_NAME --force
```

**Automatic Preparation Process:**
1. **Drive Detection**: Verifies USB drive is accessible
2. **Format Check**: Ensures proper file system (FAT32/exFAT)
3. **Identification Setup**: Creates EFIS drive markers
4. **Chart Data Copy**: Copies complete current chart archive
5. **NAV Database**: Copies current navigation database
6. **GRT Software**: Copies latest GRT software updates
7. **Verification**: Confirms all files copied successfully

### Manual Preparation Steps

If automatic preparation fails or you prefer manual setup:

#### Step 1: Format the USB Drive

**Using macOS Disk Utility:**
1. Open Disk Utility (Applications > Utilities)
2. Select the USB drive
3. Click "Erase"
4. Choose format:
   - **MS-DOS (FAT)** for drives ≤32GB
   - **exFAT** for drives >32GB
5. Name the drive (e.g., "EFIS_USB")
6. Click "Erase"

**Using Command Line:**
```bash
# List available drives
diskutil list

# Format as FAT32 (for drives ≤32GB)
sudo diskutil eraseDisk FAT32 EFIS_USB /dev/diskX

# Format as exFAT (for drives >32GB)  
sudo diskutil eraseDisk exFAT EFIS_USB /dev/diskX
```

#### Step 2: Create EFIS Identification Markers

```bash
# Navigate to mounted USB drive
cd /Volumes/EFIS_USB

# Create identification file
echo "EFIS Data Drive - $(date)" > EFIS_DRIVE.txt

# Create GRT data directory
mkdir -p GRT_DATA

# Create version tracking file
echo "Prepared: $(date)" > DRIVE_INFO.txt
echo "System: EFIS Data Manager" >> DRIVE_INFO.txt
```

#### Step 3: Copy Chart Data

```bash
# Copy complete chart archive
cp -r "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/"* /Volumes/EFIS_USB/

# Verify copy completed successfully
echo "Chart data copied: $(date)" >> /Volumes/EFIS_USB/DRIVE_INFO.txt
```

#### Step 4: Copy NAV Database

```bash
# Copy current NAV database
cp "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/NAV.DB" /Volumes/EFIS_USB/

# Verify NAV database
ls -la /Volumes/EFIS_USB/NAV.DB
echo "NAV database: $(ls -la /Volumes/EFIS_USB/NAV.DB | awk '{print $9, $5, $6, $7, $8}')" >> /Volumes/EFIS_USB/DRIVE_INFO.txt
```

#### Step 5: Copy GRT Software (if available)

```bash
# Copy GRT software updates
if [ -d "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/GRT-Software" ]; then
    cp -r "/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB/GRT-Software/"* /Volumes/EFIS_USB/
    echo "GRT software copied: $(date)" >> /Volumes/EFIS_USB/DRIVE_INFO.txt
fi
```

## USB Drive File Structure

### Standard EFIS USB Drive Layout

```
EFIS_USB/
├── EFIS_DRIVE.txt              # Drive identification marker
├── DRIVE_INFO.txt              # Drive preparation information
├── NAV.DB                      # Navigation database (updated every 28 days)
├── GRT_DATA/                   # GRT-specific data directory
├── Charts/                     # Chart data directory structure
│   ├── Sectional/             # Sectional charts
│   │   ├── Seattle/
│   │   ├── Portland/
│   │   └── ...
│   ├── Low_Altitude/          # Low altitude charts
│   ├── High_Altitude/         # High altitude charts
│   └── Approach_Plates/       # Approach procedures
├── Software/                   # GRT software updates (when available)
│   ├── HXr/                   # HXr display software
│   ├── Mini-AP/               # Mini autopilot software
│   ├── AHRS/                  # AHRS software
│   └── Servo/                 # Servo software
└── Logs/                      # Flight data (populated by aircraft)
    ├── DEMO-YYYYMMDD-HHMMSS.LOG
    ├── Logbook.csv
    └── *.png (snapshots)
```

### File Size Estimates

**Typical File Sizes:**
- **Complete Chart Set**: 15-25GB (varies by region and currency)
- **NAV Database**: 50-100MB
- **GRT Software Package**: 10-50MB per component
- **Demo Files**: 1-10MB per flight
- **Snapshot Files**: 100KB-1MB per image
- **Logbook Files**: 10-100KB per file

**Recommended Drive Sizes:**
- **32GB**: Sufficient for charts + NAV database
- **64GB**: Recommended for charts + software + flight data
- **128GB**: Ample space for multiple chart cycles and extensive flight data

## Processing Existing USB Drives

### Automatic Processing

When you insert an EFIS USB drive that contains flight data:

```bash
# System automatically detects and processes
# Manual processing if needed:
./macos/efis process-usb /Volumes/EFIS_USB

# Dry run to see what would be processed
./macos/efis process-usb /Volumes/EFIS_USB --dry-run

# Process with verbose output
./macos/efis process-usb /Volumes/EFIS_USB --verbose
```

### Processing Workflow

**Automatic Processing Steps:**
1. **Drive Detection**: Identifies EFIS drive by markers
2. **File Inventory**: Catalogs demo files, snapshots, and logbooks
3. **File Processing**:
   - Demo files → `/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO/`
   - Snapshot files → `/Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO/`
   - Logbook files → `/Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks/` (renamed with dates)
4. **Drive Updates**:
   - Copy new chart data if available
   - Update NAV database if newer version available
   - Copy GRT software updates if available
5. **Verification**: Confirm all operations completed successfully
6. **Notification**: Alert user of processing completion

### File Processing Details

**Demo File Processing:**
- **Source Pattern**: `DEMO-YYYYMMDD-HHMMSS.LOG` or `DEMO-YYYYMMDD-HHMMSS+N.LOG`
- **Target Location**: Demo archive directory
- **Processing**: Files moved (not copied) to preserve USB space
- **Naming**: Original filename preserved

**Snapshot File Processing:**
- **Source Pattern**: `*.png`, `*.jpg`, `*.bmp`
- **Target Location**: Demo archive directory
- **Processing**: Files moved to preserve USB space
- **Organization**: Grouped by date if possible

**Logbook File Processing:**
- **Source Pattern**: `*.csv`, `Logbook*.csv`
- **Target Location**: Logbook archive directory
- **Processing**: Files moved and renamed
- **Naming Convention**: `Logbook YYYY-MM-DD.csv` (based on file date)

## Troubleshooting USB Drive Issues

### Drive Not Detected

**Symptoms:**
- USB drive inserted but no processing notification
- Drive appears in Finder but system doesn't recognize it as EFIS drive

**Diagnosis:**
```bash
# Check if drive is mounted
ls -la /Volumes/

# Check for EFIS markers
ls -la /Volumes/USB_DRIVE_NAME/EFIS_DRIVE.txt
ls -la /Volumes/USB_DRIVE_NAME/GRT_DATA/

# Test manual detection
./macos/efis detect-drive /Volumes/USB_DRIVE_NAME
```

**Solutions:**
1. **Add EFIS Markers**:
   ```bash
   echo "EFIS Data Drive" > /Volumes/USB_DRIVE_NAME/EFIS_DRIVE.txt
   mkdir -p /Volumes/USB_DRIVE_NAME/GRT_DATA
   ```

2. **Check File System**:
   ```bash
   diskutil info /Volumes/USB_DRIVE_NAME
   # Should show FAT32 or exFAT
   ```

3. **Reformat if Necessary**:
   ```bash
   # Backup data first, then reformat
   sudo diskutil eraseDisk FAT32 EFIS_USB /dev/diskX
   ```

### Processing Failures

**Symptoms:**
- Processing starts but fails partway through
- Error messages about file operations
- Incomplete file transfers

**Common Causes and Solutions:**

1. **Insufficient Space**:
   ```bash
   # Check available space
   df -h /Volumes/USB_DRIVE_NAME
   
   # Clean up old files if needed
   rm /Volumes/USB_DRIVE_NAME/old_files*
   ```

2. **File Permission Issues**:
   ```bash
   # Fix permissions
   sudo chmod -R 755 /Volumes/USB_DRIVE_NAME
   ```

3. **Corrupted Files**:
   ```bash
   # Check file system
   sudo fsck_msdos /dev/diskXsY
   ```

### Slow Transfer Speeds

**Symptoms:**
- USB operations take much longer than expected
- Transfer speeds below 10MB/s

**Solutions:**

1. **Check USB Port Speed**:
   - Use USB 3.0 ports when available
   - Avoid USB hubs if possible
   - Try different USB ports

2. **Optimize File Operations**:
   ```bash
   # Use rsync for better performance
   rsync -av --progress source/ /Volumes/USB_DRIVE_NAME/
   ```

3. **Check Drive Health**:
   ```bash
   # Test drive speed
   dd if=/dev/zero of=/Volumes/USB_DRIVE_NAME/test.tmp bs=1m count=100
   rm /Volumes/USB_DRIVE_NAME/test.tmp
   ```

### File Corruption Issues

**Symptoms:**
- Files appear corrupted after transfer
- GRT system reports file errors
- Incomplete or truncated files

**Prevention:**
1. **Always Safely Eject**: Use "Eject" before removing drive
2. **Verify Transfers**: Check file sizes and checksums
3. **Use Quality Drives**: Invest in reliable USB drives
4. **Avoid Interruption**: Don't remove drive during operations

**Recovery:**
```bash
# Verify file integrity
shasum -a 256 /Volumes/USB_DRIVE_NAME/NAV.DB
shasum -a 256 /Users/mwalker/archive/NAV.DB

# Re-copy corrupted files
cp /Users/mwalker/archive/NAV.DB /Volumes/USB_DRIVE_NAME/
```

## Best Practices

### USB Drive Management

**Drive Labeling:**
- Use consistent naming: "EFIS_USB_1", "EFIS_USB_2", etc.
- Include preparation date on physical label
- Track drive usage and rotation

**Multiple Drive Strategy:**
- Maintain 2-3 prepared drives
- Rotate drives to prevent wear
- Keep one drive as backup with current data

**Drive Maintenance:**
- Reformat drives every 6 months
- Replace drives showing errors or slow performance
- Keep drives in protective cases when not in use

### Data Management

**Regular Updates:**
- Process USB drives after each flight
- Update drives with latest chart data monthly
- Verify NAV database currency (28-day cycle)

**Backup Strategy:**
- Maintain archive of all flight data
- Backup USB drive contents before major updates
- Keep offline backup of critical chart data

**Version Control:**
- Track chart data versions and dates
- Document GRT software versions on drives
- Maintain log of drive preparation dates

### Operational Procedures

**Pre-Flight:**
- Verify USB drive has current data
- Check drive for physical damage
- Confirm drive is properly seated in aircraft

**Post-Flight:**
- Process USB drive promptly after flight
- Verify flight data was captured
- Check for any error messages or warnings

**Maintenance:**
- Clean USB connectors regularly
- Store drives in dry, temperature-controlled environment
- Replace drives showing signs of wear or unreliability

This guide provides comprehensive information for managing EFIS USB drives effectively. For additional support with USB drive issues, refer to the troubleshooting section or contact technical support.