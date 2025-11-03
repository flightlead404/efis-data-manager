"""
Unit tests for ImDisk wrapper functionality.
"""

import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path

from windows.src.imdisk_wrapper import ImDiskWrapper, ImDiskError


class TestImDiskWrapper:
    """Test cases for ImDiskWrapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.wrapper = ImDiskWrapper()

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_mount_vhd_success(self, mock_run):
        """Test successful VHD mounting."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = self.wrapper.mount_vhd("C:\\test\\virtual.vhd", "E:")
        
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "MountImg.exe" in args[0]
        assert "C:\\test\\virtual.vhd" in args
        assert "/m" in args
        assert "E:" in args

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_mount_vhd_failure(self, mock_run):
        """Test VHD mounting failure."""
        mock_run.return_value = Mock(
            returncode=1, 
            stdout="", 
            stderr="Error: File not found"
        )
        
        with pytest.raises(ImDiskError) as exc_info:
            self.wrapper.mount_vhd("C:\\nonexistent\\virtual.vhd", "E:")
        
        assert "Failed to mount VHD" in str(exc_info.value)
        assert "File not found" in str(exc_info.value)

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_unmount_drive_success(self, mock_run):
        """Test successful drive unmounting."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = self.wrapper.unmount_drive("E:")
        
        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "MountImg.exe" in args[0]
        assert "/u" in args
        assert "E:" in args

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_unmount_drive_failure(self, mock_run):
        """Test drive unmounting failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Drive not found"
        )
        
        with pytest.raises(ImDiskError) as exc_info:
            self.wrapper.unmount_drive("E:")
        
        assert "Failed to unmount drive" in str(exc_info.value)

    @patch('windows.src.imdisk_wrapper.os.path.exists')
    def test_is_drive_mounted_true(self, mock_exists):
        """Test drive mount status check - mounted."""
        mock_exists.return_value = True
        
        result = self.wrapper.is_drive_mounted("E:")
        
        assert result is True
        mock_exists.assert_called_once_with("E:\\")

    @patch('windows.src.imdisk_wrapper.os.path.exists')
    def test_is_drive_mounted_false(self, mock_exists):
        """Test drive mount status check - not mounted."""
        mock_exists.return_value = False
        
        result = self.wrapper.is_drive_mounted("E:")
        
        assert result is False
        mock_exists.assert_called_once_with("E:\\")

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_get_drive_info_success(self, mock_run):
        """Test getting drive information."""
        mock_output = "E: VHD 32GB NTFS"
        mock_run.return_value = Mock(
            returncode=0,
            stdout=mock_output,
            stderr=""
        )
        
        info = self.wrapper.get_drive_info("E:")
        
        assert info is not None
        assert "VHD" in info
        mock_run.assert_called_once()

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_get_drive_info_failure(self, mock_run):
        """Test getting drive information failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Drive not found"
        )
        
        info = self.wrapper.get_drive_info("E:")
        
        assert info is None

    def test_validate_drive_letter_valid(self):
        """Test drive letter validation - valid cases."""
        valid_letters = ["C:", "E:", "Z:", "c:", "e:", "z:"]
        
        for letter in valid_letters:
            result = self.wrapper._validate_drive_letter(letter)
            assert result is True

    def test_validate_drive_letter_invalid(self):
        """Test drive letter validation - invalid cases."""
        invalid_letters = ["", "C", "E", "CC:", "1:", "E:\\", "/dev/sda1"]
        
        for letter in invalid_letters:
            result = self.wrapper._validate_drive_letter(letter)
            assert result is False

    def test_validate_vhd_path_valid(self):
        """Test VHD path validation - valid cases."""
        valid_paths = [
            "C:\\test\\virtual.vhd",
            "D:\\data\\backup.vhd",
            "E:\\files\\image.VHD"
        ]
        
        for path in valid_paths:
            result = self.wrapper._validate_vhd_path(path)
            assert result is True

    def test_validate_vhd_path_invalid(self):
        """Test VHD path validation - invalid cases."""
        invalid_paths = [
            "",
            "C:\\test\\file.txt",
            "invalid_path",
            "/unix/path/file.vhd",
            "C:\\test\\file.VHD.backup"
        ]
        
        for path in invalid_paths:
            result = self.wrapper._validate_vhd_path(path)
            assert result is False

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    def test_mount_with_retry_success_first_attempt(self, mock_run):
        """Test mount with retry - success on first attempt."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        result = self.wrapper.mount_with_retry("C:\\test\\virtual.vhd", "E:", max_retries=3)
        
        assert result is True
        assert mock_run.call_count == 1

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    @patch('windows.src.imdisk_wrapper.time.sleep')
    def test_mount_with_retry_success_after_retry(self, mock_sleep, mock_run):
        """Test mount with retry - success after retry."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="Temporary error"),
            Mock(returncode=0, stdout="", stderr="")
        ]
        
        result = self.wrapper.mount_with_retry("C:\\test\\virtual.vhd", "E:", max_retries=3)
        
        assert result is True
        assert mock_run.call_count == 2
        mock_sleep.assert_called_once()

    @patch('windows.src.imdisk_wrapper.subprocess.run')
    @patch('windows.src.imdisk_wrapper.time.sleep')
    def test_mount_with_retry_failure_after_max_retries(self, mock_sleep, mock_run):
        """Test mount with retry - failure after max retries."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Persistent error"
        )
        
        with pytest.raises(ImDiskError) as exc_info:
            self.wrapper.mount_with_retry("C:\\test\\virtual.vhd", "E:", max_retries=2)
        
        assert "Failed to mount VHD after 2 retries" in str(exc_info.value)
        assert mock_run.call_count == 2
        assert mock_sleep.call_count == 1