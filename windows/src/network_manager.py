"""
Network connectivity and discovery manager for EFIS Data Manager.
Handles MacBook discovery and network connectivity validation.
"""

import socket
import subprocess
import time
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class ConnectionStatus(Enum):
    """Network connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UNREACHABLE = "unreachable"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class NetworkInfo:
    """Network connection information."""
    hostname: str
    ip_address: str
    port: int
    status: ConnectionStatus
    response_time_ms: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None


class NetworkManager:
    """
    Manages network connectivity and MacBook discovery.
    
    Provides methods for discovering the MacBook on the local network,
    validating connectivity, and monitoring network changes.
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize network manager.
        
        Args:
            config: Configuration dictionary with network settings
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Network configuration
        self.macbook_hostname = config.get('macbookHostname', 'MacBookM2.local')
        self.macbook_ip = config.get('macbookIP', '192.168.1.100')
        self.http_port = config.get('httpPort', 8080)
        self.connection_timeout = config.get('connectionTimeout', 10)
        self.ping_timeout = config.get('pingTimeout', 5)
        
        # Connection state
        self.last_known_good_ip = None
        self.connection_history = []
        self.max_history_size = 100
        
        self.logger.info(f"Network manager initialized: {self.macbook_hostname} -> {self.macbook_ip}:{self.http_port}")
        
    def discover_macbook(self) -> Optional[NetworkInfo]:
        """
        Discover MacBook on the local network.
        
        Uses mDNS hostname first, then falls back to static IP.
        
        Returns:
            NetworkInfo object if MacBook is found, None otherwise
        """
        self.logger.debug("Starting MacBook discovery")
        
        # Try mDNS hostname first
        network_info = self._try_hostname_connection(self.macbook_hostname)
        if network_info and network_info.status == ConnectionStatus.CONNECTED:
            self.logger.info(f"MacBook discovered via mDNS: {network_info.ip_address}")
            self.last_known_good_ip = network_info.ip_address
            return network_info
            
        # Fallback to static IP
        network_info = self._try_ip_connection(self.macbook_ip)
        if network_info and network_info.status == ConnectionStatus.CONNECTED:
            self.logger.info(f"MacBook discovered via static IP: {network_info.ip_address}")
            self.last_known_good_ip = network_info.ip_address
            return network_info
            
        self.logger.warning("MacBook discovery failed - no reachable endpoints found")
        return None
        
    def check_connectivity(self, target_ip: Optional[str] = None) -> NetworkInfo:
        """
        Check connectivity to MacBook.
        
        Args:
            target_ip: Specific IP to check, or None to use discovery
            
        Returns:
            NetworkInfo with connection status
        """
        if target_ip:
            return self._try_ip_connection(target_ip)
        else:
            # Use last known good IP if available
            if self.last_known_good_ip:
                network_info = self._try_ip_connection(self.last_known_good_ip)
                if network_info.status == ConnectionStatus.CONNECTED:
                    return network_info
                    
            # Fall back to full discovery
            discovered = self.discover_macbook()
            if discovered:
                return discovered
            else:
                return NetworkInfo(
                    hostname=self.macbook_hostname,
                    ip_address=self.macbook_ip,
                    port=self.http_port,
                    status=ConnectionStatus.UNREACHABLE,
                    last_check=datetime.now(),
                    error_message="MacBook not reachable via any method"
                )
                
    def ping_host(self, hostname_or_ip: str) -> Tuple[bool, Optional[float]]:
        """
        Ping a host to check basic network connectivity.
        
        Args:
            hostname_or_ip: Hostname or IP address to ping
            
        Returns:
            Tuple of (success, response_time_ms)
        """
        try:
            # Use Windows ping command
            cmd = ['ping', '-n', '1', '-w', str(self.ping_timeout * 1000), hostname_or_ip]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.ping_timeout + 2
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # Parse response time from ping output
                output = result.stdout
                if 'time=' in output:
                    try:
                        # Extract time from "time=XXXms" or "time<1ms"
                        time_part = output.split('time=')[1].split()[0]
                        if time_part.endswith('ms'):
                            response_time = float(time_part[:-2])
                        else:
                            response_time = elapsed_ms
                    except (IndexError, ValueError):
                        response_time = elapsed_ms
                else:
                    response_time = elapsed_ms
                    
                self.logger.debug(f"Ping successful: {hostname_or_ip} ({response_time:.1f}ms)")
                return True, response_time
            else:
                self.logger.debug(f"Ping failed: {hostname_or_ip}")
                return False, None
                
        except subprocess.TimeoutExpired:
            self.logger.debug(f"Ping timeout: {hostname_or_ip}")
            return False, None
        except Exception as e:
            self.logger.debug(f"Ping error for {hostname_or_ip}: {e}")
            return False, None
            
    def test_http_connection(self, ip_address: str, port: int = None) -> NetworkInfo:
        """
        Test HTTP connection to MacBook sync service.
        
        Args:
            ip_address: IP address to test
            port: Port to test (uses configured port if None)
            
        Returns:
            NetworkInfo with connection test results
        """
        if port is None:
            port = self.http_port
            
        network_info = NetworkInfo(
            hostname=self.macbook_hostname if ip_address == self.macbook_ip else ip_address,
            ip_address=ip_address,
            port=port,
            status=ConnectionStatus.DISCONNECTED,
            last_check=datetime.now()
        )
        
        try:
            self.logger.debug(f"Testing HTTP connection: {ip_address}:{port}")
            
            # Create socket connection
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connection_timeout)
            
            try:
                result = sock.connect_ex((ip_address, port))
                elapsed_ms = (time.time() - start_time) * 1000
                
                if result == 0:
                    network_info.status = ConnectionStatus.CONNECTED
                    network_info.response_time_ms = elapsed_ms
                    self.logger.debug(f"HTTP connection successful: {ip_address}:{port} ({elapsed_ms:.1f}ms)")
                else:
                    network_info.status = ConnectionStatus.UNREACHABLE
                    network_info.error_message = f"Connection refused (error {result})"
                    self.logger.debug(f"HTTP connection failed: {ip_address}:{port} (error {result})")
                    
            finally:
                sock.close()
                
        except socket.timeout:
            network_info.status = ConnectionStatus.TIMEOUT
            network_info.error_message = f"Connection timeout after {self.connection_timeout}s"
            self.logger.debug(f"HTTP connection timeout: {ip_address}:{port}")
        except Exception as e:
            network_info.status = ConnectionStatus.ERROR
            network_info.error_message = str(e)
            self.logger.debug(f"HTTP connection error: {ip_address}:{port} - {e}")
            
        # Record connection attempt
        self._record_connection_attempt(network_info)
        
        return network_info
        
    def resolve_hostname(self, hostname: str) -> Optional[str]:
        """
        Resolve hostname to IP address.
        
        Args:
            hostname: Hostname to resolve (e.g., 'MacBookM2.local')
            
        Returns:
            IP address string or None if resolution fails
        """
        try:
            self.logger.debug(f"Resolving hostname: {hostname}")
            
            # Use socket.getaddrinfo for better IPv4/IPv6 handling
            addr_info = socket.getaddrinfo(
                hostname, 
                None, 
                socket.AF_INET,  # IPv4 only for simplicity
                socket.SOCK_STREAM
            )
            
            if addr_info:
                ip_address = addr_info[0][4][0]
                self.logger.debug(f"Hostname resolved: {hostname} -> {ip_address}")
                return ip_address
            else:
                self.logger.debug(f"Hostname resolution failed: {hostname}")
                return None
                
        except socket.gaierror as e:
            self.logger.debug(f"Hostname resolution error: {hostname} - {e}")
            return None
        except Exception as e:
            self.logger.debug(f"Unexpected error resolving {hostname}: {e}")
            return None
            
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics and history.
        
        Returns:
            Dictionary with connection statistics
        """
        if not self.connection_history:
            return {
                'total_attempts': 0,
                'successful_connections': 0,
                'success_rate': 0.0,
                'average_response_time': None,
                'last_successful_connection': None
            }
            
        total_attempts = len(self.connection_history)
        successful = [conn for conn in self.connection_history 
                     if conn.status == ConnectionStatus.CONNECTED]
        
        success_rate = (len(successful) / total_attempts) * 100
        
        avg_response_time = None
        if successful:
            response_times = [conn.response_time_ms for conn in successful 
                            if conn.response_time_ms is not None]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                
        last_successful = None
        if successful:
            last_successful = max(successful, key=lambda x: x.last_check).last_check
            
        return {
            'total_attempts': total_attempts,
            'successful_connections': len(successful),
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'last_successful_connection': last_successful,
            'last_known_good_ip': self.last_known_good_ip
        }
        
    def _try_hostname_connection(self, hostname: str) -> Optional[NetworkInfo]:
        """Try to connect using hostname resolution."""
        try:
            # Resolve hostname to IP
            ip_address = self.resolve_hostname(hostname)
            if not ip_address:
                return NetworkInfo(
                    hostname=hostname,
                    ip_address="unknown",
                    port=self.http_port,
                    status=ConnectionStatus.UNREACHABLE,
                    last_check=datetime.now(),
                    error_message="Hostname resolution failed"
                )
                
            # Test HTTP connection
            return self.test_http_connection(ip_address)
            
        except Exception as e:
            self.logger.debug(f"Error trying hostname connection {hostname}: {e}")
            return None
            
    def _try_ip_connection(self, ip_address: str) -> NetworkInfo:
        """Try to connect using direct IP address."""
        # First try ping for basic connectivity
        ping_success, ping_time = self.ping_host(ip_address)
        
        if not ping_success:
            return NetworkInfo(
                hostname=self.macbook_hostname if ip_address == self.macbook_ip else ip_address,
                ip_address=ip_address,
                port=self.http_port,
                status=ConnectionStatus.UNREACHABLE,
                last_check=datetime.now(),
                error_message="Host unreachable (ping failed)"
            )
            
        # Test HTTP connection
        return self.test_http_connection(ip_address)
        
    def _record_connection_attempt(self, network_info: NetworkInfo):
        """Record connection attempt for statistics."""
        self.connection_history.append(network_info)
        
        # Limit history size
        if len(self.connection_history) > self.max_history_size:
            self.connection_history = self.connection_history[-self.max_history_size:]


class NetworkMonitor:
    """
    Monitors network connectivity changes and interface status.
    
    Provides notifications when network connectivity changes occur.
    """
    
    def __init__(self, network_manager: NetworkManager, 
                 logger: Optional[logging.Logger] = None):
        """Initialize network monitor."""
        self.network_manager = network_manager
        self.logger = logger or logging.getLogger(__name__)
        
        self.is_monitoring = False
        self.last_status = None
        self.status_change_callbacks = []
        
    def add_status_change_callback(self, callback):
        """Add callback for network status changes."""
        self.status_change_callbacks.append(callback)
        
    def check_network_changes(self) -> bool:
        """
        Check for network connectivity changes.
        
        Returns:
            True if network status changed, False otherwise
        """
        try:
            current_info = self.network_manager.check_connectivity()
            current_status = current_info.status
            
            if self.last_status != current_status:
                self.logger.info(f"Network status changed: {self.last_status} -> {current_status}")
                
                # Notify callbacks
                for callback in self.status_change_callbacks:
                    try:
                        callback(self.last_status, current_status, current_info)
                    except Exception as e:
                        self.logger.error(f"Error in status change callback: {e}")
                        
                self.last_status = current_status
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking network changes: {e}")
            return False
            
    def get_current_status(self) -> Optional[ConnectionStatus]:
        """Get current network status."""
        return self.last_status


def create_network_manager(config: Dict[str, Any], 
                          logger: Optional[logging.Logger] = None) -> NetworkManager:
    """
    Factory function to create a configured NetworkManager.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Configured NetworkManager instance
    """
    sync_config = config.get('sync', {})
    
    # Set default values
    network_config = {
        'macbookHostname': sync_config.get('macbookHostname', 'MacBookM2.local'),
        'macbookIP': sync_config.get('macbookIP', '192.168.1.100'),
        'httpPort': sync_config.get('httpPort', 8080),
        'connectionTimeout': sync_config.get('connectionTimeout', 10),
        'pingTimeout': sync_config.get('pingTimeout', 5)
    }
    
    return NetworkManager(network_config, logger)