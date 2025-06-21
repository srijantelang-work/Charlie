"""
Application Control Service (Windows-specific)
Handles launching, controlling, and monitoring Windows applications
"""

import os
import subprocess
import psutil
import logging
import time
import platform
from typing import Dict, Any, List, Optional
from pathlib import Path

# Windows-specific imports with fallback
try:
    import win32gui  # type: ignore
    import win32con  # type: ignore
    import win32process  # type: ignore
    import win32api  # type: ignore
    WINDOWS_API_AVAILABLE = True
except ImportError:
    # Graceful fallback for non-Windows systems or missing pywin32
    win32gui = None
    win32con = None
    win32process = None
    win32api = None
    WINDOWS_API_AVAILABLE = False

logger = logging.getLogger(__name__)


class AppControl:
    """Windows application control service"""
    
    def __init__(self):
        # Check if we're running on Windows
        self.is_windows = platform.system() == "Windows"
        self.windows_api_available = WINDOWS_API_AVAILABLE and self.is_windows
        
        if not self.is_windows:
            logger.warning("AppControl service initialized on non-Windows platform. Limited functionality available.")
        elif not WINDOWS_API_AVAILABLE:
            logger.warning("pywin32 not available. Window management features will be disabled.")
        
        # Define common application paths
        self.app_paths = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe',
            'explorer': 'explorer.exe',
            'chrome': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
            ],
            'firefox': [
                r'C:\Program Files\Mozilla Firefox\firefox.exe',
                r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe'
            ],
            'edge': r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            'vscode': [
                r'C:\Program Files\Microsoft VS Code\Code.exe',
                r'C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe'.format(os.getenv('USERNAME'))
            ]
        }
        
        # Define restricted applications for security
        self.restricted_apps = {
            'regedit.exe', 'msconfig.exe', 'gpedit.msc', 'services.msc',
            'taskmgr.exe', 'control.exe', 'mmc.exe'
        }
    
    def _find_app_path(self, app_name: str) -> Optional[str]:
        """Find the full path to an application"""
        app_name_lower = app_name.lower()
        
        # Check if it's in our predefined paths
        if app_name_lower in self.app_paths:
            app_path = self.app_paths[app_name_lower]
            
            if isinstance(app_path, list):
                # Multiple possible paths
                for path in app_path:
                    if os.path.exists(path):
                        return path
            elif isinstance(app_path, str):
                # Single path or system command
                if os.path.exists(app_path) or app_path in ['notepad.exe', 'calc.exe', 'cmd.exe', 'powershell.exe']:
                    return app_path
        
        # Check if it's a direct path
        if os.path.exists(app_name):
            return app_name
        
        # Try to find in PATH
        try:
            result = subprocess.run(['where', app_name], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None
    
    def _is_app_allowed(self, app_path: str) -> bool:
        """Check if application is allowed to be launched"""
        app_name = Path(app_path).name.lower()
        return app_name not in self.restricted_apps
    
    def launch_application(self, app_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launch a Windows application"""
        try:
            app_path = self._find_app_path(app_name)
            
            if not app_path:
                return {
                    'success': False,
                    'error': f'Application not found: {app_name}'
                }
            
            if not self._is_app_allowed(app_path):
                return {
                    'success': False,
                    'error': f'Application not allowed: {app_name}'
                }
            
            # Build command
            command = [app_path]
            if args:
                command.extend(args)
            
            # Launch application
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait a moment to check if it started successfully
            time.sleep(1)
            
            if process.poll() is None:  # Process is still running
                return {
                    'success': True,
                    'message': f'Application launched: {app_name}',
                    'pid': process.pid,
                    'app_path': app_path,
                    'command': ' '.join(command)
                }
            else:
                # Process terminated immediately
                stdout, stderr = process.communicate()
                return {
                    'success': False,
                    'error': f'Application failed to start: {stderr.decode()}',
                    'return_code': process.returncode
                }
            
        except Exception as e:
            logger.error(f"Failed to launch application: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def kill_process(self, process_name: str) -> Dict[str, Any]:
        """Kill a process by name"""
        try:
            killed_processes = []
            
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if process.name().lower() == process_name.lower():
                        process.kill()
                        killed_processes.append({
                            'pid': process.pid,
                            'name': process.name()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_processes:
                return {
                    'success': True,
                    'message': f'Killed {len(killed_processes)} process(es)',
                    'killed_processes': killed_processes
                }
            else:
                return {
                    'success': False,
                    'error': f'No processes found with name: {process_name}'
                }
                
        except Exception as e:
            logger.error(f"Failed to kill process: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_processes(self) -> Dict[str, Any]:
        """List running processes"""
        try:
            processes = []
            
            for process in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    processes.append({
                        'pid': process.pid,
                        'name': process.name(),
                        'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                        'cpu_percent': process.cpu_percent()
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            return {
                'success': True,
                'processes': processes[:50],  # Limit to top 50 processes
                'total_processes': len(processes)
            }
            
        except Exception as e:
            logger.error(f"Failed to list processes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def focus_window(self, window_title: str) -> Dict[str, Any]:
        """Focus a window by title"""
        if not self.windows_api_available:
            return {
                'success': False,
                'error': 'Window management not available on this platform or pywin32 not installed'
            }
            
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):  # type: ignore
                    window_text = win32gui.GetWindowText(hwnd)  # type: ignore
                    if window_title.lower() in window_text.lower():
                        windows.append((hwnd, window_text))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)  # type: ignore
            
            if not windows:
                return {
                    'success': False,
                    'error': f'No window found with title containing: {window_title}'
                }
            
            # Focus the first matching window
            hwnd, title = windows[0]
            
            # Restore window if minimized
            if win32gui.IsIconic(hwnd):  # type: ignore
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # type: ignore
            
            # Bring window to foreground
            win32gui.SetForegroundWindow(hwnd)  # type: ignore
            
            return {
                'success': True,
                'message': f'Focused window: {title}',
                'window_title': title,
                'window_handle': hwnd
            }
            
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_windows(self) -> Dict[str, Any]:
        """List all visible windows"""
        if not self.windows_api_available:
            return {
                'success': False,
                'error': 'Window management not available on this platform or pywin32 not installed'
            }
            
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):  # type: ignore
                    window_text = win32gui.GetWindowText(hwnd)  # type: ignore
                    if window_text:  # Only include windows with titles
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)  # type: ignore
                            process_name = psutil.Process(pid).name()
                            windows.append({
                                'handle': hwnd,
                                'title': window_text,
                                'pid': pid,
                                'process_name': process_name
                            })
                        except:
                            windows.append({
                                'handle': hwnd,
                                'title': window_text,
                                'pid': None,
                                'process_name': 'Unknown'
                            })
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)  # type: ignore
            
            return {
                'success': True,
                'windows': windows,
                'count': len(windows)
            }
            
        except Exception as e:
            logger.error(f"Failed to list windows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def minimize_window(self, window_title: str) -> Dict[str, Any]:
        """Minimize a window by title"""
        if not self.windows_api_available:
            return {
                'success': False,
                'error': 'Window management not available on this platform or pywin32 not installed'
            }
            
        try:
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):  # type: ignore
                    window_text = win32gui.GetWindowText(hwnd)  # type: ignore
                    if window_title.lower() in window_text.lower():
                        windows.append((hwnd, window_text))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)  # type: ignore
            
            if not windows:
                return {
                    'success': False,
                    'error': f'No window found with title containing: {window_title}'
                }
            
            # Minimize the first matching window
            hwnd, title = windows[0]
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)  # type: ignore
            
            return {
                'success': True,
                'message': f'Minimized window: {title}',
                'window_title': title
            }
            
        except Exception as e:
            logger.error(f"Failed to minimize window: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            # Get CPU information
            cpu_freq_info = psutil.cpu_freq()
            freq_dict = None
            if cpu_freq_info:
                try:
                    freq_dict = cpu_freq_info._asdict()  # type: ignore
                except AttributeError:
                    # Handle case where cpu_freq returns a list or different type
                    if isinstance(cpu_freq_info, (list, tuple)) and len(cpu_freq_info) >= 3:
                        freq_dict = {
                            'current': cpu_freq_info[0] if len(cpu_freq_info) > 0 else None,
                            'min': cpu_freq_info[1] if len(cpu_freq_info) > 1 else None,
                            'max': cpu_freq_info[2] if len(cpu_freq_info) > 2 else None
                        }
            
            cpu_info = {
                'count': psutil.cpu_count(),
                'percent': psutil.cpu_percent(interval=1),
                'freq': freq_dict
            }
            
            # Get memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'total_gb': round(memory.total / 1024**3, 2),
                'available_gb': round(memory.available / 1024**3, 2),
                'used_gb': round(memory.used / 1024**3, 2),
                'percent': memory.percent
            }
            
            # Get disk information
            disk = psutil.disk_usage('C:')
            disk_info = {
                'total_gb': round(disk.total / 1024**3, 2),
                'free_gb': round(disk.free / 1024**3, 2),
                'used_gb': round(disk.used / 1024**3, 2),
                'percent': round((disk.used / disk.total) * 100, 2)
            }
            
            return {
                'success': True,
                'system': {
                    'platform': platform.platform(),
                    'processor': platform.processor(),
                    'machine': platform.machine(),
                    'python_version': platform.python_version()
                },
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info,
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {
                'success': False,
                'error': str(e)
            } 