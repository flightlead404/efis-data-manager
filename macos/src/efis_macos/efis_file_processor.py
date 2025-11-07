"""
EFIS file processing engine for demo files, snapshots, and logbook CSV files.
"""

import os
import re
import csv
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Use importlib to import config to avoid conflicts
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("local_config", Path(__file__).parent / "config.py")
local_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_config)
MacOSConfig = local_config.MacOSConfig

from usb_drive_processor import SafeDriveAccess


@dataclass
class DemoFileInfo:
    """Information about a demo file."""
    filename: str
    original_path: str
    timestamp: datetime
    flight_number: Optional[int] = None
    
    @classmethod
    def from_filename(cls, filename: str, path: str) -> Optional['DemoFileInfo']:
        """Parse demo file information from filename."""
        # Pattern: DEMO-YYYYMMDD-HHMMSS[+N].LOG
        pattern = r'DEMO-(\d{8})-(\d{6})(?:\+(\d+))?\.LOG$'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if not match:
            return None
        
        date_str, time_str, flight_num = match.groups()
        
        try:
            timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            flight_number = int(flight_num) if flight_num else None
            
            return cls(
                filename=filename,
                original_path=path,
                timestamp=timestamp,
                flight_number=flight_number
            )
        except ValueError:
            return None


@dataclass
class SnapshotFileInfo:
    """Information about a snapshot file."""
    filename: str
    original_path: str
    timestamp: Optional[datetime] = None
    
    @classmethod
    def from_file(cls, filename: str, path: str) -> 'SnapshotFileInfo':
        """Create snapshot file info."""
        # Try to extract timestamp from filename if it follows a pattern
        timestamp = None
        
        # Common patterns: SNAP_YYYYMMDD_HHMMSS.png, Screenshot_YYYY-MM-DD_HH-MM-SS.png
        patterns = [
            r'SNAP_(\d{8})_(\d{6})\.png$',
            r'Screenshot_(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})\.png$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:  # SNAP format
                        date_str, time_str = match.groups()
                        timestamp = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    elif len(match.groups()) == 6:  # Screenshot format
                        year, month, day, hour, minute, second = match.groups()
                        timestamp = datetime(int(year), int(month), int(day), 
                                           int(hour), int(minute), int(second))
                    break
                except ValueError:
                    continue
        
        return cls(
            filename=filename,
            original_path=path,
            timestamp=timestamp
        )


@dataclass
class LogbookFileInfo:
    """Information about a logbook CSV file."""
    filename: str
    original_path: str
    row_count: int = 0
    date_range: Optional[Tuple[datetime, datetime]] = None
    
    @classmethod
    def from_file(cls, filename: str, path: str) -> 'LogbookFileInfo':
        """Create logbook file info and analyze contents."""
        info = cls(filename=filename, original_path=path)
        
        try:
            # Analyze CSV file to get row count and date range
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                info.row_count = len(rows)
                
                # Try to find date columns and determine range
                date_columns = ['date', 'flight_date', 'Date', 'Flight Date']
                dates = []
                
                for row in rows:
                    for col in date_columns:
                        if col in row and row[col]:
                            try:
                                # Try common date formats
                                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']:
                                    try:
                                        date = datetime.strptime(row[col], fmt)
                                        dates.append(date)
                                        break
                                    except ValueError:
                                        continue
                            except:
                                continue
                
                if dates:
                    info.date_range = (min(dates), max(dates))
                    
        except Exception as e:
            logging.getLogger(__name__).debug(f"Error analyzing logbook file {filename}: {e}")
        
        return info


class DemoFileProcessor:
    """Processes EFIS demo files."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.safe_access = SafeDriveAccess()
    
    def detect_demo_files(self, drive_path: Path) -> List[DemoFileInfo]:
        """Detect and parse demo files on the drive."""
        demo_files = []
        
        try:
            # Look for demo files in root and DEMO directory
            search_paths = [drive_path]
            demo_dir = drive_path / "DEMO"
            if demo_dir.exists():
                search_paths.append(demo_dir)
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                for file_path in search_path.iterdir():
                    if file_path.is_file() and file_path.name.upper().endswith('.LOG'):
                        demo_info = DemoFileInfo.from_filename(file_path.name, str(file_path))
                        if demo_info:
                            demo_files.append(demo_info)
                            self.logger.debug(f"Found demo file: {demo_info.filename}")
        
        except Exception as e:
            self.logger.error(f"Error detecting demo files: {e}")
        
        return demo_files
    
    def process_demo_files(self, demo_files: List[DemoFileInfo]) -> Dict[str, int]:
        """Process demo files by moving them to the archive."""
        results = {'moved': 0, 'errors': 0}
        
        # Ensure demo archive directory exists
        demo_archive = Path(self.config.demo_path)
        demo_archive.mkdir(parents=True, exist_ok=True)
        
        for demo_file in demo_files:
            try:
                src_path = Path(demo_file.original_path)
                
                # Create destination filename with date prefix for better organization
                date_prefix = demo_file.timestamp.strftime("%Y-%m-%d")
                if demo_file.flight_number:
                    dest_filename = f"{date_prefix}_flight-{demo_file.flight_number}_{demo_file.filename}"
                else:
                    dest_filename = f"{date_prefix}_{demo_file.filename}"
                
                dest_path = demo_archive / dest_filename
                
                # Check if file already exists
                if dest_path.exists():
                    self.logger.info(f"Demo file already exists, skipping: {dest_filename}")
                    continue
                
                # Move the file
                if self.safe_access.safe_move_file(src_path, dest_path):
                    self.logger.info(f"Moved demo file: {demo_file.filename} -> {dest_filename}")
                    results['moved'] += 1
                else:
                    self.logger.error(f"Failed to move demo file: {demo_file.filename}")
                    results['errors'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing demo file {demo_file.filename}: {e}")
                results['errors'] += 1
        
        return results


class SnapshotProcessor:
    """Processes EFIS snapshot PNG files."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.safe_access = SafeDriveAccess()
    
    def detect_snapshot_files(self, drive_path: Path) -> List[SnapshotFileInfo]:
        """Detect snapshot PNG files on the drive."""
        snapshots = []
        
        try:
            # Look for PNG files in root and SNAP directory
            search_paths = [drive_path]
            snap_dir = drive_path / "SNAP"
            if snap_dir.exists():
                search_paths.append(snap_dir)
            
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                for file_path in search_path.iterdir():
                    if (file_path.is_file() and 
                        file_path.suffix.lower() == '.png'):
                        
                        snapshot_info = SnapshotFileInfo.from_file(file_path.name, str(file_path))
                        snapshots.append(snapshot_info)
                        self.logger.debug(f"Found snapshot: {snapshot_info.filename}")
        
        except Exception as e:
            self.logger.error(f"Error detecting snapshot files: {e}")
        
        return snapshots
    
    def process_snapshot_files(self, snapshots: List[SnapshotFileInfo]) -> Dict[str, int]:
        """Process snapshot files by moving them to the archive."""
        results = {'moved': 0, 'errors': 0}
        
        # Create snapshots directory in demo path
        snapshot_archive = Path(self.config.demo_path) / "snapshots"
        snapshot_archive.mkdir(parents=True, exist_ok=True)
        
        for snapshot in snapshots:
            try:
                src_path = Path(snapshot.original_path)
                
                # Create destination filename with timestamp if available
                if snapshot.timestamp:
                    date_prefix = snapshot.timestamp.strftime("%Y-%m-%d_%H%M%S")
                    dest_filename = f"{date_prefix}_{snapshot.filename}"
                else:
                    dest_filename = snapshot.filename
                
                dest_path = snapshot_archive / dest_filename
                
                # Check if file already exists
                if dest_path.exists():
                    self.logger.info(f"Snapshot already exists, skipping: {dest_filename}")
                    continue
                
                # Move the file
                if self.safe_access.safe_move_file(src_path, dest_path):
                    self.logger.info(f"Moved snapshot: {snapshot.filename} -> {dest_filename}")
                    results['moved'] += 1
                else:
                    self.logger.error(f"Failed to move snapshot: {snapshot.filename}")
                    results['errors'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing snapshot {snapshot.filename}: {e}")
                results['errors'] += 1
        
        return results


class LogbookProcessor:
    """Processes EFIS logbook CSV files."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.safe_access = SafeDriveAccess()
    
    def detect_logbook_files(self, drive_path: Path) -> List[LogbookFileInfo]:
        """Detect logbook CSV files on the drive."""
        logbooks = []
        
        try:
            # Look for CSV files that might be logbooks
            for file_path in drive_path.rglob("*.csv"):
                if file_path.is_file():
                    # Check if filename suggests it's a logbook
                    filename_lower = file_path.name.lower()
                    if any(keyword in filename_lower for keyword in ['logbook', 'log', 'flight']):
                        logbook_info = LogbookFileInfo.from_file(file_path.name, str(file_path))
                        logbooks.append(logbook_info)
                        self.logger.debug(f"Found logbook: {logbook_info.filename} ({logbook_info.row_count} entries)")
        
        except Exception as e:
            self.logger.error(f"Error detecting logbook files: {e}")
        
        return logbooks
    
    def process_logbook_files(self, logbooks: List[LogbookFileInfo]) -> Dict[str, int]:
        """Process logbook files with date-based renaming."""
        results = {'moved': 0, 'errors': 0}
        
        # Ensure logbook archive directory exists
        logbook_archive = Path(self.config.logbook_path)
        logbook_archive.mkdir(parents=True, exist_ok=True)
        
        for logbook in logbooks:
            try:
                src_path = Path(logbook.original_path)
                
                # Create destination filename with date range if available
                if logbook.date_range:
                    start_date = logbook.date_range[0].strftime("%Y-%m-%d")
                    end_date = logbook.date_range[1].strftime("%Y-%m-%d")
                    if start_date == end_date:
                        date_prefix = start_date
                    else:
                        date_prefix = f"{start_date}_to_{end_date}"
                    dest_filename = f"{date_prefix}_logbook_{logbook.row_count}entries.csv"
                else:
                    # Use current date as fallback
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    dest_filename = f"{current_date}_logbook_{logbook.row_count}entries.csv"
                
                dest_path = logbook_archive / dest_filename
                
                # Check if file already exists
                if dest_path.exists():
                    self.logger.info(f"Logbook already exists, skipping: {dest_filename}")
                    continue
                
                # Move the file
                if self.safe_access.safe_move_file(src_path, dest_path):
                    self.logger.info(f"Moved logbook: {logbook.filename} -> {dest_filename}")
                    results['moved'] += 1
                else:
                    self.logger.error(f"Failed to move logbook: {logbook.filename}")
                    results['errors'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing logbook {logbook.filename}: {e}")
                results['errors'] += 1
        
        return results


class EFISFileProcessor:
    """Main EFIS file processing coordinator."""
    
    def __init__(self, config: MacOSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize processors
        self.demo_processor = DemoFileProcessor(config)
        self.snapshot_processor = SnapshotProcessor(config)
        self.logbook_processor = LogbookProcessor(config)
    
    def process_efis_drive(self, drive_path: str) -> Dict[str, any]:
        """Process all EFIS files on a drive."""
        drive_path = Path(drive_path)
        results = {
            'demo_files': {'detected': 0, 'moved': 0, 'errors': 0},
            'snapshots': {'detected': 0, 'moved': 0, 'errors': 0},
            'logbooks': {'detected': 0, 'moved': 0, 'errors': 0},
            'total_files_processed': 0,
            'success': True,
            'errors': []
        }
        
        try:
            self.logger.info(f"Processing EFIS drive: {drive_path}")
            
            # Process demo files
            demo_files = self.demo_processor.detect_demo_files(drive_path)
            results['demo_files']['detected'] = len(demo_files)
            
            if demo_files:
                demo_results = self.demo_processor.process_demo_files(demo_files)
                results['demo_files'].update(demo_results)
            
            # Process snapshots
            snapshots = self.snapshot_processor.detect_snapshot_files(drive_path)
            results['snapshots']['detected'] = len(snapshots)
            
            if snapshots:
                snapshot_results = self.snapshot_processor.process_snapshot_files(snapshots)
                results['snapshots'].update(snapshot_results)
            
            # Process logbooks
            logbooks = self.logbook_processor.detect_logbook_files(drive_path)
            results['logbooks']['detected'] = len(logbooks)
            
            if logbooks:
                logbook_results = self.logbook_processor.process_logbook_files(logbooks)
                results['logbooks'].update(logbook_results)
            
            # Calculate totals
            results['total_files_processed'] = (
                results['demo_files']['moved'] + 
                results['snapshots']['moved'] + 
                results['logbooks']['moved']
            )
            
            total_errors = (
                results['demo_files']['errors'] + 
                results['snapshots']['errors'] + 
                results['logbooks']['errors']
            )
            
            if total_errors > 0:
                results['success'] = False
                results['errors'].append(f"Processing completed with {total_errors} errors")
            
            self.logger.info(f"EFIS processing complete: {results['total_files_processed']} files processed")
            
        except Exception as e:
            self.logger.error(f"Error processing EFIS drive: {e}")
            results['success'] = False
            results['errors'].append(f"Processing error: {e}")
        
        return results
    
    def cleanup_drive(self, drive_path: str) -> bool:
        """Clean up processed files and empty directories on the drive."""
        try:
            drive_path = Path(drive_path)
            
            # Remove empty directories
            for dir_path in [drive_path / "DEMO", drive_path / "SNAP"]:
                if dir_path.exists() and dir_path.is_dir():
                    try:
                        # Only remove if empty
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            self.logger.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        pass  # Directory not empty or permission issue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up drive: {e}")
            return False