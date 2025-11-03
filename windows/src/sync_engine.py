"""
File synchronization engine for EFIS Data Manager.
Optimized for syncing many small PNG chart files via HTTP.
"""

import os
import json
import hashlib
import zipfile
import tempfile
import requests
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

from network_manager import NetworkManager, ConnectionStatus


@dataclass
class FileInfo:
    """Information about a file for synchronization."""
    path: str
    size: int
    checksum: str
    last_modified: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    success: bool
    files_transferred: int
    bytes_transferred: int
    files_skipped: int
    files_failed: int
    duration_seconds: float
    error_message: Optional[str] = None
    failed_files: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting."""
        return asdict(self)


class FileManifest:
    """
    Manages file manifests for synchronization.
    
    A manifest contains checksums and metadata for all files
    to enable efficient incremental synchronization.
    """
    
    def __init__(self, base_path: str):
        """Initialize manifest for a base directory."""
        self.base_path = Path(base_path)
        self.files: Dict[str, FileInfo] = {}
        
    def scan_directory(self, extensions: List[str] = None) -> None:
        """
        Scan directory and build file manifest.
        
        Args:
            extensions: List of file extensions to include (e.g., ['.png', '.jpg'])
        """
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            
        self.files.clear()
        
        if not self.base_path.exists():
            return
            
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                # Check extension filter
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                    
                # Calculate relative path
                rel_path = file_path.relative_to(self.base_path)
                rel_path_str = str(rel_path).replace('\\', '/')  # Normalize path separators
                
                # Get file info
                stat = file_path.stat()
                checksum = self._calculate_checksum(file_path)
                
                self.files[rel_path_str] = FileInfo(
                    path=rel_path_str,
                    size=stat.st_size,
                    checksum=checksum,
                    last_modified=stat.st_mtime
                )
                
    def get_changed_files(self, other_manifest: 'FileManifest') -> List[str]:
        """
        Get list of files that are different from another manifest.
        
        Args:
            other_manifest: Manifest to compare against
            
        Returns:
            List of relative file paths that are different
        """
        changed_files = []
        
        for rel_path, file_info in self.files.items():
            other_file = other_manifest.files.get(rel_path)
            
            if not other_file:
                # File doesn't exist in other manifest
                changed_files.append(rel_path)
            elif other_file.checksum != file_info.checksum:
                # File exists but checksum is different
                changed_files.append(rel_path)
                
        return changed_files
        
    def get_deleted_files(self, other_manifest: 'FileManifest') -> List[str]:
        """
        Get list of files that exist in other manifest but not in this one.
        
        Args:
            other_manifest: Manifest to compare against
            
        Returns:
            List of relative file paths that were deleted
        """
        return [rel_path for rel_path in other_manifest.files.keys() 
                if rel_path not in self.files]
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary for JSON serialization."""
        return {
            'base_path': str(self.base_path),
            'files': {path: file_info.to_dict() for path, file_info in self.files.items()},
            'generated_at': datetime.now().isoformat()
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileManifest':
        """Create manifest from dictionary."""
        manifest = cls(data['base_path'])
        manifest.files = {
            path: FileInfo.from_dict(file_data) 
            for path, file_data in data.get('files', {}).items()
        }
        return manifest
        
    def save_to_file(self, file_path: str) -> None:
        """Save manifest to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_from_file(cls, file_path: str) -> 'FileManifest':
        """Load manifest from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
        
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()


class SyncEngine:
    """
    HTTP-based file synchronization engine.
    
    Optimized for syncing many small PNG files with batch transfers
    and compression to minimize network overhead.
    """
    
    def __init__(self, network_manager: NetworkManager, config: Dict[str, Any],
                 logger: Optional[logging.Logger] = None):
        """
        Initialize sync engine.
        
        Args:
            network_manager: NetworkManager for connectivity
            config: Configuration dictionary
            logger: Logger instance
        """
        self.network_manager = network_manager
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Sync configuration
        self.local_chart_path = config.get('localChartPath', 'E:\\Charts')
        self.batch_size_mb = config.get('batchSizeMB', 2)  # 2MB batches
        self.max_concurrent_requests = config.get('maxConcurrentRequests', 4)
        self.request_timeout = config.get('requestTimeout', 30)
        self.retry_attempts = config.get('retryAttempts', 3)
        self.retry_delay = config.get('retryDelay', 5)
        
        # HTTP session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EFIS-Data-Manager/1.0',
            'Accept': 'application/json, application/octet-stream',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # Base URL will be set when connection is established
        self.base_url = None
        
        self.logger.info(f"Sync engine initialized: {self.local_chart_path}")
        
    def sync_charts(self) -> SyncResult:
        """
        Perform complete chart synchronization.
        
        Returns:
            SyncResult with operation details
        """
        start_time = time.time()
        
        try:
            self.logger.info("Starting chart synchronization")
            
            # Establish connection to MacBook
            if not self._establish_connection():
                return SyncResult(
                    success=False,
                    files_transferred=0,
                    bytes_transferred=0,
                    files_skipped=0,
                    files_failed=0,
                    duration_seconds=time.time() - start_time,
                    error_message="Failed to establish connection to MacBook"
                )
                
            # Get local manifest
            local_manifest = self._get_local_manifest()
            
            # Get remote manifest
            remote_manifest = self._get_remote_manifest()
            if not remote_manifest:
                return SyncResult(
                    success=False,
                    files_transferred=0,
                    bytes_transferred=0,
                    files_skipped=0,
                    files_failed=0,
                    duration_seconds=time.time() - start_time,
                    error_message="Failed to get remote manifest"
                )
                
            # Determine files to sync
            changed_files = remote_manifest.get_changed_files(local_manifest)
            deleted_files = remote_manifest.get_deleted_files(local_manifest)
            
            self.logger.info(f"Sync analysis: {len(changed_files)} changed, {len(deleted_files)} deleted")
            
            # Perform synchronization
            sync_stats = self._sync_files(changed_files, deleted_files, remote_manifest)
            
            # Save updated local manifest
            self._save_local_manifest(remote_manifest)
            
            duration = time.time() - start_time
            self.logger.info(f"Chart synchronization completed in {duration:.1f}s: "
                           f"{sync_stats['transferred']} files, {sync_stats['bytes']/(1024*1024):.1f} MB")
            
            return SyncResult(
                success=True,
                files_transferred=sync_stats['transferred'],
                bytes_transferred=sync_stats['bytes'],
                files_skipped=sync_stats['skipped'],
                files_failed=sync_stats['failed'],
                duration_seconds=duration,
                failed_files=sync_stats.get('failed_files', [])
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Chart synchronization failed: {e}")
            
            return SyncResult(
                success=False,
                files_transferred=0,
                bytes_transferred=0,
                files_skipped=0,
                files_failed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
            
    def _establish_connection(self) -> bool:
        """Establish connection to MacBook sync service."""
        try:
            # Discover MacBook
            network_info = self.network_manager.discover_macbook()
            if not network_info or network_info.status != ConnectionStatus.CONNECTED:
                self.logger.error("MacBook not reachable")
                return False
                
            # Set base URL
            self.base_url = f"http://{network_info.ip_address}:{network_info.port}/api/charts"
            
            # Test API endpoint
            response = self.session.get(
                f"{self.base_url}/status",
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Connected to MacBook sync service: {network_info.ip_address}")
                return True
            else:
                self.logger.error(f"MacBook sync service returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to establish connection: {e}")
            return False
            
    def _get_local_manifest(self) -> FileManifest:
        """Get or create local file manifest."""
        manifest_path = Path(self.local_chart_path) / '.sync_manifest.json'
        
        if manifest_path.exists():
            try:
                return FileManifest.load_from_file(str(manifest_path))
            except Exception as e:
                self.logger.warning(f"Failed to load local manifest: {e}")
                
        # Create new manifest by scanning local directory
        manifest = FileManifest(self.local_chart_path)
        manifest.scan_directory(['.png', '.jpg', '.jpeg'])
        return manifest
        
    def _get_remote_manifest(self) -> Optional[FileManifest]:
        """Get remote file manifest from MacBook."""
        try:
            response = self.session.get(
                f"{self.base_url}/manifest",
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                manifest_data = response.json()
                return FileManifest.from_dict(manifest_data)
            else:
                self.logger.error(f"Failed to get remote manifest: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting remote manifest: {e}")
            return None
            
    def _save_local_manifest(self, manifest: FileManifest) -> None:
        """Save local manifest to disk."""
        try:
            manifest_path = Path(self.local_chart_path) / '.sync_manifest.json'
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest.save_to_file(str(manifest_path))
        except Exception as e:
            self.logger.warning(f"Failed to save local manifest: {e}")
            
    def _sync_files(self, changed_files: List[str], deleted_files: List[str], 
                   remote_manifest: FileManifest) -> Dict[str, Any]:
        """
        Synchronize files with the remote system.
        
        Args:
            changed_files: List of files to download
            deleted_files: List of files to delete locally
            remote_manifest: Remote file manifest
            
        Returns:
            Dictionary with sync statistics
        """
        stats = {
            'transferred': 0,
            'bytes': 0,
            'skipped': 0,
            'failed': 0,
            'failed_files': []
        }
        
        # Delete local files that no longer exist remotely
        for file_path in deleted_files:
            try:
                local_file = Path(self.local_chart_path) / file_path
                if local_file.exists():
                    local_file.unlink()
                    self.logger.debug(f"Deleted local file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")
                
        # Download changed files in batches
        if changed_files:
            file_batches = self._create_file_batches(changed_files, remote_manifest)
            
            with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
                # Submit batch download tasks
                future_to_batch = {
                    executor.submit(self._download_file_batch, batch): batch
                    for batch in file_batches
                }
                
                # Process completed downloads
                for future in as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        batch_result = future.result()
                        stats['transferred'] += batch_result['transferred']
                        stats['bytes'] += batch_result['bytes']
                        stats['failed'] += batch_result['failed']
                        stats['failed_files'].extend(batch_result['failed_files'])
                        
                    except Exception as e:
                        self.logger.error(f"Batch download failed: {e}")
                        stats['failed'] += len(batch)
                        stats['failed_files'].extend(batch)
                        
        return stats
        
    def _create_file_batches(self, file_list: List[str], 
                           manifest: FileManifest) -> List[List[str]]:
        """
        Create batches of files for efficient downloading.
        
        Groups files into batches based on total size to optimize
        network transfers while keeping memory usage reasonable.
        
        Args:
            file_list: List of file paths to batch
            manifest: File manifest with size information
            
        Returns:
            List of file path batches
        """
        batches = []
        current_batch = []
        current_batch_size = 0
        max_batch_size = self.batch_size_mb * 1024 * 1024  # Convert to bytes
        
        for file_path in file_list:
            file_info = manifest.files.get(file_path)
            if not file_info:
                continue
                
            file_size = file_info.size
            
            # If adding this file would exceed batch size, start new batch
            if current_batch and (current_batch_size + file_size) > max_batch_size:
                batches.append(current_batch)
                current_batch = []
                current_batch_size = 0
                
            current_batch.append(file_path)
            current_batch_size += file_size
            
        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
            
        return batches
        
    def _download_file_batch(self, file_batch: List[str]) -> Dict[str, Any]:
        """
        Download a batch of files from the remote system.
        
        Args:
            file_batch: List of file paths to download
            
        Returns:
            Dictionary with batch download statistics
        """
        batch_stats = {
            'transferred': 0,
            'bytes': 0,
            'failed': 0,
            'failed_files': []
        }
        
        try:
            # Request batch download
            response = self.session.post(
                f"{self.base_url}/batch",
                json={'files': file_batch},
                timeout=self.request_timeout * 2,  # Longer timeout for batches
                stream=True
            )
            
            if response.status_code != 200:
                self.logger.error(f"Batch download failed: HTTP {response.status_code}")
                batch_stats['failed'] = len(file_batch)
                batch_stats['failed_files'] = file_batch
                return batch_stats
                
            # Download and extract batch
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Download to temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        batch_stats['bytes'] += len(chunk)
                        
                temp_file_path = temp_file.name
                
            # Extract files from ZIP archive
            try:
                with zipfile.ZipFile(temp_file_path, 'r') as zip_file:
                    for file_path in file_batch:
                        try:
                            # Extract file to correct location
                            local_file_path = Path(self.local_chart_path) / file_path
                            local_file_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            with zip_file.open(file_path) as source:
                                with open(local_file_path, 'wb') as target:
                                    target.write(source.read())
                                    
                            batch_stats['transferred'] += 1
                            self.logger.debug(f"Downloaded: {file_path}")
                            
                        except KeyError:
                            # File not in ZIP (server-side error)
                            self.logger.warning(f"File not in batch response: {file_path}")
                            batch_stats['failed'] += 1
                            batch_stats['failed_files'].append(file_path)
                        except Exception as e:
                            self.logger.error(f"Failed to extract {file_path}: {e}")
                            batch_stats['failed'] += 1
                            batch_stats['failed_files'].append(file_path)
                            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Batch download error: {e}")
            batch_stats['failed'] = len(file_batch)
            batch_stats['failed_files'] = file_batch
            
        return batch_stats


def create_sync_engine(network_manager: NetworkManager, config: Dict[str, Any],
                      logger: Optional[logging.Logger] = None) -> SyncEngine:
    """
    Factory function to create a configured SyncEngine.
    
    Args:
        network_manager: NetworkManager instance
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Configured SyncEngine instance
    """
    sync_config = config.get('sync', {})
    
    # Map configuration to sync engine settings
    engine_config = {
        'localChartPath': config.get('virtualDrive', {}).get('driveLetter', 'E:') + '\\Charts',
        'batchSizeMB': sync_config.get('batchSizeMB', 2),
        'maxConcurrentRequests': sync_config.get('maxConcurrentRequests', 4),
        'requestTimeout': sync_config.get('requestTimeout', 30),
        'retryAttempts': sync_config.get('retryAttempts', 3),
        'retryDelay': sync_config.get('retryDelay', 5)
    }
    
    return SyncEngine(network_manager, engine_config, logger)