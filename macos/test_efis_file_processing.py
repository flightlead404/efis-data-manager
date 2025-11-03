#!/usr/bin/env python3
"""
Test script for EFIS file processing functionality.
"""

import sys
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from efis_macos.efis_file_processor import (
    DemoFileInfo,
    SnapshotFileInfo, 
    LogbookFileInfo,
    EFISFileProcessor
)
from efis_macos.config import MacOSConfig


def setup_logging():
    """Set up logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_test_files(test_drive: Path):
    """Create test EFIS files for processing."""
    print("Creating test EFIS files...")
    
    # Create demo files
    demo_dir = test_drive / "DEMO"
    demo_dir.mkdir(exist_ok=True)
    
    demo_files = [
        "DEMO-20241029-143000.LOG",
        "DEMO-20241029-150000+1.LOG",
        "DEMO-20241028-120000.LOG"
    ]
    
    for demo_file in demo_files:
        (demo_dir / demo_file).write_text(f"Demo flight data for {demo_file}")
        print(f"  Created: {demo_file}")
    
    # Create snapshot files
    snap_dir = test_drive / "SNAP"
    snap_dir.mkdir(exist_ok=True)
    
    snapshot_files = [
        "SNAP_20241029_143000.png",
        "Screenshot_2024-10-29_14-30-00.png",
        "display_capture.png"
    ]
    
    for snap_file in snapshot_files:
        (snap_dir / snap_file).write_bytes(b"PNG fake image data")
        print(f"  Created: {snap_file}")
    
    # Create logbook file
    logbook_content = """Date,Flight Time,Aircraft,Departure,Arrival,Notes
2024-10-29,1.5,N12345,KPAO,KSQL,Practice approaches
2024-10-28,2.0,N12345,KSQL,KPAO,Cross country flight
2024-10-27,1.0,N12345,KPAO,KPAO,Pattern work"""
    
    (test_drive / "logbook.csv").write_text(logbook_content)
    print("  Created: logbook.csv")


def test_demo_file_parsing():
    """Test demo file parsing."""
    print("\nTesting Demo File Parsing...")
    
    test_cases = [
        ("DEMO-20241029-143000.LOG", True, None),
        ("DEMO-20241029-150000+1.LOG", True, 1),
        ("DEMO-20241028-120000+5.LOG", True, 5),
        ("invalid-file.log", False, None),
        ("DEMO-invalid-format.LOG", False, None)
    ]
    
    for filename, should_parse, expected_flight_num in test_cases:
        demo_info = DemoFileInfo.from_filename(filename, f"/test/{filename}")
        
        if should_parse:
            assert demo_info is not None, f"Should parse: {filename}"
            assert demo_info.flight_number == expected_flight_num, f"Flight number mismatch: {filename}"
            print(f"  ✓ Parsed: {filename} -> {demo_info.timestamp}, flight #{demo_info.flight_number}")
        else:
            assert demo_info is None, f"Should not parse: {filename}"
            print(f"  ✓ Rejected: {filename}")


def test_snapshot_file_parsing():
    """Test snapshot file parsing."""
    print("\nTesting Snapshot File Parsing...")
    
    test_cases = [
        "SNAP_20241029_143000.png",
        "Screenshot_2024-10-29_14-30-00.png",
        "display_capture.png",
        "random_image.png"
    ]
    
    for filename in test_cases:
        snapshot_info = SnapshotFileInfo.from_file(filename, f"/test/{filename}")
        
        if snapshot_info.timestamp:
            print(f"  ✓ Parsed timestamp: {filename} -> {snapshot_info.timestamp}")
        else:
            print(f"  ✓ No timestamp: {filename}")


def test_logbook_file_parsing():
    """Test logbook file parsing."""
    print("\nTesting Logbook File Parsing...")
    
    # Create a temporary logbook file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("""Date,Flight Time,Aircraft,Notes
2024-10-29,1.5,N12345,Test flight 1
2024-10-28,2.0,N12345,Test flight 2
2024-10-27,1.0,N12345,Test flight 3""")
        temp_path = f.name
    
    try:
        logbook_info = LogbookFileInfo.from_file("test_logbook.csv", temp_path)
        
        print(f"  ✓ Row count: {logbook_info.row_count}")
        if logbook_info.date_range:
            start, end = logbook_info.date_range
            print(f"  ✓ Date range: {start.date()} to {end.date()}")
        else:
            print("  ✓ No date range detected")
            
    finally:
        Path(temp_path).unlink()


def test_file_processing():
    """Test complete file processing."""
    print("\nTesting Complete File Processing...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test drive
        test_drive = temp_path / "test_drive"
        test_drive.mkdir()
        
        # Create archive directories
        demo_archive = temp_path / "demo_archive"
        logbook_archive = temp_path / "logbook_archive"
        
        # Create test configuration
        config = MacOSConfig(
            demo_path=str(demo_archive),
            logbook_path=str(logbook_archive),
            archive_path=str(temp_path / "archive")
        )
        
        # Create test files
        create_test_files(test_drive)
        
        # Process the files
        processor = EFISFileProcessor(config)
        results = processor.process_efis_drive(str(test_drive))
        
        print(f"  Processing results:")
        print(f"    Success: {results['success']}")
        print(f"    Demo files: {results['demo_files']['detected']} detected, {results['demo_files']['moved']} moved")
        print(f"    Snapshots: {results['snapshots']['detected']} detected, {results['snapshots']['moved']} moved")
        print(f"    Logbooks: {results['logbooks']['detected']} detected, {results['logbooks']['moved']} moved")
        print(f"    Total processed: {results['total_files_processed']}")
        
        if results['errors']:
            print(f"    Errors: {results['errors']}")
        
        # Verify files were moved
        print(f"\n  Verifying file moves:")
        
        # Check demo archive
        if demo_archive.exists():
            demo_files = list(demo_archive.glob("*.LOG"))
            print(f"    Demo archive: {len(demo_files)} files")
            for f in demo_files:
                print(f"      - {f.name}")
        
        # Check snapshot archive
        snapshot_dir = demo_archive / "snapshots"
        if snapshot_dir.exists():
            snap_files = list(snapshot_dir.glob("*.png"))
            print(f"    Snapshot archive: {len(snap_files)} files")
            for f in snap_files:
                print(f"      - {f.name}")
        
        # Check logbook archive
        if logbook_archive.exists():
            logbook_files = list(logbook_archive.glob("*.csv"))
            print(f"    Logbook archive: {len(logbook_files)} files")
            for f in logbook_files:
                print(f"      - {f.name}")


def main():
    """Main test function."""
    setup_logging()
    
    print("EFIS File Processing Test")
    print("=" * 40)
    
    try:
        test_demo_file_parsing()
        test_snapshot_file_parsing()
        test_logbook_file_parsing()
        test_file_processing()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())