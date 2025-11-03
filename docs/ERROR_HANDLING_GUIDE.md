# EFIS Data Manager - Error Handling Guide

## Overview

The EFIS Data Manager now includes comprehensive error handling and recovery capabilities designed to make the system more robust and reliable. This guide explains how to use the new error handling components.

## Components

### 1. File System Error Handling (`shared/error_handling/file_system_errors.py`)

**Features:**
- File locking detection and retry mechanisms
- Disk space monitoring and cleanup procedures
- Atomic file operations with rollback capability
- Permission error detection and user guidance

**Key Classes:**
- `FileSystemErrorHandler`: Main error handler with retry logic
- `AtomicFileOperation`: Provides atomic file operations
- `DiskSpaceMonitor`: Monitors disk space and triggers cleanup
- `PermissionChecker`: Checks and provides guidance for permission issues

### 2. Network Resilience (`shared/error_handling/network_resilience.py`)

**Features:**
- Connection pooling with timeout management
- Operation queuing for offline periods
- Graceful degradation during network issues
- Automatic recovery when connectivity returns

**Key Classes:**
- `NetworkResilienceManager`: Main network resilience coordinator
- `ConnectionPool`: Manages HTTP connections with health checking
- `OperationQueue`: Queues operations during offline periods
- `RetryManager`: Handles retry logic with exponential backoff

### 3. Comprehensive Monitoring (`shared/error_handling/monitoring.py`)

**Features:**
- Structured logging with JSON format
- Log rotation and archival system
- Performance metrics collection and reporting
- Health check endpoints for monitoring

**Key Classes:**
- `StructuredLogger`: Enhanced JSON logger with rotation
- `PerformanceMonitor`: Collects system and application metrics
- `HealthChecker`: Implements health checks and monitoring

### 4. Integration Manager (`shared/error_handling/integration.py`)

**Features:**
- Central coordinator for all error handling components
- Default configuration management
- Background monitoring and cleanup
- Comprehensive status reporting

**Key Classes:**
- `EFISErrorHandlingManager`: Main integration manager

## Quick Start

### Basic Usage

```python
from shared.error_handling.integration import create_error_handler, get_default_config

# Create error handler with default config
config = get_default_config()
error_manager = create_error_handler(config)

# Use structured logging
error_manager.logger.info("Operation started", operation="sync_charts")

# Use atomic file operations
result = error_manager.atomic_ops.atomic_copy(src_path, dst_path, verify=True)
if result.success:
    print("File copied successfully")
else:
    print(f"Copy failed: {result.error_message}")

# Check system health
health_report = error_manager.health_checker.get_health_report()
print(f"System status: {health_report['overall_status']}")

# Shutdown when done
error_manager.shutdown()
```

### Network Operations with Resilience

```python
# Execute network operation with automatic retry and queuing
def sync_operation():
    # Your sync logic here
    return {"files_synced": 150}

try:
    result = error_manager.network_manager.execute_with_resilience(
        pool_name='macbook',
        operation=sync_operation,
        operation_id='chart_sync_001',
        priority=OperationPriority.HIGH,
        max_retries=3,
        timeout=300.0
    )
    print(f"Sync completed: {result}")
except ConnectionError as e:
    if "queued for later execution" in str(e):
        print("System offline - operation queued for when connectivity returns")
    else:
        print(f"Sync failed: {e}")
```

### File Operations with Error Handling

```python
# Safe file operations with comprehensive error handling
def process_files():
    files_to_process = ["demo1.log", "demo2.log"]
    
    for file_name in files_to_process:
        src_path = Path(f"/source/{file_name}")
        dst_path = Path(f"/destination/{file_name}")
        
        # Use error handler for robust file operations
        def move_operation():
            return src_path.rename(dst_path)
        
        result = error_manager.file_handler.handle_file_operation(
            move_operation,
            "move_demo_file",
            src_path
        )
        
        if result.success:
            error_manager.logger.info(f"Moved file: {file_name}",
                                    duration=result.duration,
                                    bytes_processed=result.bytes_processed)
        else:
            error_manager.logger.error(f"Failed to move file: {file_name}",
                                     error_type=result.error_type.value,
                                     error_message=result.error_message,
                                     retry_count=result.retry_count)
```

## Configuration

### Default Configuration Structure

```python
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
        'paths': ['/path/to/monitor'],
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
    }
}
```

### Platform-Specific Defaults

The system automatically configures platform-specific defaults:

**Windows:**
- Monitors C:\ and E:\ drives
- Checks permissions for C:\Scripts and E:\

**macOS:**
- Monitors / and /tmp
- Checks permissions for /var/log and /tmp

## Integration Examples

See `shared/error_handling/examples.py` for complete examples of integrating error handling into:

1. **USB Drive Processing** - Enhanced with atomic operations and permission checking
2. **Chart Synchronization** - Enhanced with network resilience and queuing
3. **GRT Website Scraping** - Enhanced with retry logic and file integrity

## Monitoring and Health Checks

### Built-in Health Checks

1. **System Resources** - CPU and memory usage
2. **Disk Space** - Available disk space on monitored paths
3. **Process Health** - Current process resource usage
4. **File Permissions** - Critical path permissions
5. **Network Connectivity** - Connection pool health

### Performance Metrics

The system automatically collects:
- CPU and memory usage
- Disk usage
- Process statistics
- Operation timing and throughput
- Error counts by type

### Accessing Status Information

```python
# Get comprehensive system status
status = error_manager.get_comprehensive_status()

# Get specific health report
health_report = error_manager.health_checker.get_health_report()

# Get performance metrics summary
metrics = error_manager.performance_monitor.get_metrics_summary(hours=1)

# Get network status
network_status = error_manager.network_manager.get_status()
```

## Dependencies

Install additional dependencies for error handling:

```bash
pip install -r requirements-error-handling.txt
```

Required packages:
- `psutil>=5.9.0` - System and process monitoring
- `requests>=2.28.0` - HTTP requests (already in main requirements)

## Best Practices

1. **Always use the error manager** for file operations in production code
2. **Configure appropriate retry limits** based on operation criticality
3. **Monitor disk space** on all critical paths
4. **Use structured logging** with meaningful context
5. **Implement custom health checks** for application-specific monitoring
6. **Handle queued operations** gracefully when system comes back online
7. **Review error logs regularly** to identify patterns and improve reliability

## Troubleshooting

### Common Issues

1. **Permission Errors**: Use `PermissionChecker.get_permission_guidance()` for user-friendly error messages
2. **Network Timeouts**: Operations are automatically queued and retried when connectivity returns
3. **Disk Full**: Automatic cleanup handlers free space when thresholds are exceeded
4. **File Locks**: Retry logic with exponential backoff handles temporary file locks

### Debugging

Enable console logging for debugging:

```python
config['logging']['console'] = True
error_manager = create_error_handler(config)
```

Check system status:

```python
status = error_manager.get_comprehensive_status()
print(json.dumps(status, indent=2, default=str))
```

## Migration Guide

To integrate error handling into existing code:

1. **Replace direct file operations** with `AtomicFileOperation` methods
2. **Wrap network operations** with `NetworkResilienceManager.execute_with_resilience()`
3. **Replace standard logging** with `StructuredLogger`
4. **Add health checks** for critical system components
5. **Configure monitoring paths** for disk space monitoring

The error handling system is designed to be backward compatible and can be gradually integrated into existing code.