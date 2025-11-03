"""
Troubleshooting utilities for EFIS Data Manager.
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class SystemDiagnostics:
    """System diagnostics and troubleshooting utilities."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize diagnostics."""
        self.logger = logger or logging.getLogger(__name__)
        self.platform = platform.system().lower()
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics."""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform,
            'system_info': self._get_system_info(),
            'python_info': self._get_python_info(),
            'disk_space': self._check_disk_space(),
            'network_connectivity': self._check_network_connectivity(),
            'process_status': self._check_processes(),
            'log_analysis': self._analyze_logs(),
            'configuration_check': self._check_configuration(),
            'recommendations': []
        }
        
        # Add platform-specific checks
        if self.platform == 'windows':
            diagnostics['windows_specific'] = self._windows_diagnostics()
        elif self.platform == 'darwin':
            diagnostics['macos_specific'] = self._macos_diagnostics()
        
        # Generate recommendations based on findings
        diagnostics['recommendations'] = self._generate_recommendations(diagnostics)
        
        return diagnostics
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        try:
            return {
                'platform': platform.platform(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': platform.node(),
                'uptime': self._get_uptime()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_python_info(self) -> Dict[str, Any]:
        """Get Python environment information."""
        try:
            return {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path[:5],  # First 5 entries
                'modules': self._check_required_modules()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_required_modules(self) -> Dict[str, bool]:
        """Check if required Python modules are available."""
        required_modules = [
            'json', 'logging', 'pathlib', 'subprocess', 'threading',
            'datetime', 'typing', 'dataclasses', 'enum'
        ]
        
        # Platform-specific modules
        if self.platform == 'windows':
            required_modules.extend(['win32serviceutil', 'win32service', 'win32event'])
        
        module_status = {}
        for module in required_modules:
            try:
                __import__(module)
                module_status[module] = True
            except ImportError:
                module_status[module] = False
        
        return module_status
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space on relevant drives."""
        try:
            disk_info = {}
            
            if self.platform == 'windows':
                # Check C: drive and any configured drives
                drives = ['C:\\']
                
                # Add configured drive letters if available
                try:
                    # This would read from config if available
                    drives.append('E:\\')  # Virtual drive
                except:
                    pass
                
                for drive in drives:
                    if os.path.exists(drive):
                        try:
                            import shutil
                            total, used, free = shutil.disk_usage(drive)
                            disk_info[drive] = {
                                'total_gb': total / (1024**3),
                                'used_gb': used / (1024**3),
                                'free_gb': free / (1024**3),
                                'usage_percent': (used / total) * 100
                            }
                        except Exception as e:
                            disk_info[drive] = {'error': str(e)}
            
            elif self.platform == 'darwin':
                # Check root and common mount points
                mount_points = ['/', '/Volumes']
                
                for mount_point in mount_points:
                    if os.path.exists(mount_point):
                        try:
                            import shutil
                            total, used, free = shutil.disk_usage(mount_point)
                            disk_info[mount_point] = {
                                'total_gb': total / (1024**3),
                                'used_gb': used / (1024**3),
                                'free_gb': free / (1024**3),
                                'usage_percent': (used / total) * 100
                            }
                        except Exception as e:
                            disk_info[mount_point] = {'error': str(e)}
            
            return disk_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            connectivity = {}
            
            # Test basic internet connectivity
            test_hosts = ['8.8.8.8', 'google.com']
            
            for host in test_hosts:
                try:
                    if self.platform == 'windows':
                        result = subprocess.run(
                            ['ping', '-n', '1', host],
                            capture_output=True,
                            timeout=5
                        )
                    else:
                        result = subprocess.run(
                            ['ping', '-c', '1', host],
                            capture_output=True,
                            timeout=5
                        )
                    
                    connectivity[host] = {
                        'reachable': result.returncode == 0,
                        'response_time': 'success' if result.returncode == 0 else 'failed'
                    }
                    
                except subprocess.TimeoutExpired:
                    connectivity[host] = {'reachable': False, 'response_time': 'timeout'}
                except Exception as e:
                    connectivity[host] = {'error': str(e)}
            
            return connectivity
            
        except Exception as e:
            return {'error': str(e)}
    
    def _check_processes(self) -> Dict[str, Any]:
        """Check relevant processes."""
        try:
            processes = {}
            
            if self.platform == 'windows':
                # Check for EFIS service and related processes
                process_names = ['EFISDataManager', 'MountImg.exe', 'python.exe']
                
                for process_name in process_names:
                    try:
                        result = subprocess.run(
                            ['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                            capture_output=True,
                            text=True
                        )
                        
                        processes[process_name] = {
                            'running': process_name.lower() in result.stdout.lower(),
                            'details': result.stdout.strip() if result.returncode == 0 else 'error'
                        }
                        
                    except Exception as e:
                        processes[process_name] = {'error': str(e)}
            
            elif self.platform == 'darwin':
                # Check for daemon and related processes
                process_names = ['efis_daemon', 'python3']
                
                for process_name in process_names:
                    try:
                        result = subprocess.run(
                            ['pgrep', '-f', process_name],
                            capture_output=True,
                            text=True
                        )
                        
                        processes[process_name] = {
                            'running': result.returncode == 0,
                            'pids': result.stdout.strip().split('\n') if result.returncode == 0 else []
                        }
                        
                    except Exception as e:
                        processes[process_name] = {'error': str(e)}
            
            return processes
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_logs(self) -> Dict[str, Any]:
        """Analyze system logs for issues."""
        try:
            log_analysis = {
                'recent_errors': [],
                'warning_count': 0,
                'error_count': 0,
                'last_activity': None
            }
            
            # Common log locations
            log_paths = []
            
            if self.platform == 'windows':
                log_paths = [
                    'C:\\Scripts\\efis-data-manager.log',
                    'C:\\Scripts\\MountEFIS.log'
                ]
            elif self.platform == 'darwin':
                log_paths = [
                    '/var/log/efis-daemon.log',
                    os.path.expanduser('~/Library/Logs/efis-data-manager.log')
                ]
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    try:
                        # Read last 100 lines
                        with open(log_path, 'r') as f:
                            lines = f.readlines()[-100:]
                        
                        for line in lines:
                            line_lower = line.lower()
                            if 'error' in line_lower:
                                log_analysis['error_count'] += 1
                                if len(log_analysis['recent_errors']) < 5:
                                    log_analysis['recent_errors'].append(line.strip())
                            elif 'warning' in line_lower:
                                log_analysis['warning_count'] += 1
                        
                        # Get last modification time
                        mtime = os.path.getmtime(log_path)
                        last_modified = datetime.fromtimestamp(mtime)
                        
                        if not log_analysis['last_activity'] or last_modified > log_analysis['last_activity']:
                            log_analysis['last_activity'] = last_modified.isoformat()
                    
                    except Exception as e:
                        log_analysis[f'log_error_{log_path}'] = str(e)
            
            return log_analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration files."""
        try:
            config_check = {
                'files_found': [],
                'files_missing': [],
                'configuration_valid': True,
                'issues': []
            }
            
            # Common config locations
            config_paths = []
            
            if self.platform == 'windows':
                config_paths = [
                    'config/windows-config.json',
                    'C:/Scripts/efis-config.json'
                ]
            elif self.platform == 'darwin':
                config_paths = [
                    'config/macos-config.yaml',
                    os.path.expanduser('~/.efis/config.yaml')
                ]
            
            for config_path in config_paths:
                if os.path.exists(config_path):
                    config_check['files_found'].append(config_path)
                    
                    # Basic validation
                    try:
                        if config_path.endswith('.json'):
                            import json
                            with open(config_path, 'r') as f:
                                json.load(f)
                        elif config_path.endswith('.yaml'):
                            # Would use yaml.load if available
                            pass
                    except Exception as e:
                        config_check['configuration_valid'] = False
                        config_check['issues'].append(f"Invalid config {config_path}: {e}")
                else:
                    config_check['files_missing'].append(config_path)
            
            return config_check
            
        except Exception as e:
            return {'error': str(e)}
    
    def _windows_diagnostics(self) -> Dict[str, Any]:
        """Windows-specific diagnostics."""
        try:
            windows_info = {}
            
            # Check ImDisk installation
            imdisk_paths = [
                'C:\\Program Files\\ImDisk\\MountImg.exe',
                'C:\\Program Files (x86)\\ImDisk\\MountImg.exe'
            ]
            
            windows_info['imdisk_installed'] = any(os.path.exists(path) for path in imdisk_paths)
            
            # Check Windows services
            try:
                result = subprocess.run(
                    ['sc', 'query', 'EFISDataManager'],
                    capture_output=True,
                    text=True
                )
                windows_info['service_installed'] = result.returncode == 0
                windows_info['service_status'] = result.stdout if result.returncode == 0 else 'Not installed'
            except Exception as e:
                windows_info['service_error'] = str(e)
            
            # Check scheduled tasks
            try:
                result = subprocess.run(
                    ['schtasks', '/query', '/tn', 'MountEFIS'],
                    capture_output=True,
                    text=True
                )
                windows_info['scheduled_task_exists'] = result.returncode == 0
            except Exception as e:
                windows_info['scheduled_task_error'] = str(e)
            
            return windows_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _macos_diagnostics(self) -> Dict[str, Any]:
        """macOS-specific diagnostics."""
        try:
            macos_info = {}
            
            # Check launchd services
            try:
                result = subprocess.run(
                    ['launchctl', 'list', 'com.efis-data-manager.daemon'],
                    capture_output=True,
                    text=True
                )
                macos_info['daemon_loaded'] = result.returncode == 0
                macos_info['daemon_status'] = result.stdout if result.returncode == 0 else 'Not loaded'
            except Exception as e:
                macos_info['daemon_error'] = str(e)
            
            # Check USB monitoring
            try:
                result = subprocess.run(['df', '-h'], capture_output=True, text=True)
                usb_drives = []
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '/Volumes/' in line:
                            usb_drives.append(line.strip())
                macos_info['usb_drives'] = usb_drives
            except Exception as e:
                macos_info['usb_error'] = str(e)
            
            return macos_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_uptime(self) -> Optional[str]:
        """Get system uptime."""
        try:
            if self.platform == 'windows':
                result = subprocess.run(
                    ['wmic', 'os', 'get', 'LastBootUpTime'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            elif self.platform == 'darwin':
                result = subprocess.run(['uptime'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return None
            
        except Exception:
            return None
    
    def _generate_recommendations(self, diagnostics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on diagnostic results."""
        recommendations = []
        
        # Check disk space
        disk_space = diagnostics.get('disk_space', {})
        for drive, info in disk_space.items():
            if isinstance(info, dict) and 'usage_percent' in info:
                if info['usage_percent'] > 90:
                    recommendations.append(f"Critical: {drive} is {info['usage_percent']:.1f}% full. Free up disk space.")
                elif info['usage_percent'] > 80:
                    recommendations.append(f"Warning: {drive} is {info['usage_percent']:.1f}% full. Consider freeing up space.")
        
        # Check network connectivity
        network = diagnostics.get('network_connectivity', {})
        if isinstance(network, dict):
            unreachable_hosts = [host for host, info in network.items() 
                               if isinstance(info, dict) and not info.get('reachable', True)]
            if unreachable_hosts:
                recommendations.append(f"Network connectivity issues detected for: {', '.join(unreachable_hosts)}")
        
        # Check log analysis
        log_analysis = diagnostics.get('log_analysis', {})
        if isinstance(log_analysis, dict):
            error_count = log_analysis.get('error_count', 0)
            if error_count > 10:
                recommendations.append(f"High error count in logs ({error_count} errors). Check log files for details.")
            
            last_activity = log_analysis.get('last_activity')
            if last_activity:
                try:
                    last_time = datetime.fromisoformat(last_activity)
                    if datetime.now() - last_time > timedelta(hours=24):
                        recommendations.append("No recent log activity detected. System may not be running.")
                except:
                    pass
        
        # Platform-specific recommendations
        if self.platform == 'windows':
            windows_info = diagnostics.get('windows_specific', {})
            if isinstance(windows_info, dict):
                if not windows_info.get('imdisk_installed', False):
                    recommendations.append("ImDisk not found. Install ImDisk for virtual drive functionality.")
                if not windows_info.get('service_installed', False):
                    recommendations.append("EFIS service not installed. Run 'efis service install' to install.")
        
        elif self.platform == 'darwin':
            macos_info = diagnostics.get('macos_specific', {})
            if isinstance(macos_info, dict):
                if not macos_info.get('daemon_loaded', False):
                    recommendations.append("EFIS daemon not loaded. Check launchd configuration.")
        
        # Configuration recommendations
        config_check = diagnostics.get('configuration_check', {})
        if isinstance(config_check, dict):
            if not config_check.get('configuration_valid', True):
                recommendations.append("Configuration file issues detected. Check configuration syntax.")
            
            missing_files = config_check.get('files_missing', [])
            if missing_files:
                recommendations.append(f"Missing configuration files: {', '.join(missing_files)}")
        
        if not recommendations:
            recommendations.append("No issues detected. System appears to be functioning normally.")
        
        return recommendations