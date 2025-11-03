# Requirements Document

## Introduction

The EFIS Data Manager is a cross-platform system that automates the management of aviation chart data, navigation databases, logging data, and software updates between a MacBook Pro, Windows 11 machine, and aircraft EFIS systems via USB drives. The system ensures data synchronization, automatic updates, and seamless file transfers while maintaining data integrity and providing user notifications.

## Glossary

- **EFIS_System**: Electronic Flight Information System consisting of primary GRT HXr and secondary Mini A/P displays
- **Chart_Data**: FAA published sectional, low altitude, and IFR procedures data consisting of thousands of PNG files in directory structure
- **Chart_Manager**: Seattle Avionics Chart Manager agent running on Windows 11
- **Virtual_USB_Drive**: Software-mounted drive (E:) on Windows 11 containing chart data
- **MacBook_System**: macOS-based system responsible for USB management and GRT downloads
- **Windows_System**: Windows 11 machine running Chart Manager and virtual USB drive
- **USB_Drive**: Physical USB storage device used for data transfer with EFIS systems
- **Demo_Files**: Flight data logging files with format DEMO-YYYYMMDD-HHMMSS[+#].LOG
- **Snap_Files**: Screenshot PNG files captured by EFIS system
- **Logbook_Files**: CSV files containing flight logbook data
- **NAV_Database**: Navigation database file (NAV.DB) updated every 28 days
- **GRT_Software**: Firmware and software files for EFIS, autopilot, and AHRS systems

## Requirements

### Requirement 1

**User Story:** As a pilot, I want the Windows system to automatically maintain the virtual USB drive connection, so that chart updates are never interrupted due to drive dismounting.

#### Acceptance Criteria

1. SHORTLY AFTER the Windows_System starts, THE Windows_System SHALL verify Virtual_USB_Drive is mounted at E: drive
2. WHILE the Windows_System is running, THE Windows_System SHALL check Virtual_USB_Drive mount status every 5 minutes
3. IF Virtual_USB_Drive becomes dismounted, THEN THE Windows_System SHALL automatically remount the drive
4. WHEN Virtual_USB_Drive remounting fails, THE Windows_System SHALL log the error and retry after 1 minute
5. THE Windows_System SHALL maintain a log of all mount/dismount events with timestamps

### Requirement 2

**User Story:** As a pilot, I want chart data to be automatically synchronized from Windows to MacBook, so that I always have the latest charts available for USB transfer.

#### Acceptance Criteria

1. WHEN both Windows_System and MacBook_System are on the same network, THE Windows_System SHALL initiate file synchronization every 30 minutes
2. THE Windows_System SHALL verify network connectivity to MacBook_System before attempting synchronization
3. THE Windows_System SHALL transfer only new or modified files from Virtual_USB_Drive to MacBook_System
4. THE Windows_System SHALL preserve all directory structures and hidden files during transfer
5. WHEN synchronization fails, THE Windows_System SHALL retry after 10 minutes for maximum 3 attempts

### Requirement 3

**User Story:** As a pilot, I want the MacBook to automatically download and manage GRT software updates, so that I can keep my EFIS systems current without manual intervention.

#### Acceptance Criteria

1. THE MacBook_System SHALL check for NAV_Database updates daily at 01:00 local time
2. THE MacBook_System SHALL check for GRT_Software updates daily at 01:30 local time
3. WHEN NAV_Database is updated, THE MacBook_System SHALL download the file and compare with previous version
4. WHEN GRT_Software version changes are detected, THE MacBook_System SHALL download the new software files
5. THE MacBook_System SHALL store all downloaded files in local archive at /Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-USB

### Requirement 4

**User Story:** As a pilot, I want automatic detection and processing of EFIS USB drives, so that flight data is safely archived and the drive is updated with current information.

#### Acceptance Criteria

1. WHEN USB_Drive is inserted into MacBook_System, THE MacBook_System SHALL detect the drive within 5 seconds
2. THE MacBook_System SHALL identify EFIS drives using file system markers rather than drive names
3. WHEN EFIS USB_Drive is detected, THE MacBook_System SHALL move Demo_Files to /Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO
4. THE MacBook_System SHALL move Snap_Files to /Users/mwalker/Library/CloudStorage/Dropbox/Flying/EFIS-DEMO
5. THE MacBook_System SHALL move Logbook_Files to /Users/mwalker/Library/CloudStorage/Dropbox/Flying/Logbooks with renamed format "Logbook YYYY-MM-DD.csv"

### Requirement 5

**User Story:** As a pilot, I want the USB drive to be automatically updated with current chart data and software, so that my EFIS systems have the latest information.

#### Acceptance Criteria

1. WHEN EFIS USB_Drive is processed, THE MacBook_System SHALL copy new or updated chart files from local archive
2. WHEN new NAV_Database is available, THE MacBook_System SHALL copy NAV.DB to USB_Drive root directory
3. WHEN new GRT_Software is available, THE MacBook_System SHALL copy software files to USB_Drive root directory
4. THE MacBook_System SHALL verify file integrity after copying to USB_Drive
5. THE MacBook_System SHALL notify user of any software or database updates copied to USB_Drive

### Requirement 6

**User Story:** As a pilot, I want to be notified of system status and any issues, so that I can take appropriate action when needed.

#### Acceptance Criteria

1. WHEN NAV_Database is updated, THE MacBook_System SHALL display notification "New NAV database available"
2. WHEN GRT_Software is updated, THE MacBook_System SHALL display notification specifying software type and version
3. WHEN USB_Drive processing completes, THE MacBook_System SHALL display summary of files transferred
4. WHEN synchronization or download errors occur, THE MacBook_System SHALL display error notification with recommended action
5. THE MacBook_System SHALL maintain detailed logs of all operations with timestamps

### Requirement 7

**User Story:** As a pilot, I want to prepare new EFIS USB drives, so that they are properly configured for use with the system.

#### Acceptance Criteria

1. THE MacBook_System SHALL provide command to initialize new EFIS USB drives
2. WHEN initializing USB_Drive, THE MacBook_System SHALL create identification markers for EFIS drive detection
3. THE MacBook_System SHALL copy complete current chart data archive to new USB_Drive
4. THE MacBook_System SHALL copy current NAV_Database to new USB_Drive root directory
5. THE MacBook_System SHALL copy current GRT_Software files to new USB_Drive root directory

### Requirement 8

**User Story:** As a pilot, I want robust error handling and recovery, so that temporary issues don't disrupt the automated processes.

#### Acceptance Criteria

1. WHEN network connectivity is lost, THE Windows_System SHALL pause synchronization and resume when connectivity returns without error accumulation during extended offline periods
2. WHEN USB_Drive read/write errors occur, THE MacBook_System SHALL retry operation up to 3 times
3. WHEN GRT website links are broken or changed, THE MacBook_System SHALL log error and continue with other operations
4. WHEN file system errors occur, THE MacBook_System SHALL attempt recovery and notify user if manual intervention required
5. THE MacBook_System SHALL maintain operation logs for troubleshooting purposes