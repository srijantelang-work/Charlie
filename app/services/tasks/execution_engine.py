"""
Secure Task Execution Engine
Implements sandboxed Python script execution with security validation
"""

import os
import sys
import tempfile
import subprocess
import asyncio
import psutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
import time
import json
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    RESTRICTED = "restricted"


class TaskExecutionError(Exception):
    """Custom exception for task execution errors"""
    pass


class SecurityViolationError(Exception):
    """Exception for security violations"""
    pass


class TaskExecutor:
    """Secure task execution engine with sandboxing"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "charlie_tasks"
        self.temp_dir.mkdir(exist_ok=True)
        self.running_tasks = {}
        
        # Security configuration
        self.max_execution_time = 300  # 5 minutes
        self.max_memory_mb = 512
        self.max_cpu_percent = 50
        
        # Allowed modules for script execution
        self.allowed_modules = {
            'json', 'math', 'datetime', 'time', 'pathlib', 'os.path',
            'requests', 'urllib', 'base64', 're', 'string', 'hashlib'
        }
        
        # Restricted operations
        self.restricted_keywords = [
            'import os', 'import sys', 'import subprocess', 'exec(',
            'eval(', '__import__', 'compile(', 'open(', 'file(',
            'input(', 'raw_input(', 'execfile(', 'reload('
        ]

    async def execute_task(
        self,
        task_id: str,
        task_type: str,
        script_content: str,
        parameters: Dict[str, Any],
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a task with security validation"""
        
        try:
            # Validate security
            self._validate_security(script_content, security_level)
            
            # Create task context
            task_context = {
                'task_id': task_id,
                'task_type': task_type,
                'user_id': user_id,
                'parameters': parameters,
                'status': TaskStatus.PENDING,
                'start_time': time.time(),
                'security_level': security_level
            }
            
            self.running_tasks[task_id] = task_context
            
            # Execute based on task type
            if task_type == "python_script":
                result = await self._execute_python_script(
                    task_id, script_content, parameters, security_level
                )
            elif task_type == "system_command":
                result = await self._execute_system_command(
                    task_id, script_content, parameters, security_level
                )
            else:
                raise TaskExecutionError(f"Unknown task type: {task_type}")
            
            # Update task status
            task_context['status'] = TaskStatus.COMPLETED
            task_context['end_time'] = time.time()
            task_context['result'] = result
            
            return {
                'task_id': task_id,
                'status': TaskStatus.COMPLETED,
                'result': result,
                'execution_time': task_context['end_time'] - task_context['start_time']
            }
            
        except Exception as e:
            logger.error(f"Task execution failed for {task_id}: {e}")
            if task_id in self.running_tasks:
                self.running_tasks[task_id]['status'] = TaskStatus.FAILED
                self.running_tasks[task_id]['error'] = str(e)
            
            raise TaskExecutionError(f"Task execution failed: {str(e)}")

    def _validate_security(self, script_content: str, security_level: SecurityLevel):
        """Validate script content for security violations"""
        
        if security_level == SecurityLevel.RESTRICTED:
            # Very strict validation
            for keyword in self.restricted_keywords:
                if keyword in script_content:
                    raise SecurityViolationError(f"Restricted keyword found: {keyword}")
        
        # Check for potentially dangerous imports
        lines = script_content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                module_name = line.split()[1].split('.')[0]
                if module_name not in self.allowed_modules and security_level in [SecurityLevel.HIGH, SecurityLevel.RESTRICTED]:
                    raise SecurityViolationError(f"Module not allowed: {module_name}")

    async def _execute_python_script(
        self,
        task_id: str,
        script_content: str,
        parameters: Dict[str, Any],
        security_level: SecurityLevel
    ) -> Dict[str, Any]:
        """Execute Python script in sandboxed environment"""
        
        # Create temporary script file
        script_file = self.temp_dir / f"task_{task_id}.py"
        
        try:
            # Prepare script with parameters injection
            full_script = f"""
import json
import sys
import traceback

# Injected parameters
TASK_PARAMETERS = {json.dumps(parameters)}

try:
    # User script content
{script_content}
    
    # Return success if no exceptions
    result = {{"success": True, "output": "Script executed successfully"}}
    print(json.dumps(result))
    
except Exception as e:
    error_result = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(error_result))
    sys.exit(1)
"""
            
            # Write script to file
            with open(script_file, 'w') as f:
                f.write(full_script)
            
            # Execute script with resource limits
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            # Monitor resource usage
            monitor_task = asyncio.create_task(
                self._monitor_process(process, task_id)
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.max_execution_time
                )
                
                monitor_task.cancel()
                
                # Parse result
                try:
                    result = json.loads(stdout.decode())
                    if stderr:
                        result['warnings'] = stderr.decode()
                    return result
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid script output',
                        'stdout': stdout.decode(),
                        'stderr': stderr.decode()
                    }
                    
            except asyncio.TimeoutError:
                process.kill()
                monitor_task.cancel()
                raise TaskExecutionError("Script execution timeout")
                
        finally:
            # Cleanup
            if script_file.exists():
                script_file.unlink()

    async def _execute_system_command(
        self,
        task_id: str,
        command: str,
        parameters: Dict[str, Any],
        security_level: SecurityLevel
    ) -> Dict[str, Any]:
        """Execute system command with security restrictions"""
        
        if security_level in [SecurityLevel.HIGH, SecurityLevel.RESTRICTED]:
            raise SecurityViolationError("System commands not allowed at this security level")
        
        # Whitelist of allowed commands
        allowed_commands = [
            'dir', 'ls', 'echo', 'type', 'cat', 'find', 'grep',
            'powershell.exe -Command Get-Process',
            'powershell.exe -Command Get-Service'
        ]
        
        command_base = command.split()[0] if command else ""
        if command_base not in [cmd.split()[0] for cmd in allowed_commands]:
            raise SecurityViolationError(f"Command not allowed: {command_base}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30  # Shorter timeout for system commands
            )
            
            return {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode(),
                'stderr': stderr.decode()
            }
            
        except asyncio.TimeoutError:
            raise TaskExecutionError("Command execution timeout")

    async def _monitor_process(self, process: asyncio.subprocess.Process, task_id: str):
        """Monitor process resource usage"""
        
        try:
            if process.pid:
                psutil_process = psutil.Process(process.pid)
                
                while process.returncode is None:
                    try:
                        # Check memory usage
                        memory_info = psutil_process.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024
                        
                        if memory_mb > self.max_memory_mb:
                            process.kill()
                            raise TaskExecutionError(f"Memory limit exceeded: {memory_mb}MB")
                        
                        # Check CPU usage
                        cpu_percent = psutil_process.cpu_percent()
                        if cpu_percent > self.max_cpu_percent:
                            logger.warning(f"High CPU usage for task {task_id}: {cpu_percent}%")
                        
                        await asyncio.sleep(1)
                        
                    except psutil.NoSuchProcess:
                        break
                        
        except Exception as e:
            logger.error(f"Process monitoring error for task {task_id}: {e}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a running task"""
        return self.running_tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]['status'] = TaskStatus.CANCELLED
            # In a real implementation, you'd also terminate the process
            return True
        return False

    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        current_time = time.time()
        to_remove = []
        
        for task_id, task_info in self.running_tasks.items():
            if 'end_time' in task_info:
                age_hours = (current_time - task_info['end_time']) / 3600
                if age_hours > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.running_tasks[task_id]


# Global executor instance
task_executor = TaskExecutor() 