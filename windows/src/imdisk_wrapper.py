"""
ImDisk wrapper for VHD mounting operations.
Provides a Python interface to ImDisk MountImg.exe for virtual drive management.
"""

import os
import subprocess
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class MountResult(Enum):
    """Result codes for mount operations."""
    SUCCESS = "success"
    ALREADY_MOUNTED = "already_mounted"
    FILE_NOT_FOUND = "file_not_found"
    TOOL_NOT_FOUND = "tool_not_found"
    PERMISSION_DENIED = "permission_denied"
    DRIVE_IN_USE = "drive_in_use"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class DriveInfo:
    """Information about a mounted drive."""
    drive_letter: str
    vhd_path: str
    is_mounted: bool
    size_bytes: Optional[int] = None
    free_space_bytes: Optional[int] = None
    file_system: Optional[str] = None


class ImDiskWrapper:
    """
    Wrapper class for ImDisk MountImg.exe operations.
    
    Provides methods for mounting, unmounting, and checking VHD files
    with proper error handling and logging integration.
    """
    
    def __init__(self, mount_tool_path: str, logger: Optional[logging.Logger] = None):
        """
        Initialize ImDisk wrapper.
        
        Args:
            mount_tool_path: Path to MountImg.exe
            logger: Logger instance for operation logging
        """
        self.mount_tool_path = Path(mount_tool_path)
        self.logger = logger or logging.getLogger(__name__)
        
        # Validate mount tool exists
        if not self.mount_tool_path.exists():
            raise FileNotFoundError(f"ImDisk MountImg.exe not found at: {mount_tool_path}")
            
        self.logger.info(f"ImDisk wrapper initialized with tool: {mount_tool_path}")
        
    def mount_vhd(self, vhd_path: str, drive_letter: str, 
                  timeout: int = 30) -> MountResult:
        """
        Mount a VHD file to specified drive letter.
        
        Args:
            vhd_path: Path to VHD file to mount
            drive_letter: Target drive letter (e.g., 'E:')
            timeout: Timeout in seconds for mount operation
            
        Returns:
            MountResult indicating success or failure reason
        """
        vhd_file = Path(vhd_path)
        
        # Validate VHD file exists
        if not vhd_file.exists():
            self.logger.error(f"VHD file not found: {vhd_path}")
            return MountResult.FILE_NOT_FOUND
            
        # Check if drive is already mounted
        if self.is_drive_mounted(drive_letter):
            current_vhd = self._get_mounted_vhd_path(drive_letter)
            if current_vhd and Path(current_vhd).resolve() == vhd_file.resolve():
                self.logger.info(f"VHD already mounted at {drive_letter}: {vhd_path}")
                return MountResult.ALREADY_MOUNTED
            else:
                self.logger.warning(f"Different VHD mounted at {drive_letter}, unmounting first")
                unmount_result = self.unmount_drive(drive_letter)
                if unmount_result != MountResult.SUCCESS:
                    return unmount_result
                    
        # Prepare mount command
        cmd = [
            str(self.mount_tool_path),
            "-a",  # Attach
            "-f", str(vhd_file),  # File path
            "-m", drive_letter  # Mount point
        ]
        
        try:
            self.logger.info(f"Mounting VHD: {vhd_path} -> {drive_letter}")
            
            # Execute mount command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Log command output
            if result.stdout:
                self.logger.debug(f"Mount stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"Mount stderr: {result.stderr.strip()}")
                
            # Check result
            if result.returncode == 0:
                # Verify mount was successful
                if self._verify_mount(drive_letter, vhd_path):
                    self.logger.info(f"Successfully mounted {vhd_path} at {drive_letter}")
                    return MountResult.SUCCESS
                else:
                    self.logger.error(f"Mount command succeeded but verification failed")
                    return MountResult.UNKNOWN_ERROR
            else:
                # Parse error from output
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.error(f"Mount failed (code {result.returncode}): {error_msg}")
                
                # Map common error codes to results
                if "access denied" in error_msg.lower():
                    return MountResult.PERMISSION_DENIED
                elif "in use" in error_msg.lower():
                    return MountResult.DRIVE_IN_USE
                else:
                    return MountResult.UNKNOWN_ERROR
                    
        except subprocess.TimeoutExpired:
            self.logger.error(f"Mount operation timed out after {timeout} seconds")
            return MountResult.UNKNOWN_ERROR
        except FileNotFoundError:
            self.logger.error(f"ImDisk tool not found: {self.mount_tool_path}")
            return MountResult.TOOL_NOT_FOUND
        except Exception as e:
            self.logger.error(f"Unexpected error during mount: {e}")
            return MountResult.UNKNOWN_ERROR
            
    def unmount_drive(self, drive_letter: str, force: bool = False, 
                     timeout: int = 30) -> MountResult:
        """
        Unmount a drive.
        
        Args:
            drive_letter: Drive letter to unmount (e.g., 'E:')
            force: Force unmount even if drive is in use
            timeout: Timeout in seconds for unmount operation
            
        Returns:
            MountResult indicating success or failure reason
        """
        # Check if drive is mounted
        if not self.is_drive_mounted(drive_letter):
            self.logger.info(f"Drive {drive_letter} is not mounted")
            return MountResult.SUCCESS
            
        # Prepare unmount command
        cmd = [
            str(self.mount_tool_path),
            "-d",  # Detach
            "-m", drive_letter  # Mount point
        ]
        
        if force:
            cmd.append("-f")  # Force unmount
            
        try:
            self.logger.info(f"Unmounting drive: {drive_letter}")
            
            # Execute unmount command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            # Log command output
            if result.stdout:
                self.logger.debug(f"Unmount stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger.debug(f"Unmount stderr: {result.stderr.strip()}")
                
            # Check result
            if result.returncode == 0:
                # Verify unmount was successful
                if not self.is_drive_mounted(drive_letter):
                    self.logger.info(f"Successfully unmounted {drive_letter}")
                    return MountResult.SUCCESS
                else:
                    self.logger.error(f"Unmount command succeeded but drive still mounted")
                    return MountResult.UNKNOWN_ERROR
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.error(f"Unmount failed (code {result.returncode}): {error_msg}")
                
                if "in use" in error_msg.lower() and not force:
                    self.logger.warning("Drive in use, retrying with force")
                    return self.unmount_drive(drive_letter, force=True, timeout=timeout)
                else:
                    return MountResult.UNKNOWN_ERROR
                    
        except subprocess.TimeoutExpired:
            self.logger.error(f"Unmount operation timed out after {timeout} seconds")
            return MountResult.UNKNOWN_ERROR
        except Exception as e:
            self.logger.error(f"Unexpected error during unmount: {e}")
            return MountResult.UNKNOWN_ERROR
            
    def is_drive_mounted(self, drive_letter: str) -> bool:
        """
        Check if a drive letter is currently mounted.
        
        Args:
            drive_letter: Drive letter to check (e.g., 'E:')
            
        Returns:
            True if drive is mounted, False otherwise
        """
        try:
            # Normalize drive letter
            if not drive_letter.endswith(':'):
                drive_letter += ':'
                
            # Check if drive exists and is accessible
            drive_path = Path(drive_letter + '\\')
            return drive_path.exists() and drive_path.is_dir()
            
        except Exception as e:
            self.logger.debug(f"Error checking drive {drive_letter}: {e}")
            return False
            
    def get_drive_info(self, drive_letter: str) -> Optional[DriveInfo]:
        """
        Get detailed information about a mounted drive.
        
        Args:
            drive_letter: Drive letter to query (e.g., 'E:')
            
        Returns:
            DriveInfo object with drive details, or None if not mounted
        """
        if not self.is_drive_mounted(drive_letter):
            return None
            
        try:
            # Normalize drive letter
            if not drive_letter.endswith(':'):
                drive_letter += ':'
                
            drive_path = Path(drive_letter + '\\')
            
            # Get VHD path from ImDisk
            vhd_path = self._get_mounted_vhd_path(drive_letter)
            
            # Get disk usage information
            try:
                import shutil
                total, used, free = shutil.disk_usage(drive_path)
                size_bytes = total
                free_space_bytes = free
            except Exception:
                size_bytes = None
                free_space_bytes = None
                
            # Get file system type
            file_system = self._get_file_system_type(drive_letter)
            
            return DriveInfo(
                drive_letter=drive_letter,
                vhd_path=vhd_path or "Unknown",
                is_mounted=True,
                size_bytes=size_bytes,
                free_space_bytes=free_space_bytes,
                file_system=file_system
            )
            
        except Exception as e:
            self.logger.error(f"Error getting drive info for {drive_letter}: {e}")
            return None
            
    def list_mounted_drives(self) -> List[DriveInfo]:
        """
        List all ImDisk mounted drives.
        
        Returns:
            List of DriveInfo objects for mounted drives
        """
        mounted_drives = []
        
        try:
            # Query ImDisk for mounted devices
            cmd = [str(self.mount_tool_path), "-l"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse ImDisk output to find mounted drives
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ':' in line and 'VHD' in line.upper():
                        # Extract drive letter and VHD path from output
                        # Format varies, so this is a basic parser
                        parts = line.split()
                        for part in parts:
                            if ':' in part and len(part) <= 3:
                                drive_letter = part.rstrip('\\')
                                drive_info = self.get_drive_info(drive_letter)
                                if drive_info:
                                    mounted_drives.append(drive_info)
                                break
                                
        except Exception as e:
            self.logger.error(f"Error listing mounted drives: {e}")
            
        return mounted_drives
        
    def _verify_mount(self, drive_letter: str, expected_vhd_path: str) -> bool:
        """
        Verify that a mount operation was successful.
        
        Args:
            drive_letter: Expected drive letter
            expected_vhd_path: Expected VHD file path
            
        Returns:
            True if mount is verified, False otherwise
        """
        try:
            # Check if drive is accessible
            if not self.is_drive_mounted(drive_letter):
                return False
                
            # Optionally verify VHD path matches
            mounted_vhd = self._get_mounted_vhd_path(drive_letter)
            if mounted_vhd:
                expected_path = Path(expected_vhd_path).resolve()
                mounted_path = Path(mounted_vhd).resolve()
                return expected_path == mounted_path
                
            # If we can't verify VHD path, just check if drive is accessible
            return True
            
        except Exception as e:
            self.logger.debug(f"Error verifying mount: {e}")
            return False
            
    def _get_mounted_vhd_path(self, drive_letter: str) -> Optional[str]:
        """
        Get the VHD file path for a mounted drive.
        
        Args:
            drive_letter: Drive letter to query
            
        Returns:
            VHD file path or None if not found
        """
        try:
            # Query ImDisk for device information
            cmd = [str(self.mount_tool_path), "-l", "-m", drive_letter]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                # Parse output to extract VHD path
                # This is implementation-specific to ImDisk output format
                output = result.stdout.strip()
                # Look for file path in output
                for line in output.split('\n'):
                    if '.vhd' in line.lower():
                        # Extract file path (this may need adjustment based on actual output)
                        return line.strip()
                        
        except Exception as e:
            self.logger.debug(f"Error getting VHD path for {drive_letter}: {e}")
            
        return None
        
    def _get_file_system_type(self, drive_letter: str) -> Optional[str]:
        """
        Get the file system type for a drive.
        
        Args:
            drive_letter: Drive letter to query
            
        Returns:
            File system type string or None
        """
        try:
            import win32api
            import win32file
            
            # Normalize drive letter
            if not drive_letter.endswith(':'):
                drive_letter += ':'
                
            # Get volume information
            volume_info = win32api.GetVolumeInformation(drive_letter + '\\')
            return volume_info[4]  # File system name
            
        except Exception:
            # Fallback method using subprocess
            try:
                cmd = ['fsutil', 'fsinfo', 'volumeinfo', drive_letter]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'File System Name' in line:
                            return line.split(':')[-1].strip()
                            
            except Exception:
                pass
                
        return None


class VirtualDriveManager:
    """
    High-level manager for virtual drive operations.
    
    Provides simplified interface for common virtual drive management tasks
    with automatic retry logic and comprehensive logging.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize virtual drive manager.
        
        Args:
            config: Configuration dictionary with drive settings
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize ImDisk wrapper
        mount_tool_path = config.get('mountTool', r'C:\Program Files\ImDisk\MountImg.exe')
        self.imdisk = ImDiskWrapper(mount_tool_path, self.logger)
        
        # Configuration
        self.vhd_file = config.get('virtualDriveFile')
        self.drive_letter = config.get('driveLetter', 'E:')
        self.retry_attempts = config.get('retryAttempts', 3)
        self.retry_delay = config.get('retryDelay', 5)
        
        if not self.vhd_file:
            raise ValueError("virtualDriveFile not specified in configuration")
            
        self.logger.info(f"Virtual drive manager initialized: {self.vhd_file} -> {self.drive_letter}")
        
    def ensure_drive_mounted(self) -> bool:
        """
        Ensure the virtual drive is mounted, with retry logic.
        
        Returns:
            True if drive is mounted successfully, False otherwise
        """
        for attempt in range(self.retry_attempts):
            try:
                # Check if already mounted
                if self.imdisk.is_drive_mounted(self.drive_letter):
                    # Verify it's the correct VHD
                    mounted_vhd = self.imdisk._get_mounted_vhd_path(self.drive_letter)
                    if mounted_vhd and Path(mounted_vhd).resolve() == Path(self.vhd_file).resolve():
                        self.logger.debug(f"Drive {self.drive_letter} already correctly mounted")
                        return True
                    else:
                        self.logger.warning(f"Wrong VHD mounted at {self.drive_letter}, remounting")
                        self.imdisk.unmount_drive(self.drive_letter, force=True)
                        
                # Attempt to mount
                result = self.imdisk.mount_vhd(self.vhd_file, self.drive_letter)
                
                if result == MountResult.SUCCESS:
                    self.logger.info(f"Successfully mounted virtual drive on attempt {attempt + 1}")
                    return True
                elif result == MountResult.ALREADY_MOUNTED:
                    return True
                else:
                    self.logger.warning(f"Mount attempt {attempt + 1} failed: {result.value}")
                    
            except Exception as e:
                self.logger.error(f"Mount attempt {attempt + 1} error: {e}")
                
            # Wait before retry (except on last attempt)
            if attempt < self.retry_attempts - 1:
                self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                
        self.logger.error(f"Failed to mount virtual drive after {self.retry_attempts} attempts")
        return False
        
    def check_drive_status(self) -> DriveInfo:
        """
        Check the current status of the virtual drive.
        
        Returns:
            DriveInfo object with current drive status
        """
        drive_info = self.imdisk.get_drive_info(self.drive_letter)
        
        if drive_info:
            self.logger.debug(f"Drive {self.drive_letter} status: mounted, "
                            f"free space: {drive_info.free_space_bytes} bytes")
        else:
            self.logger.debug(f"Drive {self.drive_letter} is not mounted")
            
        return drive_info
        
    def unmount_drive(self, force: bool = False) -> bool:
        """
        Unmount the virtual drive.
        
        Args:
            force: Force unmount even if drive is in use
            
        Returns:
            True if unmounted successfully, False otherwise
        """
        result = self.imdisk.unmount_drive(self.drive_letter, force=force)
        
        if result == MountResult.SUCCESS:
            self.logger.info(f"Successfully unmounted drive {self.drive_letter}")
            return True
        else:
            self.logger.error(f"Failed to unmount drive {self.drive_letter}: {result.value}")
            return False
            
    def get_drive_contents(self) -> List[Path]:
        """
        Get list of files and directories on the virtual drive.
        
        Returns:
            List of Path objects for drive contents
        """
        contents = []
        
        try:
            if not self.imdisk.is_drive_mounted(self.drive_letter):
                self.logger.warning(f"Drive {self.drive_letter} not mounted")
                return contents
                
            drive_path = Path(self.drive_letter + '\\')
            
            # Recursively list all files and directories
            for item in drive_path.rglob('*'):
                contents.append(item)
                
            self.logger.debug(f"Found {len(contents)} items on drive {self.drive_letter}")
            
        except Exception as e:
            self.logger.error(f"Error listing drive contents: {e}")
            
        return contents


def main():
    """Command-line interface for ImDisk wrapper testing."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='ImDisk VHD Management Tool')
    parser.add_argument('--test', action='store_true', 
                       help='Test ImDisk installation and basic functionality')
    parser.add_argument('--mount', metavar='VHD_FILE', 
                       help='Mount a VHD file')
    parser.add_argument('--unmount', metavar='DRIVE_LETTER', 
                       help='Unmount a drive letter')
    parser.add_argument('--drive', metavar='DRIVE_LETTER', default='E:', 
                       help='Drive letter to use (default: E:)')
    parser.add_argument('--tool', metavar='PATH', 
                       default=r'C:\Program Files\ImDisk\MountImg.exe',
                       help='Path to MountImg.exe')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        if args.test:
            print("Testing ImDisk installation and functionality...")
            print(f"ImDisk tool path: {args.tool}")
            
            # Check if ImDisk tool exists
            if not Path(args.tool).exists():
                print(f"❌ ERROR: ImDisk tool not found at: {args.tool}")
                print("Please install ImDisk Toolkit from: https://www.ltr-data.se/opencode.html/#ImDisk")
                return 1
            else:
                print(f"✅ ImDisk tool found: {args.tool}")
            
            # Initialize wrapper
            try:
                wrapper = ImDiskWrapper(args.tool, logger)
                print("✅ ImDisk wrapper initialized successfully")
            except Exception as e:
                print(f"❌ ERROR: Failed to initialize ImDisk wrapper: {e}")
                return 1
            
            # Test listing mounted drives
            try:
                mounted_drives = wrapper.list_mounted_drives()
                print(f"✅ Successfully queried mounted drives: {len(mounted_drives)} found")
                
                if mounted_drives:
                    print("\nCurrently mounted ImDisk drives:")
                    for drive in mounted_drives:
                        print(f"  - {drive.drive_letter} -> {drive.vhd_path}")
                else:
                    print("  No ImDisk drives currently mounted")
                    
            except Exception as e:
                print(f"⚠️  WARNING: Could not list mounted drives: {e}")
            
            # Test drive letter availability
            test_drive = args.drive
            if wrapper.is_drive_mounted(test_drive):
                print(f"ℹ️  Drive {test_drive} is currently in use")
                drive_info = wrapper.get_drive_info(test_drive)
                if drive_info:
                    print(f"   VHD: {drive_info.vhd_path}")
                    if drive_info.free_space_bytes:
                        free_gb = drive_info.free_space_bytes / (1024**3)
                        print(f"   Free space: {free_gb:.1f} GB")
            else:
                print(f"✅ Drive letter {test_drive} is available for mounting")
            
            print("\n🎉 ImDisk test completed successfully!")
            print("\nNext steps:")
            print("1. Create or locate your VHD file")
            print(f"2. Test mounting: python {__file__} --mount path\\to\\file.vhd --drive {test_drive}")
            print(f"3. Test unmounting: python {__file__} --unmount {test_drive}")
            
            return 0
            
        elif args.mount:
            vhd_file = args.mount
            drive_letter = args.drive
            
            print(f"Mounting {vhd_file} to {drive_letter}...")
            
            wrapper = ImDiskWrapper(args.tool, logger)
            result = wrapper.mount_vhd(vhd_file, drive_letter)
            
            if result == MountResult.SUCCESS:
                print(f"✅ Successfully mounted {vhd_file} to {drive_letter}")
                return 0
            else:
                print(f"❌ Mount failed: {result.value}")
                return 1
                
        elif args.unmount:
            drive_letter = args.unmount
            
            print(f"Unmounting {drive_letter}...")
            
            wrapper = ImDiskWrapper(args.tool, logger)
            result = wrapper.unmount_drive(drive_letter)
            
            if result == MountResult.SUCCESS:
                print(f"✅ Successfully unmounted {drive_letter}")
                return 0
            else:
                print(f"❌ Unmount failed: {result.value}")
                return 1
                
        else:
            parser.print_help()
            return 0
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())