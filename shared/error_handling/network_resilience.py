"""
Network resilience and recovery for EFIS Data Manager.
"""

import time
import queue
import threading
import logging
import socket
import requests
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, Future


class NetworkErrorType(Enum):
    """Types of network errors."""
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_RESOLUTION = "dns_resolution"
    NETWORK_UNREACHABLE = "network_unreachable"
    SSL_ERROR = "ssl_error"
    HTTP_ERROR = "http_error"
    UNKNOWN = "unknown"


class OperationPriority(Enum):
    """Priority levels for queued operations."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class NetworkOperation:
    """Represents a network operation that can be queued."""
    id: str
    operation: Callable[[], Any]
    priority: OperationPriority
    max_retries: int
    timeout: float
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ConnectionInfo:
    """Information about a network connection."""
    host: str
    port: int
    protocol: str = "http"
    timeout: float = 30.0
    max_connections: int = 10
    keep_alive: bool = True


class RetryManager:
    """
    Manages retry logic with exponential backoff and jitter.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize retry manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_factor = 2.0
        self.jitter_factor = 0.1
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        import random
        
        # Exponential backoff
        delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        
        # Add jitter to prevent thundering herd
        jitter = delay * self.jitter_factor * random.random()
        
        return delay + jitter
    
    def should_retry(self, error_type: NetworkErrorType, attempt: int, max_retries: int) -> bool:
        """Determine if operation should be retried."""
        if attempt >= max_retries:
            return False
        
        # Don't retry certain error types
        non_retryable = {
            NetworkErrorType.DNS_RESOLUTION,
            NetworkErrorType.SSL_ERROR
        }
        
        return error_type not in non_retryable


class ConnectionPool:
    """
    Connection pool with timeout management and health checking.
    """
    
    def __init__(self, connection_info: ConnectionInfo, logger: Optional[logging.Logger] = None):
        """Initialize connection pool."""
        self.connection_info = connection_info
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = connection_info.timeout
        
        # Configure session
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=connection_info.max_connections,
            pool_maxsize=connection_info.max_connections,
            max_retries=0  # We handle retries ourselves
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Connection health tracking
        self.last_successful_connection = None
        self.consecutive_failures = 0
        self.is_healthy = True
        self._health_check_lock = threading.Lock()
    
    def execute_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute HTTP request with connection management."""
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Update health status on success
            with self._health_check_lock:
                self.last_successful_connection = datetime.now()
                self.consecutive_failures = 0
                self.is_healthy = True
            
            return response
            
        except Exception as e:
            # Update health status on failure
            with self._health_check_lock:
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    self.is_healthy = False
            
            raise e
    
    def check_health(self) -> bool:
        """Check connection health."""
        try:
            # Simple health check request
            base_url = f"{self.connection_info.protocol}://{self.connection_info.host}:{self.connection_info.port}"
            response = self.session.get(f"{base_url}/health", timeout=5)
            
            with self._health_check_lock:
                self.is_healthy = response.status_code == 200
                if self.is_healthy:
                    self.consecutive_failures = 0
                    self.last_successful_connection = datetime.now()
            
            return self.is_healthy
            
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            with self._health_check_lock:
                self.consecutive_failures += 1
                self.is_healthy = False
            return False
    
    def close(self):
        """Close connection pool."""
        self.session.close()


class OperationQueue:
    """
    Queue for network operations during offline periods.
    """
    
    def __init__(self, max_size: int = 1000, logger: Optional[logging.Logger] = None):
        """Initialize operation queue."""
        self.max_size = max_size
        self.logger = logger or logging.getLogger(__name__)
        self._queue = queue.PriorityQueue(maxsize=max_size)
        self._operations: Dict[str, NetworkOperation] = {}
        self._lock = threading.Lock()
        
    def enqueue(self, operation: NetworkOperation) -> bool:
        """
        Add operation to queue.
        
        Args:
            operation: NetworkOperation to queue
            
        Returns:
            True if operation was queued, False if queue is full
        """
        try:
            # Use negative priority for correct ordering (higher priority first)
            priority_value = -operation.priority.value
            self._queue.put((priority_value, operation.created_at, operation.id), block=False)
            
            with self._lock:
                self._operations[operation.id] = operation
            
            self.logger.debug(f"Queued operation {operation.id} with priority {operation.priority.name}")
            return True
            
        except queue.Full:
            self.logger.warning(f"Operation queue full, dropping operation {operation.id}")
            return False
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[NetworkOperation]:
        """
        Get next operation from queue.
        
        Args:
            timeout: Maximum time to wait for operation
            
        Returns:
            NetworkOperation or None if timeout
        """
        try:
            priority_value, created_at, operation_id = self._queue.get(timeout=timeout)
            
            with self._lock:
                operation = self._operations.pop(operation_id, None)
            
            return operation
            
        except queue.Empty:
            return None
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
    
    def clear_expired(self, max_age: timedelta = timedelta(hours=24)) -> int:
        """
        Clear expired operations from queue.
        
        Args:
            max_age: Maximum age for operations
            
        Returns:
            Number of operations cleared
        """
        cleared_count = 0
        cutoff_time = datetime.now() - max_age
        
        # Create new queue without expired operations
        new_queue = queue.PriorityQueue(maxsize=self.max_size)
        
        with self._lock:
            while not self._queue.empty():
                try:
                    priority_value, created_at, operation_id = self._queue.get_nowait()
                    
                    if created_at > cutoff_time and operation_id in self._operations:
                        # Keep non-expired operation
                        new_queue.put((priority_value, created_at, operation_id))
                    else:
                        # Remove expired operation
                        self._operations.pop(operation_id, None)
                        cleared_count += 1
                        
                except queue.Empty:
                    break
            
            self._queue = new_queue
        
        if cleared_count > 0:
            self.logger.info(f"Cleared {cleared_count} expired operations from queue")
        
        return cleared_count


class NetworkResilienceManager:
    """
    Main network resilience manager with connection pooling and operation queuing.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize network resilience manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.operation_queue = OperationQueue(logger=logger)
        self.retry_manager = RetryManager(logger)
        
        # State management
        self.is_online = True
        self.last_connectivity_check = None
        self.connectivity_check_interval = timedelta(minutes=1)
        
        # Background processing
        self._processing_thread = None
        self._stop_processing = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="network-resilience")
        
        self.start_background_processing()
    
    def add_connection_pool(self, name: str, connection_info: ConnectionInfo) -> None:
        """Add a connection pool."""
        self.connection_pools[name] = ConnectionPool(connection_info, self.logger)
        self.logger.info(f"Added connection pool: {name}")
    
    def execute_with_resilience(
        self,
        pool_name: str,
        operation: Callable[[], Any],
        operation_id: str,
        priority: OperationPriority = OperationPriority.NORMAL,
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> Any:
        """
        Execute operation with network resilience.
        
        Args:
            pool_name: Name of connection pool to use
            operation: Operation to execute
            operation_id: Unique operation identifier
            priority: Operation priority
            max_retries: Maximum retry attempts
            timeout: Operation timeout
            
        Returns:
            Operation result
            
        Raises:
            Exception if operation fails after all retries
        """
        if not self.is_online:
            # Queue operation for later execution
            network_op = NetworkOperation(
                id=operation_id,
                operation=operation,
                priority=priority,
                max_retries=max_retries,
                timeout=timeout
            )
            
            if self.operation_queue.enqueue(network_op):
                self.logger.info(f"Queued operation {operation_id} for offline execution")
                raise ConnectionError("System is offline, operation queued for later execution")
            else:
                raise ConnectionError("System is offline and operation queue is full")
        
        # Execute operation with retry logic
        return self._execute_with_retry(pool_name, operation, operation_id, max_retries, timeout)
    
    def _execute_with_retry(
        self,
        pool_name: str,
        operation: Callable[[], Any],
        operation_id: str,
        max_retries: int,
        timeout: float
    ) -> Any:
        """Execute operation with retry logic."""
        pool = self.connection_pools.get(pool_name)
        if not pool:
            raise ValueError(f"Connection pool not found: {pool_name}")
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"Executing operation {operation_id} (attempt {attempt + 1})")
                
                # Check pool health
                if not pool.is_healthy and not pool.check_health():
                    raise ConnectionError("Connection pool is unhealthy")
                
                # Execute operation
                result = operation()
                
                self.logger.debug(f"Operation {operation_id} completed successfully")
                return result
                
            except Exception as e:
                last_error = e
                error_type = self._classify_network_error(e)
                
                self.logger.warning(
                    f"Operation {operation_id} failed (attempt {attempt + 1}): {e}",
                    extra={
                        'operation_id': operation_id,
                        'attempt': attempt + 1,
                        'error_type': error_type.value
                    }
                )
                
                # Check if we should retry
                if attempt < max_retries and self.retry_manager.should_retry(error_type, attempt, max_retries):
                    delay = self.retry_manager.calculate_delay(attempt)
                    self.logger.debug(f"Retrying operation {operation_id} in {delay:.1f}s")
                    time.sleep(delay)
                    
                    # Check connectivity after network errors
                    if error_type in [NetworkErrorType.NETWORK_UNREACHABLE, NetworkErrorType.CONNECTION_TIMEOUT]:
                        self._check_connectivity()
                else:
                    break
        
        # All retries failed
        self.logger.error(f"Operation {operation_id} failed after {max_retries + 1} attempts: {last_error}")
        raise last_error
    
    def _classify_network_error(self, error: Exception) -> NetworkErrorType:
        """Classify network error type."""
        error_str = str(error).lower()
        
        if isinstance(error, socket.timeout) or 'timeout' in error_str:
            return NetworkErrorType.CONNECTION_TIMEOUT
        elif isinstance(error, ConnectionRefusedError) or 'connection refused' in error_str:
            return NetworkErrorType.CONNECTION_REFUSED
        elif 'name resolution' in error_str or 'dns' in error_str:
            return NetworkErrorType.DNS_RESOLUTION
        elif 'network unreachable' in error_str or 'no route to host' in error_str:
            return NetworkErrorType.NETWORK_UNREACHABLE
        elif 'ssl' in error_str or 'certificate' in error_str:
            return NetworkErrorType.SSL_ERROR
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            return NetworkErrorType.HTTP_ERROR
        else:
            return NetworkErrorType.UNKNOWN
    
    def _check_connectivity(self) -> bool:
        """Check network connectivity."""
        try:
            # Simple connectivity check
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            
            if not self.is_online:
                self.logger.info("Network connectivity restored")
                self.is_online = True
            
            self.last_connectivity_check = datetime.now()
            return True
            
        except Exception as e:
            if self.is_online:
                self.logger.warning(f"Network connectivity lost: {e}")
                self.is_online = False
            
            self.last_connectivity_check = datetime.now()
            return False
    
    def start_background_processing(self) -> None:
        """Start background processing thread."""
        if self._processing_thread and self._processing_thread.is_alive():
            return
        
        self._stop_processing.clear()
        self._processing_thread = threading.Thread(
            target=self._background_processor,
            name="network-resilience-processor",
            daemon=True
        )
        self._processing_thread.start()
        self.logger.info("Started network resilience background processing")
    
    def stop_background_processing(self) -> None:
        """Stop background processing."""
        self._stop_processing.set()
        if self._processing_thread:
            self._processing_thread.join(timeout=5)
        self._executor.shutdown(wait=True)
        self.logger.info("Stopped network resilience background processing")
    
    def _background_processor(self) -> None:
        """Background processor for queued operations and health checks."""
        while not self._stop_processing.is_set():
            try:
                # Check connectivity periodically
                if (not self.last_connectivity_check or 
                    datetime.now() - self.last_connectivity_check > self.connectivity_check_interval):
                    self._check_connectivity()
                
                # Process queued operations if online
                if self.is_online:
                    self._process_queued_operations()
                
                # Clean up expired operations
                self.operation_queue.clear_expired()
                
                # Health check connection pools
                for pool in self.connection_pools.values():
                    if not pool.is_healthy:
                        pool.check_health()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in background processor: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _process_queued_operations(self) -> None:
        """Process queued operations."""
        processed_count = 0
        max_batch_size = 10
        
        while processed_count < max_batch_size:
            operation = self.operation_queue.dequeue(timeout=1.0)
            if not operation:
                break
            
            try:
                # Submit operation to thread pool
                future = self._executor.submit(self._execute_queued_operation, operation)
                processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to submit queued operation {operation.id}: {e}")
        
        if processed_count > 0:
            self.logger.debug(f"Submitted {processed_count} queued operations for processing")
    
    def _execute_queued_operation(self, operation: NetworkOperation) -> None:
        """Execute a queued operation."""
        try:
            self.logger.info(f"Executing queued operation {operation.id}")
            result = operation.operation()
            self.logger.info(f"Queued operation {operation.id} completed successfully")
            
        except Exception as e:
            operation.retry_count += 1
            operation.last_error = str(e)
            
            self.logger.warning(f"Queued operation {operation.id} failed: {e}")
            
            # Re-queue if retries remaining
            if operation.retry_count < operation.max_retries:
                self.operation_queue.enqueue(operation)
                self.logger.debug(f"Re-queued operation {operation.id} for retry")
            else:
                self.logger.error(f"Queued operation {operation.id} failed after {operation.max_retries} retries")
    
    def get_status(self) -> Dict[str, Any]:
        """Get network resilience status."""
        return {
            'is_online': self.is_online,
            'last_connectivity_check': self.last_connectivity_check.isoformat() if self.last_connectivity_check else None,
            'queued_operations': self.operation_queue.get_queue_size(),
            'connection_pools': {
                name: {
                    'is_healthy': pool.is_healthy,
                    'consecutive_failures': pool.consecutive_failures,
                    'last_successful_connection': pool.last_successful_connection.isoformat() if pool.last_successful_connection else None
                }
                for name, pool in self.connection_pools.items()
            }
        }
    
    def __del__(self):
        """Cleanup on destruction."""
        self.stop_background_processing()
        for pool in self.connection_pools.values():
            pool.close()