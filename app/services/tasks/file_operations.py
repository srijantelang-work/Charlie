"""
File Operations Service
Handles secure file system operations with validation
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import hashlib
import mimetypes

logger = logging.getLogger(__name__)


class FileOperations:
    """Secure file operations service"""
    
    def __init__(self):
        # Define allowed directories for file operations
        self.allowed_directories = [
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Desktop"),
            str(Path.cwd()),  # Current working directory
        ]
        
        # Define restricted file extensions
        self.restricted_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
            '.sys', '.dll', '.msi', '.vbs', '.js', '.jar'
        }
        
        # Maximum file size (100MB)
        self.max_file_size = 100 * 1024 * 1024
    
    def _validate_path(self, file_path: str) -> bool:
        """Validate if file path is allowed"""
        try:
            abs_path = os.path.abspath(file_path)
            
            # Check if path is within allowed directories
            for allowed_dir in self.allowed_directories:
                if abs_path.startswith(os.path.abspath(allowed_dir)):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    def _validate_file_extension(self, file_path: str) -> bool:
        """Validate file extension"""
        extension = Path(file_path).suffix.lower()
        return extension not in self.restricted_extensions
    
    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file with content"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            if not self._validate_file_extension(path):
                return {
                    'success': False,
                    'error': 'File extension not allowed'
                }
            
            file_path = Path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if file_path.exists():
                return {
                    'success': False,
                    'error': 'File already exists'
                }
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'File created: {path}',
                'path': str(file_path),
                'size': len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            file_path = Path(path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            if not file_path.is_file():
                return {
                    'success': False,
                    'error': 'Path is not a file'
                }
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return {
                    'success': False,
                    'error': f'File too large: {file_size} bytes'
                }
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                return {
                    'success': True,
                    'content': content,
                    'path': str(file_path),
                    'size': file_size,
                    'mime_type': mimetypes.guess_type(str(file_path))[0]
                }
                
            except UnicodeDecodeError:
                # Try reading as binary for non-text files
                with open(file_path, 'rb') as f:
                    content = f.read()
                    
                return {
                    'success': True,
                    'content': content.hex(),  # Return as hex string
                    'path': str(file_path),
                    'size': file_size,
                    'mime_type': mimetypes.guess_type(str(file_path))[0],
                    'binary': True
                }
            
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file (overwrites existing)"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            if not self._validate_file_extension(path):
                return {
                    'success': False,
                    'error': 'File extension not allowed'
                }
            
            file_path = Path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'message': f'File written: {path}',
                'path': str(file_path),
                'size': len(content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            file_path = Path(path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            if not file_path.is_file():
                return {
                    'success': False,
                    'error': 'Path is not a file'
                }
            
            # Delete the file
            file_path.unlink()
            
            return {
                'success': True,
                'message': f'File deleted: {path}',
                'path': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_directory(self, path: str = ".") -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'Directory path not allowed'
                }
            
            dir_path = Path(path)
            
            if not dir_path.exists():
                return {
                    'success': False,
                    'error': 'Directory does not exist'
                }
            
            if not dir_path.is_dir():
                return {
                    'success': False,
                    'error': 'Path is not a directory'
                }
            
            items = []
            for item in dir_path.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else None,
                        'modified': stat.st_mtime,
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
            
            # Sort items: directories first, then files
            items.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            return {
                'success': True,
                'path': str(dir_path),
                'items': items,
                'count': len(items)
            }
            
        except Exception as e:
            logger.error(f"Failed to list directory: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file to another location"""
        try:
            if not self._validate_path(source) or not self._validate_path(destination):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {
                    'success': False,
                    'error': 'Source file does not exist'
                }
            
            if not source_path.is_file():
                return {
                    'success': False,
                    'error': 'Source is not a file'
                }
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            
            return {
                'success': True,
                'message': f'File copied from {source} to {destination}',
                'source': str(source_path),
                'destination': str(dest_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file to another location"""
        try:
            if not self._validate_path(source) or not self._validate_path(destination):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return {
                    'success': False,
                    'error': 'Source file does not exist'
                }
            
            if not source_path.is_file():
                return {
                    'success': False,
                    'error': 'Source is not a file'
                }
            
            # Create destination directory if it doesn't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            
            return {
                'success': True,
                'message': f'File moved from {source} to {destination}',
                'source': str(source_path),
                'destination': str(dest_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            if not self._validate_path(path):
                return {
                    'success': False,
                    'error': 'File path not allowed'
                }
            
            file_path = Path(path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File does not exist'
                }
            
            stat = file_path.stat()
            
            # Calculate file hash for integrity
            file_hash = None
            if file_path.is_file() and stat.st_size < 10 * 1024 * 1024:  # Only for files < 10MB
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                except:
                    pass
            
            return {
                'success': True,
                'path': str(file_path),
                'name': file_path.name,
                'type': 'directory' if file_path.is_dir() else 'file',
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'permissions': oct(stat.st_mode)[-3:],
                'mime_type': mimetypes.guess_type(str(file_path))[0] if file_path.is_file() else None,
                'hash': file_hash
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {
                'success': False,
                'error': str(e)
            } 