"""
Unit tests for file synchronization engine.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from windows.src.sync_engine import (
    SyncEngine, FileComparator, TransferManager, 
    SyncError, FileTransferError
)
from shared.models.data_models import FileMetadata, SyncResult, OperationStatus


class TestFileComparator:
    """Test cases for FileComparator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.comparator = FileComparator()

    def test_compare_files_identical(self):
        """Test comparing identical files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create identical files
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"
            content = "Test content"
            
            file1.write_text(content)
            file2.write_text(content)
            
            result = self.comparator.compare_files(str(file1), str(file2))
            assert result is True

    def test_compare_files_different(self):
        """Test comparing different files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create different files
            file1 = Path(temp_dir) / "file1.txt"
            file2 = Path(temp_dir) / "file2.txt"
            
            file1.write_text("Content 1")
            file2.write_text("Content 2")
            
            result = self.comparator.compare_files(str(file1), str(file2))
            assert result is False

    def test_compare_files_missing_source(self):
        """Test comparing with missing source file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "nonexistent.txt"
            file2 = Path(temp_dir) / "file2.txt"
            file2.write_text("Content")
            
            result = self.comparator.compare_files(str(file1), str(file2))
            assert result is False

    def test_get_file_metadata(self):
        """Test getting file metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            content = "Test content for metadata"
            test_file.write_text(content)
            
            metadata = self.comparator.get_file_metadata(str(test_file))
            
            assert metadata.path == str(test_file)
            assert metadata.size == len(content.encode())
            assert metadata.hash is not None
            assert isinstance(metadata.last_modified, datetime)

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            content = "Test content for hash"
            test_file.write_text(content)
            
            hash1 = self.comparator.calculate_file_hash(str(test_file))
            hash2 = self.comparator.calculate_file_hash(str(test_file))
            
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 hex length

    def test_get_changed_files(self):
        """Test getting changed files between directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create files in source
            (source_dir / "file1.txt").write_text("Content 1")
            (source_dir / "file2.txt").write_text("Content 2")
            (source_dir / "new_file.txt").write_text("New content")
            
            # Create some files in destination (older versions)
            (dest_dir / "file1.txt").write_text("Content 1")  # Same
            (dest_dir / "file2.txt").write_text("Old content 2")  # Different
            # new_file.txt doesn't exist in dest
            
            changed_files = self.comparator.get_changed_files(str(source_dir), str(dest_dir))
            
            # Should find file2.txt (changed) and new_file.txt (new)
            changed_paths = [f.path for f in changed_files]
            assert len(changed_files) >= 2
            assert any("file2.txt" in path for path in changed_paths)
            assert any("new_file.txt" in path for path in changed_paths)


class TestTransferManager:
    """Test cases for TransferManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transfer_manager = TransferManager()

    def test_copy_file_success(self):
        """Test successful file copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            dest_file = Path(temp_dir) / "dest.txt"
            content = "Test content for copying"
            
            source_file.write_text(content)
            
            result = self.transfer_manager.copy_file(str(source_file), str(dest_file))
            
            assert result is True
            assert dest_file.exists()
            assert dest_file.read_text() == content

    def test_copy_file_source_not_found(self):
        """Test copying non-existent source file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "nonexistent.txt"
            dest_file = Path(temp_dir) / "dest.txt"
            
            with pytest.raises(FileTransferError) as exc_info:
                self.transfer_manager.copy_file(str(source_file), str(dest_file))
            
            assert "Source file not found" in str(exc_info.value)

    def test_copy_file_with_progress_callback(self):
        """Test file copying with progress callback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            dest_file = Path(temp_dir) / "dest.txt"
            content = "Test content" * 1000  # Larger content
            
            source_file.write_text(content)
            
            progress_calls = []
            def progress_callback(bytes_copied, total_bytes):
                progress_calls.append((bytes_copied, total_bytes))
            
            result = self.transfer_manager.copy_file(
                str(source_file), str(dest_file), progress_callback
            )
            
            assert result is True
            assert len(progress_calls) > 0
            assert progress_calls[-1][0] == progress_calls[-1][1]  # Final call should be complete

    def test_copy_files_batch(self):
        """Test batch file copying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create source files
            files_to_copy = []
            for i in range(3):
                source_file = source_dir / f"file{i}.txt"
                dest_file = dest_dir / f"file{i}.txt"
                source_file.write_text(f"Content {i}")
                files_to_copy.append((str(source_file), str(dest_file)))
            
            results = self.transfer_manager.copy_files_batch(files_to_copy)
            
            assert len(results) == 3
            assert all(result['success'] for result in results)
            
            # Verify files were copied
            for i in range(3):
                dest_file = dest_dir / f"file{i}.txt"
                assert dest_file.exists()
                assert dest_file.read_text() == f"Content {i}"

    def test_verify_transfer_integrity(self):
        """Test transfer integrity verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            dest_file = Path(temp_dir) / "dest.txt"
            content = "Test content for verification"
            
            source_file.write_text(content)
            dest_file.write_text(content)
            
            result = self.transfer_manager.verify_transfer_integrity(
                str(source_file), str(dest_file)
            )
            
            assert result is True

    def test_verify_transfer_integrity_mismatch(self):
        """Test transfer integrity verification with mismatch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_file = Path(temp_dir) / "source.txt"
            dest_file = Path(temp_dir) / "dest.txt"
            
            source_file.write_text("Original content")
            dest_file.write_text("Different content")
            
            result = self.transfer_manager.verify_transfer_integrity(
                str(source_file), str(dest_file)
            )
            
            assert result is False


class TestSyncEngine:
    """Test cases for SyncEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'windows': {
                'virtualDriveFile': 'C:\\test\\virtual.vhd',
                'driveLetter': 'E:',
                'syncInterval': 1800,
                'retryAttempts': 3
            },
            'macos': {
                'archivePath': '/Users/test/archive'
            }
        }
        self.sync_engine = SyncEngine(self.config)

    def test_sync_directories_success(self):
        """Test successful directory synchronization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files
            (source_dir / "file1.txt").write_text("Content 1")
            (source_dir / "file2.txt").write_text("Content 2")
            
            result = self.sync_engine.sync_directories(str(source_dir), str(dest_dir))
            
            assert result.status == OperationStatus.SUCCESS
            assert result.files_transferred >= 2
            assert result.bytes_transferred > 0
            assert len(result.errors) == 0

    def test_sync_directories_with_existing_files(self):
        """Test synchronization with existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create files in both directories
            (source_dir / "same_file.txt").write_text("Same content")
            (source_dir / "changed_file.txt").write_text("New content")
            (source_dir / "new_file.txt").write_text("New file content")
            
            (dest_dir / "same_file.txt").write_text("Same content")
            (dest_dir / "changed_file.txt").write_text("Old content")
            
            result = self.sync_engine.sync_directories(str(source_dir), str(dest_dir))
            
            assert result.status == OperationStatus.SUCCESS
            # Should transfer changed_file.txt and new_file.txt
            assert result.files_transferred >= 2

    @patch('windows.src.sync_engine.requests.get')
    def test_check_network_connectivity_success(self, mock_get):
        """Test successful network connectivity check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.sync_engine.check_network_connectivity("192.168.1.100")
        
        assert result is True

    @patch('windows.src.sync_engine.requests.get')
    def test_check_network_connectivity_failure(self, mock_get):
        """Test network connectivity check failure."""
        mock_get.side_effect = Exception("Connection timeout")
        
        result = self.sync_engine.check_network_connectivity("192.168.1.100")
        
        assert result is False

    def test_calculate_sync_statistics(self):
        """Test sync statistics calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            source_dir.mkdir()
            
            # Create test files
            (source_dir / "small.txt").write_text("Small")
            (source_dir / "large.txt").write_text("Large content" * 100)
            
            stats = self.sync_engine.calculate_sync_statistics(str(source_dir))
            
            assert stats['total_files'] == 2
            assert stats['total_size'] > 0
            assert 'file_types' in stats

    def test_sync_with_retry_success(self):
        """Test sync with retry - success on first attempt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            dest_dir = Path(temp_dir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            (source_dir / "test.txt").write_text("Test content")
            
            result = self.sync_engine.sync_with_retry(str(source_dir), str(dest_dir), max_retries=3)
            
            assert result.status == OperationStatus.SUCCESS
            assert result.files_transferred >= 1