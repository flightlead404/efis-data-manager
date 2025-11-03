"""
Examples of how to integrate error handling components into existing EFIS modules.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import time

from .integration import EFISErrorHandlingManager, get_default_config
from .file_system_errors import FileOperationResult
from .network_resilience import OperationPriority


class EnhancedUSBDriveProcessor:
    """
    Example of integrating error handling into USB drive processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced USB drive processor."""
        self.error_manager = EFISErrorHandlingManager(config or get_default_config())
        self.logger = self.error_manager.logger
        
    def process_efis_files(self, drive_path: str) -> Dict[str, Any]:
        """Process EFIS files with comprehensive error handling."""
        operation_id = self.logger.log_operation_start("process_efis_files", drive_path=drive_path)
        start_time = time.time()
        
        try:
            # Check drive permissions first
            has_perms, missing = self.error_manager.permission_checker.check_permissions(
                drive_path, ['read', 'write']
            )
            
            if not has_perms:
                guidance = self.error_manager.permission_checker.get_permission_guidance(
                    drive_path, missing
                )
                raise PermissionError(f"Insufficient permissions: {guidance}")
            
            # Check disk space
            self.error_manager.disk_monitor.check_all_paths()
            
            # Process files with atomic operations
            results = {
                'demo_files': self._process_demo_files(drive_path),
                'snap_files': self._process_snap_files(drive_path),
                'logbook_files': self._process_logbook_files(drive_path)
            }
            
            duration = time.time() - start_time
            self.logger.log_operation_end("process_efis_files", operation_id, True, duration)
            self.error_manager.performance_monitor.record_operation_time("process_efis_files", duration)
            
            return {
                'success': True,
                'results': results,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_operation_end("process_efis_files", operation_id, False, duration, error=str(e))
            self.logger.exception("Failed to process EFIS files", drive_path=drive_path)
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def _process_demo_files(self, drive_path: str) -> Dict[str, Any]:
        """Process demo files with error handling."""
        drive = Path(drive_path)
        demo_files = list(drive.rglob("DEMO-*.LOG"))
        
        processed = 0
        errors = []
        
        for demo_file in demo_files:
            # Use atomic file operations
            target_path = Path("~/Dropbox/Flying/EFIS-DEMO").expanduser() / demo_file.name
            
            result = self.error_manager.atomic_ops.atomic_move(demo_file, target_path)
            
            if result.success:
                processed += 1
                self.logger.info(f"Moved demo file: {demo_file.name}",
                               source=str(demo_file),
                               target=str(target_path),
                               bytes_processed=result.bytes_processed)
            else:
                errors.append(f"{demo_file.name}: {result.error_message}")
                self.logger.error(f"Failed to move demo file: {demo_file.name}",
                                error_type=result.error_type.value if result.error_type else 'unknown',
                                error_message=result.error_message)
        
        return {
            'total_found': len(demo_files),
            'processed': processed,
            'errors': errors
        }
    
    def _process_snap_files(self, drive_path: str) -> Dict[str, Any]:
        """Process snapshot files with error handling."""
        drive = Path(drive_path)
        snap_files = list(drive.rglob("*.png"))
        
        processed = 0
        errors = []
        
        for snap_file in snap_files:
            target_path = Path("~/Dropbox/Flying/EFIS-DEMO").expanduser() / snap_file.name
            
            result = self.error_manager.atomic_ops.atomic_copy(snap_file, target_path, verify=True)
            
            if result.success:
                processed += 1
                # Remove original after successful copy
                try:
                    snap_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Could not remove original snap file: {e}")
            else:
                errors.append(f"{snap_file.name}: {result.error_message}")
        
        return {
            'total_found': len(snap_files),
            'processed': processed,
            'errors': errors
        }
    
    def _process_logbook_files(self, drive_path: str) -> Dict[str, Any]:
        """Process logbook files with error handling."""
        drive = Path(drive_path)
        logbook_files = list(drive.rglob("*logbook*.csv"))
        
        processed = 0
        errors = []
        
        for logbook_file in logbook_files:
            # Generate date-based filename
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            target_name = f"Logbook {date_str}.csv"
            target_path = Path("~/Dropbox/Flying/Logbooks").expanduser() / target_name
            
            result = self.error_manager.atomic_ops.atomic_move(logbook_file, target_path)
            
            if result.success:
                processed += 1
            else:
                errors.append(f"{logbook_file.name}: {result.error_message}")
        
        return {
            'total_found': len(logbook_files),
            'processed': processed,
            'errors': errors
        }


class EnhancedSyncEngine:
    """
    Example of integrating network resilience into sync operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced sync engine."""
        self.error_manager = EFISErrorHandlingManager(config or get_default_config())
        self.logger = self.error_manager.logger
        
    def sync_charts_with_resilience(self) -> Dict[str, Any]:
        """Sync charts with network resilience."""
        operation_id = self.logger.log_operation_start("sync_charts")
        start_time = time.time()
        
        try:
            # Define sync operation
            def sync_operation():
                return self._perform_chart_sync()
            
            # Execute with network resilience
            result = self.error_manager.network_manager.execute_with_resilience(
                pool_name='macbook',
                operation=sync_operation,
                operation_id=operation_id,
                priority=OperationPriority.HIGH,
                max_retries=3,
                timeout=300.0
            )
            
            duration = time.time() - start_time
            self.logger.log_operation_end("sync_charts", operation_id, True, duration)
            self.error_manager.performance_monitor.record_operation_time("sync_charts", duration)
            
            return {
                'success': True,
                'result': result,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_operation_end("sync_charts", operation_id, False, duration, error=str(e))
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration,
                'queued_for_retry': 'queued for later execution' in str(e)
            }
    
    def _perform_chart_sync(self) -> Dict[str, Any]:
        """Perform actual chart synchronization."""
        # This would contain the actual sync logic
        # For example purposes, we'll simulate the operation
        
        self.logger.info("Starting chart synchronization")
        
        # Simulate file transfer
        files_transferred = 150
        bytes_transferred = 50 * 1024 * 1024  # 50MB
        
        # Record throughput metrics
        duration = 30.0  # Simulated duration
        self.error_manager.performance_monitor.record_throughput(
            "chart_sync", files_transferred, duration
        )
        
        return {
            'files_transferred': files_transferred,
            'bytes_transferred': bytes_transferred,
            'duration': duration
        }


class EnhancedGRTScraper:
    """
    Example of integrating error handling into GRT website scraping.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced GRT scraper."""
        self.error_manager = EFISErrorHandlingManager(config or get_default_config())
        self.logger = self.error_manager.logger
        
    def download_grt_updates(self) -> Dict[str, Any]:
        """Download GRT updates with error handling."""
        operation_id = self.logger.log_operation_start("download_grt_updates")
        start_time = time.time()
        
        try:
            # Check for updates with network resilience
            def check_updates():
                return self._check_grt_website()
            
            updates = self.error_manager.network_manager.execute_with_resilience(
                pool_name='macbook',  # Could be a different pool for GRT
                operation=check_updates,
                operation_id=f"{operation_id}_check",
                priority=OperationPriority.NORMAL,
                max_retries=2,
                timeout=60.0
            )
            
            # Download files with atomic operations
            downloaded_files = []
            for update in updates:
                download_result = self._download_file_with_error_handling(update)
                if download_result['success']:
                    downloaded_files.append(download_result['file_path'])
            
            duration = time.time() - start_time
            self.logger.log_operation_end("download_grt_updates", operation_id, True, duration)
            
            return {
                'success': True,
                'updates_found': len(updates),
                'files_downloaded': len(downloaded_files),
                'downloaded_files': downloaded_files,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_operation_end("download_grt_updates", operation_id, False, duration, error=str(e))
            
            return {
                'success': False,
                'error': str(e),
                'duration': duration
            }
    
    def _check_grt_website(self) -> list:
        """Check GRT website for updates."""
        # Simulate checking website
        self.logger.info("Checking GRT website for updates")
        
        # Return simulated updates
        return [
            {'name': 'NAV.DB', 'url': 'https://grt-avionics.com/nav.db', 'version': '2024-01'},
            {'name': 'HXr_Software.zip', 'url': 'https://grt-avionics.com/hxr.zip', 'version': '8.01'}
        ]
    
    def _download_file_with_error_handling(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Download file with comprehensive error handling."""
        file_name = update['name']
        target_path = Path("~/Downloads/GRT").expanduser() / file_name
        
        # Simulate download operation
        def download_operation():
            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Simulate file content
            content = b"Simulated GRT file content"
            
            # Write with atomic operation
            with self.error_manager.atomic_ops.atomic_write(target_path) as temp_path:
                temp_path.write_bytes(content)
        
        result = self.error_manager.file_handler.handle_file_operation(
            download_operation,
            f"download_{file_name}",
            target_path
        )
        
        if result.success:
            self.logger.info(f"Downloaded GRT file: {file_name}",
                           file_name=file_name,
                           target_path=str(target_path),
                           bytes_processed=result.bytes_processed)
            
            return {
                'success': True,
                'file_path': str(target_path),
                'bytes_downloaded': result.bytes_processed
            }
        else:
            self.logger.error(f"Failed to download GRT file: {file_name}",
                            file_name=file_name,
                            error_type=result.error_type.value if result.error_type else 'unknown',
                            error_message=result.error_message)
            
            return {
                'success': False,
                'error': result.error_message
            }


def demonstrate_error_handling():
    """Demonstrate the error handling system."""
    print("EFIS Data Manager - Error Handling Demonstration")
    print("=" * 50)
    
    # Create error handling manager
    config = get_default_config()
    config['logging']['console'] = True  # Enable console output for demo
    
    error_manager = EFISErrorHandlingManager(config)
    
    try:
        # Demonstrate USB processing
        print("\n1. USB Drive Processing with Error Handling:")
        usb_processor = EnhancedUSBDriveProcessor(config)
        # Note: This would fail in demo since drive doesn't exist
        # result = usb_processor.process_efis_files("/Volumes/EFIS_DRIVE")
        print("   USB processor initialized with comprehensive error handling")
        
        # Demonstrate sync with network resilience
        print("\n2. Chart Sync with Network Resilience:")
        sync_engine = EnhancedSyncEngine(config)
        # Note: This would be queued since network isn't available
        # result = sync_engine.sync_charts_with_resilience()
        print("   Sync engine initialized with network resilience")
        
        # Demonstrate GRT scraping
        print("\n3. GRT Scraping with Error Handling:")
        grt_scraper = EnhancedGRTScraper(config)
        result = grt_scraper.download_grt_updates()
        print(f"   GRT scraper result: {result}")
        
        # Show system status
        print("\n4. System Status:")
        status = error_manager.get_comprehensive_status()
        print(f"   Network online: {status['network_status']['is_online']}")
        print(f"   Health checks: {len(status['health_report']['individual_checks'])}")
        print(f"   Performance metrics: {len(status['performance_metrics'])}")
        
    finally:
        # Cleanup
        error_manager.shutdown()
        print("\nError handling system shutdown complete.")


if __name__ == "__main__":
    demonstrate_error_handling()