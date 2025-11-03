#!/usr/bin/env python3
"""
Test script for USB drive detection functionality.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from efis_macos.usb_drive_processor import (
    USBDriveDetector, 
    EFISDriveIdentifier, 
    USBDriveValidator,
    SafeDriveAccess
)


def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_usb_detection():
    """Test USB drive detection."""
    print("Testing USB Drive Detection...")
    print("  → Running 'diskutil' and 'mount' commands to detect USB drives...")
    
    detector = USBDriveDetector()
    
    # Check permissions first
    if not detector.check_permissions():
        print("  ❌ WARNING: Insufficient permissions for USB detection")
        print("  You may need to grant 'Full Disk Access' in System Preferences > Security & Privacy")
        return
    
    drives = detector.get_mounted_drives()
    
    print(f"  ✅ Found {len(drives)} USB drives:")
    if len(drives) == 0:
        print("    No USB drives detected (this is normal if no USB drives are connected)")
    else:
        for drive in drives:
            print(f"    - {drive['mount_path']} ({drive.get('volume_name', 'Unknown')})")
            print(f"      Device: {drive['device_path']}")
            print(f"      Capacity: {drive.get('capacity', 0) / (1024**3):.1f} GB")
            print(f"      File System: {drive.get('file_system', 'Unknown')}")
    print()


def test_efis_identification():
    """Test EFIS drive identification."""
    print("Testing EFIS Drive Identification...")
    print("  → Scanning USB drive contents to identify EFIS drives...")
    print("    (This may trigger permission requests to access drive contents)")
    
    detector = USBDriveDetector()
    identifier = EFISDriveIdentifier()
    
    drives = detector.get_mounted_drives()
    
    if len(drives) == 0:
        print("  No USB drives to test (connect a USB drive to test EFIS identification)")
    else:
        for drive in drives:
            print(f"  Checking drive: {drive['mount_path']}")
            
            is_efis = identifier.is_efis_drive(drive)
            print(f"    Is EFIS drive: {is_efis}")
            
            if is_efis:
                efis_info = identifier.get_efis_drive_info(drive)
                if efis_info:
                    print(f"    EFIS ID: {efis_info.identifier}")
                    print(f"    Demo files: {len(efis_info.demo_files)}")
                    print(f"    Snap files: {len(efis_info.snap_files)}")
                    print(f"    Logbook files: {len(efis_info.logbook_files)}")
    print()


def test_drive_validation():
    """Test drive validation."""
    print("Testing Drive Validation...")
    
    detector = USBDriveDetector()
    validator = USBDriveValidator()
    
    drives = detector.get_mounted_drives()
    
    if len(drives) == 0:
        print("  No USB drives to validate")
    else:
        for drive in drives:
            print(f"Validating drive: {drive['mount_path']}")
            
            is_valid, errors = validator.validate_drive(drive)
            print(f"  Valid: {is_valid}")
            
            if errors:
                print("  Errors:")
                for error in errors:
                    print(f"    - {error}")
    print()


def test_safe_access():
    """Test safe drive access."""
    print("Testing Safe Drive Access...")
    print("  → Testing read/write permissions on USB drives...")
    
    detector = USBDriveDetector()
    safe_access = SafeDriveAccess()
    
    drives = detector.get_mounted_drives()
    
    if len(drives) == 0:
        print("  No USB drives to test access")
    else:
        for drive in drives:
            mount_path = drive['mount_path']
            print(f"  Testing access to: {mount_path}")
            
            accessible = safe_access.is_drive_accessible(mount_path)
            print(f"    Accessible: {accessible}")
            
            if accessible:
                free_space = safe_access.get_available_space(mount_path)
                print(f"    Free space: {free_space / (1024**3):.1f} GB")
    print()


def main():
    """Main test function."""
    setup_logging()
    
    print("EFIS USB Drive Detection Test")
    print("=" * 40)
    print()
    
    print("⚠️  PERMISSION WARNING:")
    print("This test will access USB drives and system information.")
    print("macOS may show permission dialogs asking for:")
    print("  • 'Access data from other apps' - ALLOW this to detect USB drives")
    print("  • 'Full Disk Access' - ALLOW this to scan drive contents")
    print()
    print("These permissions are needed to:")
    print("  - Detect connected USB drives using system utilities")
    print("  - Scan drive contents to identify EFIS drives")
    print("  - Validate drive capacity and file system")
    print()
    
    try:
        input("Press Enter to continue with the test (or Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        return 0
    
    print()
    
    try:
        test_usb_detection()
        test_efis_identification()
        test_drive_validation()
        test_safe_access()
        
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())