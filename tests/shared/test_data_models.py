"""
Unit tests for data models.
"""

import pytest
from datetime import datetime
from shared.models.data_models import (
    FileMetadata, SyncResult, EFISDrive,
    OperationStatus, DriveStatus
)


class TestFileMetadata:
    """Test cases for FileMetadata."""

    def test_create_file_metadata(self):
        """Test creating FileMetadata instance."""
        now = datetime.now()
        metadata = FileMetadata(
            path="/test/file.txt",
            size=1024,
            hash="abc123",
            last_modified=now
        )
        
        assert metadata.path == "/test/file.txt"
        assert metadata.size == 1024
        assert metadata.hash == "abc123"
        assert metadata.last_modified == now

    def test_file_metadata_equality(self):
        """Test FileMetadata equality comparison."""
        now = datetime.now()
        metadata1 = FileMetadata(
            path="/test/file.txt",
            size=1024,
            hash="abc123",
            last_modified=now
        )
        metadata2 = FileMetadata(
            path="/test/file.txt",
            size=1024,
            hash="abc123",
            last_modified=now
        )
        
        assert metadata1 == metadata2

    def test_file_metadata_inequality(self):
        """Test FileMetadata inequality comparison."""
        now = datetime.now()
        metadata1 = FileMetadata(
            path="/test/file1.txt",
            size=1024,
            hash="abc123",
            last_modified=now
        )
        metadata2 = FileMetadata(
            path="/test/file2.txt",
            size=1024,
            hash="abc123",
            last_modified=now
        )
        
        assert metadata1 != metadata2


class TestSyncResult:
    """Test cases for SyncResult."""

    def test_create_sync_result_success(self):
        """Test creating successful SyncResult."""
        result = SyncResult(
            status=OperationStatus.SUCCESS,
            files_transferred=5,
            bytes_transferred=5120,
            duration=30.5
        )
        
        assert result.status == OperationStatus.SUCCESS
        assert result.files_transferred == 5
        assert result.bytes_transferred == 5120
        assert result.duration == 30.5
        assert len(result.errors) == 0

    def test_create_sync_result_with_errors(self):
        """Test creating SyncResult with errors."""
        errors = ["File not found", "Permission denied"]
        result = SyncResult(
            status=OperationStatus.FAILED,
            files_transferred=2,
            bytes_transferred=1024,
            errors=errors
        )
        
        assert result.status == OperationStatus.FAILED
        assert result.files_transferred == 2
        assert len(result.errors) == 2
        assert "File not found" in result.errors

    def test_sync_result_add_error(self):
        """Test adding error to SyncResult."""
        result = SyncResult(
            status=OperationStatus.IN_PROGRESS,
            files_transferred=0,
            bytes_transferred=0
        )
        
        result.add_error("Network timeout")
        assert len(result.errors) == 1
        assert "Network timeout" in result.errors


class TestEFISDrive:
    """Test cases for EFISDrive."""

    def test_create_efis_drive(self):
        """Test creating EFISDrive instance."""
        drive = EFISDrive(
            mount_path="/Volumes/EFIS",
            identifier="EFIS_DRIVE_001",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        
        assert drive.mount_path == "/Volumes/EFIS"
        assert drive.identifier == "EFIS_DRIVE_001"
        assert drive.capacity == 32000000000
        assert drive.status == DriveStatus.MOUNTED
        assert len(drive.demo_files) == 0
        assert len(drive.snap_files) == 0
        assert len(drive.logbook_files) == 0

    def test_efis_drive_add_files(self):
        """Test adding files to EFISDrive."""
        drive = EFISDrive(
            mount_path="/Volumes/EFIS",
            identifier="EFIS_DRIVE_001",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        
        drive.demo_files.append("DEMO-20231201-120000.LOG")
        drive.snap_files.append("SNAP-001.png")
        drive.logbook_files.append("logbook.csv")
        
        assert len(drive.demo_files) == 1
        assert len(drive.snap_files) == 1
        assert len(drive.logbook_files) == 1
        assert "DEMO-20231201-120000.LOG" in drive.demo_files

    def test_efis_drive_is_valid(self):
        """Test EFISDrive validation."""
        # Valid drive
        valid_drive = EFISDrive(
            mount_path="/Volumes/EFIS",
            identifier="EFIS_DRIVE_001",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        assert valid_drive.is_valid()
        
        # Invalid drive (no mount path)
        invalid_drive = EFISDrive(
            mount_path="",
            identifier="EFIS_DRIVE_001",
            capacity=32000000000,
            status=DriveStatus.MOUNTED
        )
        assert not invalid_drive.is_valid()


class TestOperationStatus:
    """Test cases for OperationStatus enum."""

    def test_operation_status_values(self):
        """Test OperationStatus enum values."""
        assert OperationStatus.SUCCESS.value == "success"
        assert OperationStatus.FAILED.value == "failed"
        assert OperationStatus.IN_PROGRESS.value == "in_progress"
        assert OperationStatus.CANCELLED.value == "cancelled"

    def test_operation_status_comparison(self):
        """Test OperationStatus comparison."""
        assert OperationStatus.SUCCESS == OperationStatus.SUCCESS
        assert OperationStatus.SUCCESS != OperationStatus.FAILED


class TestDriveStatus:
    """Test cases for DriveStatus enum."""

    def test_drive_status_values(self):
        """Test DriveStatus enum values."""
        assert DriveStatus.MOUNTED.value == "mounted"
        assert DriveStatus.UNMOUNTED.value == "unmounted"
        assert DriveStatus.ERROR.value == "error"
        assert DriveStatus.UNKNOWN.value == "unknown"

    def test_drive_status_comparison(self):
        """Test DriveStatus comparison."""
        assert DriveStatus.MOUNTED == DriveStatus.MOUNTED
        assert DriveStatus.MOUNTED != DriveStatus.UNMOUNTED