"""
Comprehensive logging and monitoring for EFIS Data Manager.
"""

import json
import time
import logging
import logging.handlers
import threading
import psutil
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque


class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatus(Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }


class JSONStructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with enhanced metadata.
    """
    
    def __init__(self, include_system_info: bool = True):
        """Initialize JSON formatter."""
        super().__init__()
        self.include_system_info = include_system_info
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        self.process_id = os.getpid()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName
        }
        
        # Add system information if enabled
        if self.include_system_info:
            log_entry.update({
                'hostname': self.hostname,
                'process_id': self.process_id
            })
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                'relativeCreated', 'thread', 'threadName', 'processName',
                'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, separators=(',', ':'))


class StructuredLogger:
    """
    Enhanced structured logger with JSON format and log rotation.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            config: Logger configuration
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(name)
        self._setup_logger()
        
        # Performance tracking
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
    def _setup_logger(self) -> None:
        """Set up logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        level = self.config.get('level', 'INFO')
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create JSON formatter
        json_formatter = JSONStructuredFormatter(
            include_system_info=self.config.get('include_system_info', True)
        )
        
        # File handler with rotation
        log_file = self.config.get('file', 'efis-data-manager.log')
        if log_file.startswith('~'):
            log_file = os.path.expanduser(log_file)
        
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure rotation
        max_bytes = self._parse_size(self.config.get('max_size', '50MB'))
        backup_count = self.config.get('backup_count', 10)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for development
        if self.config.get('console', False):
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Log message with structured data."""
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message, **kwargs)
        
        # Track error counts
        error_type = kwargs.get('error_type', 'unknown')
        self.error_counts[error_type] += 1
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.log(LogLevel.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self.logger.exception(message, extra=kwargs)
    
    def log_operation_start(self, operation: str, **kwargs) -> str:
        """Log operation start and return operation ID."""
        operation_id = f"{operation}_{int(time.time() * 1000)}"
        self.info(f"Operation started: {operation}",
                 operation=operation,
                 operation_id=operation_id,
                 status='started',
                 **kwargs)
        return operation_id
    
    def log_operation_end(self, operation: str, operation_id: str, 
                         success: bool, duration: float, **kwargs) -> None:
        """Log operation completion."""
        status = 'success' if success else 'failed'
        
        self.info(f"Operation completed: {operation}",
                 operation=operation,
                 operation_id=operation_id,
                 status=status,
                 duration=duration,
                 **kwargs)
        
        # Track operation performance
        self.operation_times[operation].append(duration)
        
        # Keep only recent measurements
        if len(self.operation_times[operation]) > 100:
            self.operation_times[operation] = self.operation_times[operation][-100:]


class PerformanceMonitor:
    """
    Collects and reports performance metrics.
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        """Initialize performance monitor."""
        self.logger = logger
        self.metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.metric_collectors: Dict[str, Callable[[], float]] = {}
        self._collection_thread = None
        self._stop_collection = threading.Event()
        
        # Register default system metrics
        self._register_system_metrics()
    
    def _register_system_metrics(self) -> None:
        """Register default system performance metrics."""
        self.metric_collectors.update({
            'cpu_percent': lambda: psutil.cpu_percent(interval=None),
            'memory_percent': lambda: psutil.virtual_memory().percent,
            'disk_usage_percent': lambda: psutil.disk_usage('/').percent if os.path.exists('/') else 0,
            'process_memory_mb': lambda: psutil.Process().memory_info().rss / 1024 / 1024,
            'process_cpu_percent': lambda: psutil.Process().cpu_percent(),
            'open_files': lambda: len(psutil.Process().open_files()),
            'thread_count': lambda: psutil.Process().num_threads()
        })
    
    def add_metric_collector(self, name: str, collector: Callable[[], float]) -> None:
        """Add custom metric collector."""
        self.metric_collectors[name] = collector
        if self.logger:
            self.logger.debug(f"Added metric collector: {name}")
    
    def record_metric(self, name: str, value: float, unit: str = "", 
                     tags: Optional[Dict[str, str]] = None) -> None:
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        if self.logger:
            self.logger.debug(f"Recorded metric: {name}={value}{unit}",
                            metric_name=name,
                            metric_value=value,
                            metric_unit=unit,
                            metric_tags=tags)
    
    def record_operation_time(self, operation: str, duration: float) -> None:
        """Record operation execution time."""
        self.record_metric(f"{operation}_duration", duration, "seconds",
                          tags={'operation': operation})
    
    def record_throughput(self, operation: str, count: int, duration: float) -> None:
        """Record operation throughput."""
        throughput = count / duration if duration > 0 else 0
        self.record_metric(f"{operation}_throughput", throughput, "ops/sec",
                          tags={'operation': operation})
    
    def collect_system_metrics(self) -> None:
        """Collect all registered system metrics."""
        for name, collector in self.metric_collectors.items():
            try:
                value = collector()
                self.record_metric(name, value)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to collect metric {name}: {e}")
    
    def start_collection(self, interval: float = 60.0) -> None:
        """Start automatic metric collection."""
        if self._collection_thread and self._collection_thread.is_alive():
            return
        
        self._stop_collection.clear()
        self._collection_thread = threading.Thread(
            target=self._collection_worker,
            args=(interval,),
            name="performance-monitor",
            daemon=True
        )
        self._collection_thread.start()
        
        if self.logger:
            self.logger.info(f"Started performance monitoring (interval: {interval}s)")
    
    def stop_collection(self) -> None:
        """Stop automatic metric collection."""
        self._stop_collection.set()
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("Stopped performance monitoring")
    
    def _collection_worker(self, interval: float) -> None:
        """Background worker for metric collection."""
        while not self._stop_collection.is_set():
            try:
                self.collect_system_metrics()
                self._stop_collection.wait(interval)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in metric collection: {e}")
                self._stop_collection.wait(min(interval, 60))
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of metrics for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Group metrics by name
        grouped_metrics = defaultdict(list)
        for metric in recent_metrics:
            grouped_metrics[metric.name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for name, values in grouped_metrics.items():
            if values:
                summary[name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1]
                }
        
        return summary
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        if format == 'json':
            return json.dumps([m.to_dict() for m in self.metrics], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


class HealthChecker:
    """
    Implements health check endpoints and monitoring.
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        """Initialize health checker."""
        self.logger = logger
        self.health_checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}
        self._check_thread = None
        self._stop_checking = threading.Event()
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self) -> None:
        """Register default health checks."""
        self.health_checks.update({
            'system_resources': self._check_system_resources,
            'disk_space': self._check_disk_space,
            'process_health': self._check_process_health
        })
    
    def add_health_check(self, name: str, check_func: Callable[[], HealthCheckResult]) -> None:
        """Add custom health check."""
        self.health_checks[name] = check_func
        if self.logger:
            self.logger.debug(f"Added health check: {name}")
    
    def run_health_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.health_checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check not found: {name}"
            )
        
        try:
            result = self.health_checks[name]()
            self.last_results[name] = result
            
            if self.logger:
                self.logger.debug(f"Health check completed: {name}",
                                health_check=name,
                                status=result.status.value,
                                message=result.message)
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {e}",
                details={'exception': str(e)}
            )
            
            self.last_results[name] = result
            
            if self.logger:
                self.logger.error(f"Health check error: {name}",
                                health_check=name,
                                error=str(e))
            
            return result
    
    def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        
        for name in self.health_checks:
            results[name] = self.run_health_check(name)
        
        return results
    
    def get_overall_health(self) -> HealthCheckResult:
        """Get overall system health status."""
        if not self.last_results:
            return HealthCheckResult(
                name="overall",
                status=HealthStatus.UNKNOWN,
                message="No health checks have been run"
            )
        
        # Determine overall status
        statuses = [result.status for result in self.last_results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
            message = "One or more critical health issues detected"
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
            message = "One or more warnings detected"
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
            message = "Some health checks have unknown status"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "All health checks passing"
        
        return HealthCheckResult(
            name="overall",
            status=overall_status,
            message=message,
            details={
                'check_count': len(self.last_results),
                'healthy_count': sum(1 for r in self.last_results.values() if r.status == HealthStatus.HEALTHY),
                'warning_count': sum(1 for r in self.last_results.values() if r.status == HealthStatus.WARNING),
                'critical_count': sum(1 for r in self.last_results.values() if r.status == HealthStatus.CRITICAL),
                'unknown_count': sum(1 for r in self.last_results.values() if r.status == HealthStatus.UNKNOWN)
            }
        )
    
    def start_monitoring(self, interval: float = 300.0) -> None:
        """Start automatic health monitoring."""
        if self._check_thread and self._check_thread.is_alive():
            return
        
        self._stop_checking.clear()
        self._check_thread = threading.Thread(
            target=self._monitoring_worker,
            args=(interval,),
            name="health-checker",
            daemon=True
        )
        self._check_thread.start()
        
        if self.logger:
            self.logger.info(f"Started health monitoring (interval: {interval}s)")
    
    def stop_monitoring(self) -> None:
        """Stop automatic health monitoring."""
        self._stop_checking.set()
        if self._check_thread:
            self._check_thread.join(timeout=5)
        
        if self.logger:
            self.logger.info("Stopped health monitoring")
    
    def _monitoring_worker(self, interval: float) -> None:
        """Background worker for health monitoring."""
        while not self._stop_checking.is_set():
            try:
                results = self.run_all_health_checks()
                
                # Log critical issues
                for name, result in results.items():
                    if result.status == HealthStatus.CRITICAL and self.logger:
                        self.logger.critical(f"Critical health issue: {name}",
                                           health_check=name,
                                           message=result.message,
                                           details=result.details)
                
                self._stop_checking.wait(interval)
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in health monitoring: {e}")
                self._stop_checking.wait(min(interval, 300))
    
    def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 90 or memory_percent > 90:
                return HealthCheckResult(
                    name="system_resources",
                    status=HealthStatus.CRITICAL,
                    message=f"High resource usage: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%",
                    details={'cpu_percent': cpu_percent, 'memory_percent': memory_percent}
                )
            elif cpu_percent > 70 or memory_percent > 70:
                return HealthCheckResult(
                    name="system_resources",
                    status=HealthStatus.WARNING,
                    message=f"Elevated resource usage: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%",
                    details={'cpu_percent': cpu_percent, 'memory_percent': memory_percent}
                )
            else:
                return HealthCheckResult(
                    name="system_resources",
                    status=HealthStatus.HEALTHY,
                    message=f"Resource usage normal: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%",
                    details={'cpu_percent': cpu_percent, 'memory_percent': memory_percent}
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check system resources: {e}"
            )
    
    def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space usage."""
        try:
            # Check root filesystem
            disk_usage = psutil.disk_usage('/')
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > 95:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.CRITICAL,
                    message=f"Critical disk space: {usage_percent:.1f}% used",
                    details={'usage_percent': usage_percent, 'free_gb': disk_usage.free / (1024**3)}
                )
            elif usage_percent > 85:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.WARNING,
                    message=f"Low disk space: {usage_percent:.1f}% used",
                    details={'usage_percent': usage_percent, 'free_gb': disk_usage.free / (1024**3)}
                )
            else:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk space OK: {usage_percent:.1f}% used",
                    details={'usage_percent': usage_percent, 'free_gb': disk_usage.free / (1024**3)}
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check disk space: {e}"
            )
    
    def _check_process_health(self) -> HealthCheckResult:
        """Check current process health."""
        try:
            process = psutil.Process()
            
            # Check memory usage
            memory_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent()
            
            details = {
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files())
            }
            
            if memory_mb > 1000:  # 1GB
                return HealthCheckResult(
                    name="process_health",
                    status=HealthStatus.WARNING,
                    message=f"High memory usage: {memory_mb:.1f}MB",
                    details=details
                )
            else:
                return HealthCheckResult(
                    name="process_health",
                    status=HealthStatus.HEALTHY,
                    message=f"Process health OK: {memory_mb:.1f}MB memory, {cpu_percent:.1f}% CPU",
                    details=details
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="process_health",
                status=HealthStatus.UNKNOWN,
                message=f"Could not check process health: {e}"
            )
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        overall_health = self.get_overall_health()
        
        return {
            'overall_status': overall_health.status.value,
            'overall_message': overall_health.message,
            'timestamp': datetime.now().isoformat(),
            'details': overall_health.details,
            'individual_checks': {
                name: result.to_dict() for name, result in self.last_results.items()
            }
        }