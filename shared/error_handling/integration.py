"""
Integration utilities for error handling components.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .file_system_errors import FileSystemErrorHandler, AtomicFileOperation, DiskSpaceMonitor, PermissionChecker
from .network_resilience import NetworkResilienceManager, ConnectionInfo, OperationPriority
from .monitoring import StructuredLogger, PerformanceMonitor, HealthChecker


class EFISErrorHandlingManager:
    """
    Central manager for all error handling components.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize error handling manager."""
        self.config = config or {}
        
        # Initialize structured logger first
        logger_config = self.config.get('logging', {})
        self.logger = StructuredLogger('efis-error-handler', logger_config)
        
        # Initialize components
        self.file_handler = FileSystemErrorHandler(self.logger.logger)
        self.atomic_ops = AtomicFileOperation(self.file_handler)
        self.disk_monitor = DiskSpaceMonitor(self.logger.logger)
        self.permission_checker = PermissionChecker(self.logger.logger)
        self.network_manager = NetworkResilienceManager(self.logger.logger)
        self.performance_monitor = PerformanceMonitor(self.logger)
        self.health_checker = HealthChecker(self.logger)
        
        # Setup monitoring paths
        self._setup_disk_monitoring()
        
        # Setup network connections
        self._setup_network_connections()
        
        # Setup cleanup handlers
        self._setup_cleanup_handlers()
        
        # Setup custom health checks
        self._setup_health_checks()
        
        # Start monitoring
        self._start_monitoring()
        
        self.logger.info("EFIS Error Handling Manager initialized")
    
    def _setup_disk_monitoring(self) -> None:
        """Setup disk space monitoring for critical paths."""
        monitoring_paths = self.config.get('disk_monitoring', {}).get('paths', [])
        
        # Add default paths based on platform
        import sys
        if sys.platform.startswith('win'):
            monitoring_paths.extend(['C:\\', 'E:\\'])
        else:
            monitoring_paths.extend(['/', '/tmp'])
        
        for path in monitoring_paths:
            if Path(path).exists():
                self.disk_monitor.add_path(path)
    
    def _setup_network_connections(self) -> None:
        """Setup network connection pools."""
        network_config = self.config.get('network', {})
        
        # Setup MacBook connection for Windows system
        macbook_config = network_config.get('macbook', {})
        if macbook_config:
            connection_info = ConnectionInfo(
                host=macbook_config.get('host', '192.168.1.100'),
                port=macbook_config.get('port', 8080),
                protocol=macbook_config.get('protocol', 'http'),
                timeout=macbook_config.get('timeout', 30.0),
                max_connections=macbook_config.get('max_connections', 5)
            )
            self.network_manager.add_connection_pool('macbook', connection_info)
    
    def _setup_cleanup_handlers(self) -> None:
        """Setup disk cleanup handlers."""
        def cleanup_temp_files(path: str) -> int:
            """Cleanup temporary files."""
            temp_patterns = ['*.tmp', '*.temp', '*.bak']
            bytes_freed = 0
            
            try:
                path_obj = Path(path)
                for pattern in temp_patterns:
                    for temp_file in path_obj.rglob(pattern):
                        if temp_file.is_file():
                            size = temp_file.stat().st_size
                            temp_file.unlink()
                            bytes_freed += size
            except Exception as e:
                self.logger.warning(f"Cleanup handler error: {e}")
            
            return bytes_freed
        
        def cleanup_old_logs(path: str) -> int:
            """Cleanup old log files."""
            bytes_freed = 0
            
            try:
                path_obj = Path(path)
                log_dir = path_obj / 'logs'
                
                if log_dir.exists():
                    from datetime import datetime, timedelta
                    cutoff_date = datetime.now() - timedelta(days=30)
                    
                    for log_file in log_dir.rglob('*.log*'):
                        if log_file.is_file():
                            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                            if mtime < cutoff_date:
                                size = log_file.stat().st_size
                                log_file.unlink()
                                bytes_freed += size
            except Exception as e:
                self.logger.warning(f"Log cleanup error: {e}")
            
            return bytes_freed
        
        self.disk_monitor.add_cleanup_handler(cleanup_temp_files)
        self.disk_monitor.add_cleanup_handler(cleanup_old_logs)
    
    def _setup_health_checks(self) -> None:
        """Setup custom health checks."""
        def check_file_permissions() -> 'HealthCheckResult':
            """Check critical file permissions."""
            from .monitoring import HealthCheckResult, HealthStatus
            
            critical_paths = self.config.get('health_checks', {}).get('critical_paths', [])
            permission_issues = []
            
            for path_config in critical_paths:
                path = path_config.get('path')
                required_perms = path_config.get('permissions', ['read'])
                
                if path:
                    has_perms, missing = self.permission_checker.check_permissions(path, required_perms)
                    if not has_perms:
                        permission_issues.append(f"{path}: missing {', '.join(missing)}")
            
            if permission_issues:
                return HealthCheckResult(
                    name="file_permissions",
                    status=HealthStatus.CRITICAL,
                    message=f"Permission issues detected: {len(permission_issues)} paths",
                    details={'issues': permission_issues}
                )
            else:
                return HealthCheckResult(
                    name="file_permissions",
                    status=HealthStatus.HEALTHY,
                    message="All critical paths have required permissions"
                )
        
        def check_network_connectivity() -> 'HealthCheckResult':
            """Check network connectivity status."""
            from .monitoring import HealthCheckResult, HealthStatus
            
            status = self.network_manager.get_status()
            
            if not status['is_online']:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.CRITICAL,
                    message="System is offline",
                    details=status
                )
            
            unhealthy_pools = [
                name for name, pool_info in status['connection_pools'].items()
                if not pool_info['is_healthy']
            ]
            
            if unhealthy_pools:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.WARNING,
                    message=f"Unhealthy connection pools: {', '.join(unhealthy_pools)}",
                    details=status
                )
            else:
                return HealthCheckResult(
                    name="network_connectivity",
                    status=HealthStatus.HEALTHY,
                    message="All network connections healthy",
                    details=status
                )
        
        self.health_checker.add_health_check('file_permissions', check_file_permissions)
        self.health_checker.add_health_check('network_connectivity', check_network_connectivity)
    
    def _start_monitoring(self) -> None:
        """Start background monitoring."""
        monitoring_config = self.config.get('monitoring', {})
        
        # Start performance monitoring
        perf_interval = monitoring_config.get('performance_interval', 60)
        self.performance_monitor.start_collection(perf_interval)
        
        # Start health monitoring
        health_interval = monitoring_config.get('health_interval', 300)
        self.health_checker.start_monitoring(health_interval)
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'timestamp': self.logger.logger.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None)),
            'disk_space': self.disk_monitor.check_all_paths(),
            'network_status': self.network_manager.get_status(),
            'performance_metrics': self.performance_monitor.get_metrics_summary(),
            'health_report': self.health_checker.get_health_report()
        }
    
    def shutdown(self) -> None:
        """Shutdown error handling manager."""
        self.logger.info("Shutting down EFIS Error Handling Manager")
        
        try:
            self.performance_monitor.stop_collection()
            self.health_checker.stop_monitoring()
            self.network_manager.stop_background_processing()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def create_error_handler(config: Optional[Dict[str, Any]] = None) -> EFISErrorHandlingManager:
    """
    Factory function to create configured error handling manager.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured EFISErrorHandlingManager instance
    """
    return EFISErrorHandlingManager(config)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for error handling."""
    import sys
    
    config = {
        'logging': {
            'level': 'INFO',
            'file': '~/logs/efis-error-handler.log',
            'max_size': '50MB',
            'backup_count': 10,
            'console': False,
            'include_system_info': True
        },
        'disk_monitoring': {
            'paths': [],
            'warning_threshold': 0.85,
            'critical_threshold': 0.95
        },
        'network': {
            'macbook': {
                'host': '192.168.1.100',
                'port': 8080,
                'protocol': 'http',
                'timeout': 30.0,
                'max_connections': 5
            }
        },
        'monitoring': {
            'performance_interval': 60,
            'health_interval': 300
        },
        'health_checks': {
            'critical_paths': []
        }
    }
    
    # Platform-specific defaults
    if sys.platform.startswith('win'):
        config['disk_monitoring']['paths'] = ['C:\\', 'E:\\']
        config['health_checks']['critical_paths'] = [
            {'path': 'C:\\Scripts', 'permissions': ['read', 'write']},
            {'path': 'E:\\', 'permissions': ['read', 'write']}
        ]
    else:
        config['disk_monitoring']['paths'] = ['/', '/tmp']
        config['health_checks']['critical_paths'] = [
            {'path': '/var/log', 'permissions': ['read', 'write']},
            {'path': '/tmp', 'permissions': ['read', 'write']}
        ]
    
    return config