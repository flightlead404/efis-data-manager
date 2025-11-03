#!/usr/bin/env python3
"""
Test script for USB drive update functionality.
"""

import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from efis_macos.usb_drive_updater import (
    UpdateFile,
    UpdateProgress,
    FileIntegrityVerifier,
    IncrementalCopyManager,
    USBDriveUpdater
)
from efis_macos.config import MacOSConfig


def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_test_source_files(source_dir: Path):
    """Create test source files for updating."""
    print("Creating test source files...")
    
    # Create navigation database files
    nav_dir = source_dir / "navigation"
    nav_dir.mkdir(parents=True)
    
    nav_files = [
        ("NAV.DB", b"Navigation database content v2.1"),
        ("WAYPOINTS.DB", b"Waypoint database content"),
        ("CHARTS.DB", b"Chart database content")
    ]
    
    for filename, content in nav_files:
        (nav_dir / filename).write_bytes(content)
        print(f"  Created: navigation/{filename}")
    
    # Create software update files
    software_dir = source_dir / "software"
    software_dir.mkdir(parents=True)
    
    software_files = [
        ("EFIS_UPDATE.bin", b"EFIS software update binary"),
        ("CONFIG.xml", b"<config><version>1.2.3</version></config>"),
        ("README.txt", b"Software update instructions")
    ]
    
    for filename, content in software_files:
        (software_dir / filename).write_bytes(content)
        print(f"  Created: software/{filename}")


def create_test_drive_files(drive_dir: Path):
    """Create existing files on test drive."""
    print("Creating existing drive files...")
    
    # Create some existing files (older versions)
    nav_dir = drive_dir / "navigation"
    nav_dir.mkdir(parents=True)
    
    # Old navigation database
    (nav_dir / "NAV.DB").write_bytes(b"Navigation database content v2.0")
    print("  Created: navigation/NAV.DB (old version)")
    
    # Missing waypoints file (will be copied)
    # Missing charts file (will be copied)
    
    # Create software directory with old config
    software_dir = drive_dir / "software"
    software_dir.mkdir(parents=True)
    
    (software_dir / "CONFIG.xml").write_bytes(b"<config><version>1.2.2</version></config>")
    print("  Created: software/CONFIG.xml (old version)")


def test_update_file_creation():
    """Test UpdateFile creation and parsing."""
    print("\nTesting UpdateFile Creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a test file
        test_file = temp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Create UpdateFile
        update_file = UpdateFile.from_source(test_file, "test.txt")
        
        print(f"  ✓ Source path: {update_file.source_path}")
        print(f"  ✓ Dest path: {update_file.dest_path}")
        print(f"  ✓ Size: {update_file.size} bytes")
        print(f"  ✓ Last modified: {update_file.last_modified}")


def test_file_integrity_verification():
    """Test file integrity verification."""
    print("\nTesting File Integrity Verification...")
    
    verifier = FileIntegrityVerifier()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create identical files
        file1 = temp_path / "file1.txt"
        file2 = temp_path / "file2.txt"
        content = b"Test content for integrity verification"
        
        file1.write_bytes(content)
        file2.write_bytes(content)
        
        # Test identical files
        assert verifier.verify_file_integrity(file1, file2), "Identical files should verify"
        print("  ✓ Identical files verified correctly")
        
        # Create different file
        file3 = temp_path / "file3.txt"
        file3.write_bytes(b"Different content")
        
        # Test different files
        assert not verifier.verify_file_integrity(file1, file3), "Different files should not verify"
        print("  ✓ Different files rejected correctly")
        
        # Test checksum calculation
        checksum1 = verifier.calculate_checksum(file1)
        checksum2 = verifier.calculate_checksum(file2)
        checksum3 = verifier.calculate_checksum(file3)
        
        assert checksum1 == checksum2, "Identical files should have same checksum"
        assert checksum1 != checksum3, "Different files should have different checksums"
        print(f"  ✓ Checksums: {checksum1[:8]}... (identical), {checksum3[:8]}... (different)")


def test_incremental_copy():
    """Test incremental file copying."""
    print("\nTesting Incremental Copy...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "destination"
        
        create_test_source_files(source_dir)
        create_test_drive_files(dest_dir)
        
        # Create config
        config = MacOSConfig(
            archive_path=str(temp_path / "archive"),
            demo_path=str(temp_path / "demo"),
            logbook_path=str(temp_path / "logbook")
        )
        
        # Test incremental copy
        copy_manager = IncrementalCopyManager(config)
        
        # Get files to update
        update_files = copy_manager.get_update_files([str(source_dir)], dest_dir)
        
        print(f"  Files to update: {len(update_files)}")
        for update_file in update_files:
            print(f"    - {update_file.dest_path} ({update_file.size} bytes)")
        
        # Progress callback for testing
        def progress_callback(progress: UpdateProgress):
            print(f"    Progress: {progress.progress_percent:.1f}% "
                  f"({progress.files_copied}/{progress.total_files} files, "
                  f"{progress.bytes_copied / 1024:.1f}KB)")
        
        # Copy files
        results = copy_manager.copy_files_incremental(update_files, dest_dir, progress_callback)
        
        print(f"  Copy results:")
        print(f"    Success: {results['success']}")
        print(f"    Files copied: {results['files_copied']}")
        print(f"    Files verified: {results['files_verified']}")
        print(f"    Files failed: {results['files_failed']}")
        print(f"    Bytes copied: {results['bytes_copied']}")
        
        if results['errors']:
            print(f"    Errors: {results['errors']}")


def test_usb_drive_updater():
    """Test complete USB drive update process."""
    print("\nTesting USB Drive Updater...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create directory structure
        source_dir = temp_path / "source"
        drive_dir = temp_path / "usb_drive"
        archive_dir = temp_path / "archive"
        
        create_test_source_files(source_dir)
        create_test_drive_files(drive_dir)
        
        # Create config
        config = MacOSConfig(
            archive_path=str(archive_dir),
            demo_path=str(temp_path / "demo"),
            logbook_path=str(temp_path / "logbook")
        )
        
        # Test USB drive updater
        updater = USBDriveUpdater(config)
        
        # Progress callback
        def progress_callback(progress: UpdateProgress):
            if progress.current_file:
                print(f"    Updating: {progress.current_file}")
        
        # Update drive
        results = updater.update_drive(
            str(drive_dir), 
            "/dev/disk99s1",  # Fake device path
            update_sources=[str(source_dir)],
            progress_callback=progress_callback
        )
        
        print(f"  Update results:")
        print(f"    Success: {results['success']}")
        print(f"    Files updated: {results['files_updated']}")
        print(f"    Bytes transferred: {results['bytes_transferred']}")
        
        if results['errors']:
            print(f"    Errors: {results['errors']}")
        if results['warnings']:
            print(f"    Warnings: {results['warnings']}")
        
        # Verify files were updated
        print(f"\n  Verifying updated files:")
        for file_path in drive_dir.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(drive_dir)
                print(f"    - {rel_path}")


def main():
    """Main test function."""
    setup_logging()
    
    print("USB Drive Updater Test")
    print("=" * 40)
    
    try:
        test_update_file_creation()
        test_file_integrity_verification()
        test_incremental_copy()
        test_usb_drive_updater()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())