"""
Unit tests for USB drive processor core functionality.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from macos.src.efis_macos.usb_drive_processor import (
    USBDriveProcessor, DriveDetector, FileProcessor, 
    ProcessingError, DriveNotFoundError
)
from macos.src.efis_macos.efis_file_processor import EFISFileProcessor
from shared.models.data_models import EFISDrive, DriveStatus


class TestDriveDetector:
    """Test cases for DriveDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DriveDetector()

    @patch('macos.src.efis_macos.usb_drive_processor.psutil.disk_partitions')
    def test_get_mounted_drives(self, mock_partitions):
        """Test getting mounted drives."""
        mock_partitions.return_value = [
            Mock(device='/dev/disk2s1', mountpoint='/Volumes/USB1', fstype='fat32'),
            Mock(device='/dev/disk3s1', mountpoint='/Volumes/USB2', fstype='exfat'),
            Mock(device='/dev/disk1s1', mountpoint='/', fstype='apfs')  # System drive
        ]
        
        drives = self.detector.get_mounted_drives()
        
        # Should exclude system drives
        assert len(drives) == 2
        assert '/Volumes/USB1' in [d.mount_path for d in drives]
        assert '/Volumes/USB2' in [d.mount_path for d in drives]

    def test_is_efis_drive_with_markers(self):
        """Test EFIS drive detection using file markers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create EFIS marker files
            (drive_path / "EFIS_DRIVE").touch()
            (drive_path / "NAV.DB").touch()
            
            result = self.detector.is_efis_drive(str(drive_path))
            assert result is True

    def test_is_efis_drive_with_demo_files(self):
        """Test EFIS drive detection using demo files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create demo files
            (drive_path / "DEMO-20231201-120000.LOG").touch()
            (drive_path / "DEMO-20231201-130000+1.LOG").touch()
            
            result = self.detector.is_efis_drive(str(drive_path))
            assert result is True

    def test_is_efis_drive_false(self):
        """Test EFIS drive detection returns false for regular drives."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create regular files
            (drive_path / "document.txt").touch()
            (drive_path / "photo.jpg").touch()
            
            result = self.detector.is_efis_drive(str(drive_path))
            assert result is False

    def test_get_drive_capacity(self):
        """Test getting drive capacity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            capacity = self.detector.get_drive_capacity(temp_dir)
            assert capacity > 0

    def test_get_drive_identifier(self):
        """Test getting drive identifier."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create identifier file
            identifier_file = drive_path / "EFIS_DRIVE"
            identifier_file.write_text("EFIS_001")
            
            identifier = self.detector.get_drive_identifier(str(drive_path))
            assert identifier == "EFIS_001"

    def test_get_drive_identifier_default(self):
        """Test getting default drive identifier."""
        with tempfile.TemporaryDirectory() as temp_dir:
            identifier = self.detector.get_drive_identifier(temp_dir)
            assert identifier.startswith("EFIS_")


class TestFileProcessor:
    """Test cases for FileProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'macos': {
                'demoPath': '/tmp/test/demo',
                'logbookPath': '/tmp/test/logbook'
            }
        }
        self.processor = FileProcessor(self.config)

    def test_find_demo_files(self):
        """Test finding demo files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create demo files
            demo_files = [
                "DEMO-20231201-120000.LOG",
                "DEMO-20231201-130000+1.LOG",
                "DEMO-20231202-140000.LOG"
            ]
            
            for filename in demo_files:
                (drive_path / filename).touch()
            
            # Create non-demo files
            (drive_path / "CONFIG.xml").touch()
            (drive_path / "README.txt").touch()
            
            found_files = self.processor.find_demo_files(str(drive_path))
            
            assert len(found_files) == 3
            for demo_file in demo_files:
                assert any(demo_file in str(f) for f in found_files)

    def test_find_snap_files(self):
        """Test finding snapshot files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create snap files
            snap_files = [
                "SNAP-001.png",
                "SNAP-002.PNG",
                "screenshot.png"
            ]
            
            for filename in snap_files:
                (drive_path / filename).touch()
            
            found_files = self.processor.find_snap_files(str(drive_path))
            
            assert len(found_files) >= 2  # At least SNAP files
            assert any("SNAP-001.png" in str(f) for f in found_files)

    def test_find_logbook_files(self):
        """Test finding logbook files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_path = Path(temp_dir)
            
            # Create logbook files
            logbook_files = [
                "logbook.csv",
                "LOGBOOK.CSV",
                "flight_log.csv"
            ]
            
            for filename in logbook_files:
                (drive_path / filename).touch()
            
            found_files = self.processor.find_logbook_files(str(drive_path))
            
            assert len(found_files) >= 2  # At least logbook files
            assert any("logbook.csv" in str(f) for f in found_files)

    def test_move_files_to_archive(self):
        """Test moving files to archive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files
            test_files = [
                source_dir / "file1.txt",
                source_dir / "file2.log"
            ]
            
            for file_path in test_files:
                file_path.write_text("Test content")
            
            # Move files
            moved_files = self.processor.move_files_to_archive(
                [str(f) for f in test_files], str(dest_dir)
            )
            
            assert len(moved_files) == 2
            
            # Verify files were moved
            for original_file in test_files:
                assert not original_file.exists()
            
            for moved_file in moved_files:
                assert Path(moved_file).exists()

    def test_rename_logbook_file(self):
        """Test renaming logbook file with date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "logbook.csv"
            source_file.write_text("Date,Flight,Duration\n2023-12-01,Flight 1,1.5")
            
            renamed_file = self.processor.rename_logbook_file(str(source_file))
            
            assert "Logbook" in renamed_file
            assert "2023-12-01" in renamed_file or datetime.now().strftime("%Y-%m-%d") in renamed_file
            assert Path(renamed_file).exists()

    def test_validate_file_integrity(self):
        """Test file integrity validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            content = "Test content for integrity check"
            test_file.write_text(content)
            
            # Valid file
            result = self.processor.validate_file_integrity(str(test_file))
            assert result is True
            
            # Empty file
            empty_file = Path(temp_dir) / "empty.txt"
            empty_file.touch()
            result = self.processor.validate_file_integrity(str(empty_file))
            assert result is False

    def test_get_file_creation_date(self):
        """Test getting file creation date."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")
            
            creation_date = self.processor.get_file_creation_date(str(test_file))
            
            assert isinstance(creation_date, datetime)
            # Should be recent (within last minute)
            assert (datetime.now() - creation_date).total_seconds() < 60


class TestUSBDriveProcessor:
    """Test cases for USBDriveProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'macos': {
                'archivePath': '/tmp/test/archive',
                'demoPath': '/tmp/test/demo',
                'logbookPath': '/tmp/test/logbook'
            }
        }
        self.processor = USBDriveProcessor(self.config)

    @patch('macos.src.efis_macos.usb_drive_processor.psutil.disk_partitions')
    def test_detect_efis_drives(self, mock_partitions):
        """Test detecting EFIS drives."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock EFIS drive
            efis_dir = Path(temp_dir) / "efis_drive"
            efis_dir.mkdir()
            (efis_dir / "EFIS_DRIVE").touch()
            (efis_dir / "NAV.DB").touch()
            
            mock_partitions.return_value = [
                Mock(device='/dev/disk2s1', mountpoint=str(efis_dir), fstype='fat32')
            ]
            
            drives = self.processor.detect_efis_drives()
            
            assert len(drives) == 1
            assert drives[0].mount_path == str(efis_dir)
            assert drives[0].status == DriveStatus.MOUNTED

    def test_process_efis_drive(self):
        """Test processing EFIS drive files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directory structure
            drive_dir = Path(temp_dir) / "drive"
            demo_dir = Path(temp_dir) / "demo"
            logbook_dir = Path(temp_dir) / "logbook"
            
            drive_dir.mkdir()
            demo_dir.mkdir()
            logbook_dir.mkdir()
            
            # Update config with temp directories
            self.processor.config['macos']['demoPath'] = str(demo_dir)
            self.processor.config['macos']['logbookPath'] = str(logbook_dir)
            
            # Create test files on drive
            (drive_dir / "DEMO-20231201-120000.LOG").write_text("Demo data")
            (drive_dir / "SNAP-001.png").write_bytes(b"PNG data")
            (drive_dir / "logbook.csv").write_text("Date,Flight\n2023-12-01,Test")
            
            # Create EFIS drive object
            efis_drive = EFISDrive(
                mount_path=str(drive_dir),
                identifier="TEST_DRIVE",
                capacity=32000000000,
                status=DriveStatus.MOUNTED
            )
            
            # Process the drive
            result = self.processor.process_efis_drive(efis_drive)
            
            assert result['success'] is True
            assert result['files_processed'] >= 3
            assert len(result['demo_files']) >= 1
            assert len(result['snap_files']) >= 1
            assert len(result['logbook_files']) >= 1

    def test_process_efis_drive_no_files(self):
        """Test processing EFIS drive with no files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_dir = Path(temp_dir)
            
            efis_drive = EFISDrive(
                mount_path=str(drive_dir),
                identifier="EMPTY_DRIVE",
                capacity=32000000000,
                status=DriveStatus.MOUNTED
            )
            
            result = self.processor.process_efis_drive(efis_drive)
            
            assert result['success'] is True
            assert result['files_processed'] == 0
            assert len(result['demo_files']) == 0

    def test_process_efis_drive_invalid_path(self):
        """Test processing EFIS drive with invalid path."""
        efis_drive = EFISDrive(
            mount_path="/nonexistent/path",
            identifier="INVALID_DRIVE",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        
        with pytest.raises(ProcessingError) as exc_info:
            self.processor.process_efis_drive(efis_drive)
        
        assert "Drive path does not exist" in str(exc_info.value)

    @patch('macos.src.efis_macos.usb_drive_processor.subprocess.run')
    def test_safely_eject_drive(self, mock_run):
        """Test safely ejecting drive."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = self.processor.safely_eject_drive("/dev/disk2s1")
        
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "diskutil" in args
        assert "eject" in args

    @patch('macos.src.efis_macos.usb_drive_processor.subprocess.run')
    def test_safely_eject_drive_failure(self, mock_run):
        """Test drive ejection failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Device busy"
        )
        
        result = self.processor.safely_eject_drive("/dev/disk2s1")
        
        assert result is False

    def test_get_processing_statistics(self):
        """Test getting processing statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            drive_dir = Path(temp_dir)
            
            # Create test files
            (drive_dir / "DEMO-20231201-120000.LOG").write_text("Demo data" * 100)
            (drive_dir / "SNAP-001.png").write_bytes(b"PNG data" * 50)
            (drive_dir / "logbook.csv").write_text("CSV data" * 25)
            
            stats = self.processor.get_processing_statistics(str(drive_dir))
            
            assert stats['total_files'] == 3
            assert stats['total_size'] > 0
            assert 'demo_files' in stats
            assert 'snap_files' in stats
            assert 'logbook_files' in stats

    def test_validate_drive_access(self):
        """Test validating drive access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid directory
            result = self.processor.validate_drive_access(temp_dir)
            assert result is True
            
            # Invalid directory
            result = self.processor.validate_drive_access("/nonexistent/path")
            assert result is False