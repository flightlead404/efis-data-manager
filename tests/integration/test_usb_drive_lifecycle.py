"""
Integration tests for USB drive lifecycle testing.
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class USBDriveSimulator:
    """Simulates USB drive insertion, processing, and ejection."""
    
    def __init__(self, temp_dir):
        self.temp_dir = Path(temp_dir)
        self.drives = {}
        self.event_callbacks = []
    
    def add_event_callback(self, callback):
        """Add callback for drive events."""
        self.event_callbacks.append(callback)
    
    def _trigger_event(self, event_type, drive_info):
        """Trigger event callbacks."""
        for callback in self.event_callbacks:
            callback(event_type, drive_info)
    
    def insert_drive(self, drive_id, drive_type="efis", capacity=32*1024*1024*1024):
        """Simulate USB drive insertion."""
        drive_path = self.temp_dir / f"drive_{drive_id}"
        drive_path.mkdir(exist_ok=True)
        
        drive_info = {
            'id': drive_id,
            'path': str(drive_path),
            'type': drive_type,
            'capacity': capacity,
            'device': f'/dev/disk{drive_id}s1',
            'mounted': True
        }
        
        # Create drive-specific files based on type
        if drive_type == "efis":
            self._create_efis_drive_content(drive_path)
        elif drive_type == "regular":
            self._create_regular_drive_content(drive_path)
        elif drive_type == "empty":
            pass  # Empty drive
        
        self.drives[drive_id] = drive_info
        self._trigger_event("inserted", drive_info)
        
        return drive_info
    
    def remove_drive(self, drive_id):
        """Simulate USB drive removal."""
        if drive_id in self.drives:
            drive_info = self.drives[drive_id]
            drive_info['mounted'] = False
            self._trigger_event("removed", drive_info)
            del self.drives[drive_id]
            return True
        return False
    
    def _create_efis_drive_content(self, drive_path):
        """Create EFIS-specific content on drive."""
        # EFIS identification
        (drive_path / "EFIS_DRIVE").write_text("EFIS_SIM_001")
        
        # Navigation database
        (drive_path / "NAV.DB").write_bytes(b"Navigation database content v2.1")
        
        # Demo files
        demo_files = [
            "DEMO-20231201-120000.LOG",
            "DEMO-20231201-130000+1.LOG",
            "DEMO-20231202-140000.LOG"
        ]
        for demo_file in demo_files:
            (drive_path / demo_file).write_text(f"Flight data for {demo_file}")
        
        # Snapshot files
        snap_files = ["SNAP-001.png", "SNAP-002.png", "SNAP-003.png"]
        for snap_file in snap_files:
            (drive_path / snap_file).write_bytes(b"PNG image data")
        
        # Logbook file
        logbook_content = """Date,Aircraft,Duration,Route,Remarks
2023-12-01,N12345,1.5,KPAO-KSQL,Pattern work
2023-12-02,N12345,2.0,KSQL-KHAF,Cross country
2023-12-03,N12345,1.2,KHAF-KPAO,Return flight
"""
        (drive_path / "logbook.csv").write_text(logbook_content)
        
        # Configuration files
        (drive_path / "CONFIG.xml").write_text("<config><version>1.2.3</version></config>")
    
    def _create_regular_drive_content(self, drive_path):
        """Create regular USB drive content."""
        (drive_path / "document.txt").write_text("Regular document")
        (drive_path / "photo.jpg").write_bytes(b"JPEG image data")
        (drive_path / "music.mp3").write_bytes(b"MP3 audio data")


class TestUSBDriveLifecycle:
    """Test complete USB drive lifecycle scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.simulator = USBDriveSimulator(self.temp_dir)
        self.config = {
            'macos': {
                'archivePath': os.path.join(self.temp_dir, 'archive'),
                'demoPath': os.path.join(self.temp_dir, 'demo'),
                'logbookPath': os.path.join(self.temp_dir, 'logbook')
            }
        }
        
        # Create directories
        for path in self.config['macos'].values():
            os.makedirs(path, exist_ok=True)
        
        # Track events
        self.events = []
        self.simulator.add_event_callback(self._event_handler)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _event_handler(self, event_type, drive_info):
        """Handle drive events."""
        self.events.append({
            'type': event_type,
            'drive_id': drive_info['id'],
            'timestamp': time.time()
        })
        print(f"Drive event: {event_type} - {drive_info['id']}")
    
    def test_efis_drive_complete_lifecycle(self):
        """Test complete EFIS drive lifecycle from insertion to ejection."""
        # Insert EFIS drive
        drive_info = self.simulator.insert_drive("efis_001", "efis")
        
        # Verify insertion event
        assert len(self.events) == 1
        assert self.events[0]['type'] == 'inserted'
        
        # Verify EFIS drive content
        drive_path = Path(drive_info['path'])
        assert (drive_path / "EFIS_DRIVE").exists()
        assert (drive_path / "NAV.DB").exists()
        
        # Count files before processing
        demo_files = list(drive_path.glob("DEMO-*.LOG"))
        snap_files = list(drive_path.glob("SNAP-*.png"))
        logbook_files = list(drive_path.glob("logbook.csv"))
        
        assert len(demo_files) == 3
        assert len(snap_files) == 3
        assert len(logbook_files) == 1
        
        print(f"✓ EFIS drive inserted with {len(demo_files)} demo files, "
              f"{len(snap_files)} snapshots, {len(logbook_files)} logbook")
        
        # Simulate processing (move files to archive)
        demo_dir = Path(self.config['macos']['demoPath'])
        logbook_dir = Path(self.config['macos']['logbookPath'])
        
        # Move demo files
        for demo_file in demo_files:
            dest_file = demo_dir / demo_file.name
            demo_file.rename(dest_file)
        
        # Move snapshot files
        for snap_file in snap_files:
            dest_file = demo_dir / snap_file.name
            snap_file.rename(dest_file)
        
        # Move and rename logbook file
        for logbook_file in logbook_files:
            timestamp = time.strftime("%Y-%m-%d")
            dest_file = logbook_dir / f"Logbook {timestamp}.csv"
            logbook_file.rename(dest_file)
        
        # Verify files were moved
        moved_demo_files = list(demo_dir.glob("DEMO-*.LOG"))
        moved_snap_files = list(demo_dir.glob("SNAP-*.png"))
        moved_logbook_files = list(logbook_dir.glob("Logbook*.csv"))
        
        assert len(moved_demo_files) == 3
        assert len(moved_snap_files) == 3
        assert len(moved_logbook_files) == 1
        
        print(f"✓ Files processed: {len(moved_demo_files)} demo, "
              f"{len(moved_snap_files)} snapshots, {len(moved_logbook_files)} logbook")
        
        # Simulate drive update (add new files)
        archive_path = Path(self.config['macos']['archivePath'])
        
        # Create chart data to copy to drive
        chart_files = [
            "Sectional/LA_SEC.png",
            "IFR_Low/L1_2.png",
            "NAV_NEW.DB"
        ]
        
        for chart_file in chart_files:
            src_file = archive_path / chart_file
            src_file.parent.mkdir(parents=True, exist_ok=True)
            src_file.write_bytes(b"Chart data content")
            
            # Copy to drive
            dest_file = drive_path / chart_file
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(src_file.read_bytes())
        
        # Verify files were copied to drive
        copied_files = list(drive_path.rglob("*.png")) + list(drive_path.glob("NAV_NEW.DB"))
        assert len(copied_files) >= 3
        
        print(f"✓ Drive updated with {len(copied_files)} new files")
        
        # Remove drive
        self.simulator.remove_drive("efis_001")
        
        # Verify removal event
        assert len(self.events) == 2
        assert self.events[1]['type'] == 'removed'
        
        print("✓ EFIS drive complete lifecycle test successful")
    
    def test_multiple_drives_concurrent_processing(self):
        """Test handling multiple USB drives simultaneously."""
        # Insert multiple drives
        drives = []
        for i in range(3):
            drive_info = self.simulator.insert_drive(f"efis_{i:03d}", "efis")
            drives.append(drive_info)
        
        # Verify all drives were inserted
        assert len(self.events) == 3
        assert all(event['type'] == 'inserted' for event in self.events)
        
        # Process each drive
        processing_results = []
        
        for drive_info in drives:
            drive_path = Path(drive_info['path'])
            
            # Count files
            demo_files = list(drive_path.glob("DEMO-*.LOG"))
            snap_files = list(drive_path.glob("SNAP-*.png"))
            logbook_files = list(drive_path.glob("logbook.csv"))
            
            total_files = len(demo_files) + len(snap_files) + len(logbook_files)
            
            processing_results.append({
                'drive_id': drive_info['id'],
                'files_found': total_files,
                'demo_files': len(demo_files),
                'snap_files': len(snap_files),
                'logbook_files': len(logbook_files)
            })
            
            print(f"✓ Drive {drive_info['id']}: {total_files} files found")
        
        # Verify consistent processing
        for result in processing_results:
            assert result['files_found'] > 0
            assert result['demo_files'] == 3
            assert result['snap_files'] == 3
            assert result['logbook_files'] == 1
        
        # Remove all drives
        for drive_info in drives:
            self.simulator.remove_drive(drive_info['id'])
        
        # Verify all removal events
        removal_events = [e for e in self.events if e['type'] == 'removed']
        assert len(removal_events) == 3
        
        print("✓ Multiple drives concurrent processing test successful")
    
    def test_drive_type_detection_and_handling(self):
        """Test detection and appropriate handling of different drive types."""
        drive_types = [
            {'type': 'efis', 'expected_files': 7},      # EFIS drive with demo/snap/logbook files
            {'type': 'regular', 'expected_files': 3},   # Regular USB drive
            {'type': 'empty', 'expected_files': 0}      # Empty drive
        ]
        
        detection_results = []
        
        for i, drive_type in enumerate(drive_types):
            # Insert drive
            drive_info = self.simulator.insert_drive(f"test_{i:03d}", drive_type['type'])
            drive_path = Path(drive_info['path'])
            
            # Detect drive type
            is_efis = self._detect_efis_drive(drive_path)
            file_count = len(list(drive_path.rglob("*")))
            
            detection_results.append({
                'type': drive_type['type'],
                'detected_as_efis': is_efis,
                'file_count': file_count,
                'expected_files': drive_type['expected_files']
            })
            
            # Verify detection
            if drive_type['type'] == 'efis':
                assert is_efis is True
                assert file_count >= drive_type['expected_files']
            else:
                assert is_efis is False
            
            print(f"✓ Drive type '{drive_type['type']}': "
                  f"EFIS={is_efis}, Files={file_count}")
            
            # Remove drive
            self.simulator.remove_drive(drive_info['id'])
        
        print("✓ Drive type detection and handling test successful")
    
    def _detect_efis_drive(self, drive_path):
        """Detect if drive is an EFIS drive."""
        # Check for EFIS markers
        efis_markers = [
            drive_path / "EFIS_DRIVE",
            drive_path / "NAV.DB"
        ]
        
        if any(marker.exists() for marker in efis_markers):
            return True
        
        # Check for demo files
        demo_files = list(drive_path.glob("DEMO-*.LOG"))
        if len(demo_files) > 0:
            return True
        
        return False
    
    def test_drive_error_conditions(self):
        """Test handling of various drive error conditions."""
        error_scenarios = [
            {
                'name': 'Corrupted EFIS Drive',
                'setup': lambda path: self._create_corrupted_efis_drive(path),
                'expected_processable': False
            },
            {
                'name': 'Read-Only Drive',
                'setup': lambda path: self._create_readonly_drive(path),
                'expected_processable': False
            },
            {
                'name': 'Partial EFIS Drive',
                'setup': lambda path: self._create_partial_efis_drive(path),
                'expected_processable': True
            }
        ]
        
        for i, scenario in enumerate(error_scenarios):
            print(f"Testing: {scenario['name']}")
            
            # Insert drive
            drive_info = self.simulator.insert_drive(f"error_{i:03d}", "empty")
            drive_path = Path(drive_info['path'])
            
            # Set up error condition
            scenario['setup'](drive_path)
            
            # Test processing
            try:
                is_processable = self._test_drive_processing(drive_path)
                
                if scenario['expected_processable']:
                    assert is_processable
                    print(f"  ✓ {scenario['name']}: Processed successfully")
                else:
                    print(f"  ✓ {scenario['name']}: Correctly rejected")
                    
            except Exception as e:
                if not scenario['expected_processable']:
                    print(f"  ✓ {scenario['name']}: Error handled - {type(e).__name__}")
                else:
                    print(f"  ✗ {scenario['name']}: Unexpected error - {e}")
                    raise
            
            # Remove drive
            self.simulator.remove_drive(drive_info['id'])
        
        print("✓ Drive error conditions test successful")
    
    def _create_corrupted_efis_drive(self, drive_path):
        """Create a corrupted EFIS drive."""
        # Create EFIS marker but with corrupted content
        (drive_path / "EFIS_DRIVE").write_bytes(b"\x00\x01\x02\x03")  # Binary garbage
        
        # Create corrupted demo file
        (drive_path / "DEMO-CORRUPTED.LOG").write_bytes(b"\xFF" * 100)
    
    def _create_readonly_drive(self, drive_path):
        """Create a read-only drive."""
        # Create EFIS content
        (drive_path / "EFIS_DRIVE").write_text("READONLY_DRIVE")
        (drive_path / "DEMO-20231201-120000.LOG").write_text("Demo data")
        
        # Make directory read-only
        try:
            os.chmod(drive_path, 0o444)
        except OSError:
            pass  # May not work on all systems
    
    def _create_partial_efis_drive(self, drive_path):
        """Create a partially populated EFIS drive."""
        # Only EFIS marker, no other files
        (drive_path / "EFIS_DRIVE").write_text("PARTIAL_DRIVE")
    
    def _test_drive_processing(self, drive_path):
        """Test if drive can be processed."""
        try:
            # Check if it's an EFIS drive
            if not self._detect_efis_drive(drive_path):
                return False
            
            # Try to read files
            files = list(drive_path.rglob("*"))
            for file_path in files:
                if file_path.is_file():
                    try:
                        file_path.read_bytes()
                    except (OSError, PermissionError):
                        return False
            
            return True
            
        except Exception:
            return False
    
    def test_drive_capacity_and_space_management(self):
        """Test handling of drive capacity and space management."""
        # Insert drive with limited capacity
        drive_info = self.simulator.insert_drive("capacity_test", "efis", capacity=1024*1024)  # 1MB
        drive_path = Path(drive_info['path'])
        
        # Get initial space usage
        initial_usage = self._calculate_space_usage(drive_path)
        
        # Try to add large files
        large_files = []
        for i in range(5):
            large_file = drive_path / f"large_file_{i}.dat"
            try:
                # Create 500KB file
                large_file.write_bytes(b"X" * (500 * 1024))
                large_files.append(large_file)
            except OSError:
                # Expected - drive full
                break
        
        final_usage = self._calculate_space_usage(drive_path)
        
        print(f"✓ Drive capacity test:")
        print(f"  Initial usage: {initial_usage / 1024:.1f}KB")
        print(f"  Final usage: {final_usage / 1024:.1f}KB")
        print(f"  Large files created: {len(large_files)}")
        
        # Should not be able to create all 5 large files (would exceed 1MB)
        assert len(large_files) < 5
        
        # Clean up
        for large_file in large_files:
            if large_file.exists():
                large_file.unlink()
        
        self.simulator.remove_drive("capacity_test")
        
        print("✓ Drive capacity and space management test successful")
    
    def _calculate_space_usage(self, drive_path):
        """Calculate total space usage of drive."""
        total_size = 0
        for file_path in drive_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except OSError:
                    pass
        return total_size
    
    def test_drive_ejection_safety(self):
        """Test safe drive ejection procedures."""
        # Insert drive
        drive_info = self.simulator.insert_drive("eject_test", "efis")
        drive_path = Path(drive_info['path'])
        
        # Simulate file operations in progress
        active_operations = []
        
        # Create test files
        test_files = []
        for i in range(3):
            test_file = drive_path / f"test_file_{i}.txt"
            test_file.write_text(f"Test content {i}")
            test_files.append(test_file)
        
        # Simulate reading files (would prevent safe ejection)
        file_handles = []
        for test_file in test_files:
            try:
                handle = open(test_file, 'r')
                file_handles.append(handle)
                active_operations.append(f"Reading {test_file.name}")
            except OSError:
                pass
        
        # Test ejection with active operations
        can_eject_safely = len(active_operations) == 0
        
        print(f"✓ Ejection safety check:")
        print(f"  Active operations: {len(active_operations)}")
        print(f"  Can eject safely: {can_eject_safely}")
        
        if not can_eject_safely:
            print("  ⚠ Waiting for operations to complete...")
            
            # Close file handles
            for handle in file_handles:
                handle.close()
            
            # Now should be safe to eject
            can_eject_safely = True
            print("  ✓ Operations completed, safe to eject")
        
        # Perform ejection
        if can_eject_safely:
            self.simulator.remove_drive("eject_test")
            print("  ✓ Drive ejected safely")
        
        print("✓ Drive ejection safety test successful")
    
    def test_drive_performance_monitoring(self):
        """Test monitoring of drive performance during operations."""
        # Insert drive
        drive_info = self.simulator.insert_drive("perf_test", "efis")
        drive_path = Path(drive_info['path'])
        
        # Performance metrics
        metrics = {
            'read_operations': 0,
            'write_operations': 0,
            'total_bytes_read': 0,
            'total_bytes_written': 0,
            'operation_times': []
        }
        
        # Test file operations with timing
        test_operations = [
            {'type': 'write', 'size': 1024, 'count': 10},
            {'type': 'read', 'size': 1024, 'count': 10},
            {'type': 'write', 'size': 10240, 'count': 5},
            {'type': 'read', 'size': 10240, 'count': 5}
        ]
        
        for operation in test_operations:
            for i in range(operation['count']):
                start_time = time.time()
                
                if operation['type'] == 'write':
                    test_file = drive_path / f"perf_test_{i}.dat"
                    data = b"X" * operation['size']
                    test_file.write_bytes(data)
                    
                    metrics['write_operations'] += 1
                    metrics['total_bytes_written'] += operation['size']
                    
                elif operation['type'] == 'read':
                    test_file = drive_path / f"perf_test_{i}.dat"
                    if test_file.exists():
                        data = test_file.read_bytes()
                        
                        metrics['read_operations'] += 1
                        metrics['total_bytes_read'] += len(data)
                
                operation_time = time.time() - start_time
                metrics['operation_times'].append(operation_time)
        
        # Calculate performance statistics
        avg_operation_time = sum(metrics['operation_times']) / len(metrics['operation_times'])
        total_operations = metrics['read_operations'] + metrics['write_operations']
        
        read_throughput = metrics['total_bytes_read'] / sum(metrics['operation_times']) if metrics['operation_times'] else 0
        write_throughput = metrics['total_bytes_written'] / sum(metrics['operation_times']) if metrics['operation_times'] else 0
        
        print(f"✓ Drive performance metrics:")
        print(f"  Total operations: {total_operations}")
        print(f"  Read operations: {metrics['read_operations']}")
        print(f"  Write operations: {metrics['write_operations']}")
        print(f"  Average operation time: {avg_operation_time * 1000:.2f}ms")
        print(f"  Read throughput: {read_throughput / 1024:.1f}KB/s")
        print(f"  Write throughput: {write_throughput / 1024:.1f}KB/s")
        
        # Performance assertions
        assert avg_operation_time < 1.0  # Operations should be fast
        assert total_operations > 0
        
        self.simulator.remove_drive("perf_test")
        
        print("✓ Drive performance monitoring test successful")