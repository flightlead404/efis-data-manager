"""
File download and version management for EFIS Data Manager.
"""

import os
import hashlib
import shutil
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    error_message: Optional[str] = None
    download_time: Optional[datetime] = None


@dataclass
class VersionRecord:
    """Record of a software version."""
    software_type: str
    version: str
    file_path: str
    file_size: int
    file_hash: str
    download_date: datetime
    source_url: str
    is_current: bool = True


class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logging.getLogger(__name__)
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries + 1} attempts failed")
        
        raise last_exception


class FileIntegrityChecker:
    """Handles file integrity verification."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate hash of a file."""
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            raise
    
    def verify_file_integrity(self, file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """Verify file integrity against expected hash."""
        try:
            actual_hash = self.calculate_file_hash(file_path, algorithm)
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            self.logger.error(f"Error verifying integrity for {file_path}: {e}")
            return False


class VersionManager:
    """Manages version tracking and comparison."""
    
    def __init__(self, version_db_path: str):
        self.version_db_path = Path(version_db_path)
        self.logger = logging.getLogger(__name__)
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Ensure version database directory exists."""
        self.version_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load_version_records(self) -> Dict[str, VersionRecord]:
        """Load version records from database."""
        if not self.version_db_path.exists():
            return {}
        
        try:
            with open(self.version_db_path, 'r') as f:
                data = json.load(f)
            
            records = {}
            for software_type, record_data in data.items():
                # Convert datetime string back to datetime object
                record_data['download_date'] = datetime.fromisoformat(record_data['download_date'])
                records[software_type] = VersionRecord(**record_data)
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error loading version records: {e}")
            return {}
    
    def save_version_records(self, records: Dict[str, VersionRecord]):
        """Save version records to database."""
        try:
            # Convert records to serializable format
            data = {}
            for software_type, record in records.items():
                record_dict = asdict(record)
                # Convert datetime to string
                record_dict['download_date'] = record.download_date.isoformat()
                data[software_type] = record_dict
            
            with open(self.version_db_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved version records to {self.version_db_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving version records: {e}")
    
    def get_current_version(self, software_type: str) -> Optional[VersionRecord]:
        """Get current version record for software type."""
        records = self.load_version_records()
        return records.get(software_type)
    
    def add_version_record(self, record: VersionRecord):
        """Add a new version record."""
        records = self.load_version_records()
        
        # Mark previous version as not current
        if record.software_type in records:
            records[record.software_type].is_current = False
        
        # Add new record
        records[record.software_type] = record
        
        self.save_version_records(records)
        self.logger.info(f"Added version record for {record.software_type} v{record.version}")
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        try:
            # Simple version comparison - split by dots and compare numerically
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 < v2:
                    return -1
                elif v1 > v2:
                    return 1
            
            return 0
            
        except ValueError:
            # Fallback to string comparison if numeric comparison fails
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def needs_update(self, software_type: str, new_version: str) -> bool:
        """Check if software needs update."""
        current_record = self.get_current_version(software_type)
        
        if not current_record:
            return True  # No current version, so update needed
        
        return self.compare_versions(current_record.version, new_version) < 0


class FileArchiver:
    """Manages file archiving with proper directory structure."""
    
    def __init__(self, archive_root: str):
        self.archive_root = Path(archive_root)
        self.logger = logging.getLogger(__name__)
        self._ensure_archive_directory()
    
    def _ensure_archive_directory(self):
        """Ensure archive root directory exists."""
        self.archive_root.mkdir(parents=True, exist_ok=True)
    
    def get_archive_path(self, software_type: str, version: str, filename: str) -> Path:
        """Get the archive path for a file."""
        # Create directory structure: archive_root/software_type/version/filename
        return self.archive_root / software_type / version / filename
    
    def archive_file(self, source_path: str, software_type: str, version: str, filename: str) -> str:
        """Archive a file to the proper location."""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        archive_path = self.get_archive_path(software_type, version, filename)
        
        # Create directory structure
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file to archive
        shutil.copy2(source, archive_path)
        
        self.logger.info(f"Archived {filename} to {archive_path}")
        return str(archive_path)
    
    def list_archived_versions(self, software_type: str) -> List[str]:
        """List all archived versions for a software type."""
        software_dir = self.archive_root / software_type
        
        if not software_dir.exists():
            return []
        
        versions = []
        for version_dir in software_dir.iterdir():
            if version_dir.is_dir():
                versions.append(version_dir.name)
        
        return sorted(versions)


class SecureDownloader:
    """Secure HTTPS download client with integrity checking."""
    
    def __init__(self, download_dir: str = "/tmp/efis_downloads"):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library is required for downloading")
        
        self.download_dir = Path(download_dir)
        self.logger = logging.getLogger(__name__)
        self.retry_manager = RetryManager()
        self.integrity_checker = FileIntegrityChecker()
        
        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EFIS-Data-Manager/1.0 (macOS; Automated Download Client)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def _download_file_chunk(self, url: str, file_path: Path, chunk_size: int = 8192) -> Tuple[int, str]:
        """Download file in chunks and return size and hash."""
        hash_obj = hashlib.sha256()
        total_size = 0
        
        response = self.session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    hash_obj.update(chunk)
                    total_size += len(chunk)
        
        return total_size, hash_obj.hexdigest()
    
    def download_file(self, url: str, filename: Optional[str] = None, expected_hash: Optional[str] = None) -> DownloadResult:
        """Download a file with integrity checking and retry logic."""
        start_time = datetime.now()
        
        try:
            # Determine filename
            if not filename:
                filename = url.split('/')[-1]
                if not filename or '.' not in filename:
                    filename = f"download_{int(time.time())}.bin"
            
            file_path = self.download_dir / filename
            
            self.logger.info(f"Starting download: {url} -> {file_path}")
            
            # Download with retry
            def download_operation():
                return self._download_file_chunk(url, file_path)
            
            file_size, file_hash = self.retry_manager.execute_with_retry(download_operation)
            
            # Verify integrity if expected hash provided
            if expected_hash and file_hash.lower() != expected_hash.lower():
                file_path.unlink()  # Remove corrupted file
                return DownloadResult(
                    success=False,
                    error_message=f"Integrity check failed. Expected: {expected_hash}, Got: {file_hash}"
                )
            
            self.logger.info(f"Download completed: {file_path} ({file_size} bytes)")
            
            return DownloadResult(
                success=True,
                file_path=str(file_path),
                file_size=file_size,
                file_hash=file_hash,
                download_time=start_time
            )
            
        except Exception as e:
            self.logger.error(f"Download failed for {url}: {e}")
            return DownloadResult(
                success=False,
                error_message=str(e),
                download_time=start_time
            )
    
    def cleanup_downloads(self, max_age_hours: int = 24):
        """Clean up old download files."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file_path in self.download_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    self.logger.debug(f"Cleaned up old download: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up {file_path}: {e}")


class DownloadManager:
    """Main download and version management coordinator."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.downloader = SecureDownloader() if REQUESTS_AVAILABLE else None
        self.version_manager = VersionManager(
            os.path.join(config.archive_path, ".version_db.json")
        )
        self.archiver = FileArchiver(config.archive_path)
    
    def download_and_archive(self, software_type: str, version: str, download_url: str, 
                           expected_hash: Optional[str] = None) -> bool:
        """Download and archive a software update."""
        if not self.downloader:
            self.logger.error("Downloader not available (missing requests library)")
            return False
        
        try:
            # Check if update is needed
            if not self.version_manager.needs_update(software_type, version):
                self.logger.info(f"{software_type} v{version} is already current")
                return True
            
            # Download file
            filename = download_url.split('/')[-1]
            result = self.downloader.download_file(download_url, filename, expected_hash)
            
            if not result.success:
                self.logger.error(f"Download failed: {result.error_message}")
                return False
            
            # Archive file
            archived_path = self.archiver.archive_file(
                result.file_path, software_type, version, filename
            )
            
            # Create version record
            version_record = VersionRecord(
                software_type=software_type,
                version=version,
                file_path=archived_path,
                file_size=result.file_size,
                file_hash=result.file_hash,
                download_date=result.download_time,
                source_url=download_url,
                is_current=True
            )
            
            # Save version record
            self.version_manager.add_version_record(version_record)
            
            # Clean up temporary download
            if os.path.exists(result.file_path):
                os.remove(result.file_path)
            
            self.logger.info(f"Successfully downloaded and archived {software_type} v{version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading and archiving {software_type}: {e}")
            return False
    
    def get_software_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all managed software."""
        status = {}
        
        for software_type in ['nav_database', 'hxr_software', 'mini_ap_software', 
                             'ahrs_software', 'servo_software']:
            current_version = self.version_manager.get_current_version(software_type)
            archived_versions = self.archiver.list_archived_versions(software_type)
            
            status[software_type] = {
                'current_version': current_version.version if current_version else None,
                'current_file': current_version.file_path if current_version else None,
                'download_date': current_version.download_date.isoformat() if current_version else None,
                'archived_versions': archived_versions,
                'total_versions': len(archived_versions)
            }
        
        return status