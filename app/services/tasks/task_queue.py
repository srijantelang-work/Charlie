"""
Celery Task Queue System
Handles async task processing with Redis broker
"""

import logging
import uuid
from typing import Dict, Any, Optional
from celery import Celery
from celery.result import AsyncResult
import asyncio

from app.core.config import settings
from app.services.tasks.execution_engine import task_executor, SecurityLevel

logger = logging.getLogger(__name__)

# Configure Celery
celery_app = Celery(
    "charlie_tasks",
    broker=f"redis://localhost:6379/0",
    backend=f"redis://localhost:6379/0",
    include=["app.services.tasks.task_queue"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.services.tasks.task_queue.execute_script_task": {"queue": "scripts"},
        "app.services.tasks.task_queue.execute_email_task": {"queue": "email"},
        "app.services.tasks.task_queue.execute_file_task": {"queue": "files"},
        "app.services.tasks.task_queue.execute_app_control_task": {"queue": "system"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@celery_app.task(bind=True, name="execute_script_task")
def execute_script_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Python script task"""
    try:
        task_id = task_data.get("task_id", str(uuid.uuid4()))
        script_content = task_data.get("script_content", "")
        parameters = task_data.get("parameters", {})
        security_level = SecurityLevel(task_data.get("security_level", "medium"))
        user_id = task_data.get("user_id")
        
        # Update task status
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        # Execute script using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                task_executor.execute_task(
                    task_id=task_id,
                    task_type="python_script",
                    script_content=script_content,
                    parameters=parameters,
                    security_level=security_level,
                    user_id=user_id
                )
            )
            
            self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Script task execution failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


@celery_app.task(bind=True, name="execute_email_task")
def execute_email_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute email automation task"""
    try:
        from app.services.tasks.email_automation import EmailAutomation
        
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        email_service = EmailAutomation()
        
        action = task_data.get("action", "send")
        parameters = task_data.get("parameters", {})
        
        if action == "send":
            result = email_service.send_email(
                to=parameters.get("to"),
                subject=parameters.get("subject"),
                body=parameters.get("body"),
                attachments=parameters.get("attachments", [])
            )
        elif action == "read":
            result = email_service.read_emails(
                limit=parameters.get("limit", 10),
                unread_only=parameters.get("unread_only", True)
            )
        else:
            raise ValueError(f"Unknown email action: {action}")
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
        return result
        
    except Exception as e:
        logger.error(f"Email task execution failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


@celery_app.task(bind=True, name="execute_file_task")
def execute_file_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute file system operation task"""
    try:
        from app.services.tasks.file_operations import FileOperations
        
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        file_service = FileOperations()
        
        operation = task_data.get("operation")
        parameters = task_data.get("parameters", {})
        
        if operation == "create":
            result = file_service.create_file(
                path=parameters.get("path"),
                content=parameters.get("content", "")
            )
        elif operation == "read":
            result = file_service.read_file(
                path=parameters.get("path")
            )
        elif operation == "write":
            result = file_service.write_file(
                path=parameters.get("path"),
                content=parameters.get("content")
            )
        elif operation == "delete":
            result = file_service.delete_file(
                path=parameters.get("path")
            )
        elif operation == "list":
            result = file_service.list_directory(
                path=parameters.get("path", ".")
            )
        else:
            raise ValueError(f"Unknown file operation: {operation}")
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
        return result
        
    except Exception as e:
        logger.error(f"File task execution failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


@celery_app.task(bind=True, name="execute_app_control_task")
def execute_app_control_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute application control task (Windows-specific)"""
    try:
        from app.services.tasks.app_control import AppControl
        
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        app_control = AppControl()
        
        action = task_data.get("action")
        parameters = task_data.get("parameters", {})
        
        if action == "launch":
            result = app_control.launch_application(
                app_name=parameters.get("app_name"),
                args=parameters.get("args", [])
            )
        elif action == "kill":
            result = app_control.kill_process(
                process_name=parameters.get("process_name")
            )
        elif action == "list":
            result = app_control.list_processes()
        elif action == "focus":
            result = app_control.focus_window(
                window_title=parameters.get("window_title")
            )
        else:
            raise ValueError(f"Unknown app control action: {action}")
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
        return result
        
    except Exception as e:
        logger.error(f"App control task execution failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


@celery_app.task(bind=True, name="execute_calendar_task")
def execute_calendar_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute calendar management task"""
    try:
        from app.services.tasks.calendar_automation import CalendarAutomation
        
        self.update_state(state="PROCESSING", meta={"progress": 0})
        
        calendar_service = CalendarAutomation()
        
        action = task_data.get("action")
        parameters = task_data.get("parameters", {})
        
        if action == "create_event":
            result = calendar_service.create_event(
                title=parameters.get("title"),
                start_time=parameters.get("start_time"),
                end_time=parameters.get("end_time"),
                description=parameters.get("description", ""),
                attendees=parameters.get("attendees", [])
            )
        elif action == "list_events":
            result = calendar_service.list_events(
                start_date=parameters.get("start_date"),
                end_date=parameters.get("end_date"),
                max_results=parameters.get("max_results", 10)
            )
        elif action == "update_event":
            result = calendar_service.update_event(
                event_id=parameters.get("event_id"),
                updates=parameters.get("updates", {})
            )
        elif action == "delete_event":
            result = calendar_service.delete_event(
                event_id=parameters.get("event_id")
            )
        else:
            raise ValueError(f"Unknown calendar action: {action}")
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
        return result
        
    except Exception as e:
        logger.error(f"Calendar task execution failed: {e}")
        self.update_state(
            state="FAILURE",
            meta={"error": str(e), "progress": 0}
        )
        raise


class TaskQueue:
    """Task queue manager for async task execution"""
    
    def __init__(self):
        self.celery = celery_app
    
    async def submit_script_task(
        self,
        script_content: str,
        parameters: Dict[str, Any],
        security_level: str = "medium",
        user_id: Optional[str] = None
    ) -> str:
        """Submit a Python script task for execution"""
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "script_content": script_content,
            "parameters": parameters,
            "security_level": security_level,
            "user_id": user_id
        }
        
        result = execute_script_task.apply_async(args=[task_data], task_id=task_id)
        return result.id
    
    async def submit_email_task(
        self,
        action: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Submit an email automation task"""
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            "action": action,
            "parameters": parameters,
            "user_id": user_id
        }
        
        result = execute_email_task.apply_async(args=[task_data], task_id=task_id)
        return result.id
    
    async def submit_file_task(
        self,
        operation: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Submit a file operation task"""
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            "operation": operation,
            "parameters": parameters,
            "user_id": user_id
        }
        
        result = execute_file_task.apply_async(args=[task_data], task_id=task_id)
        return result.id
    
    async def submit_app_control_task(
        self,
        action: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Submit an application control task"""
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            "action": action,
            "parameters": parameters,
            "user_id": user_id
        }
        
        result = execute_app_control_task.apply_async(args=[task_data], task_id=task_id)
        return result.id
    
    async def submit_calendar_task(
        self,
        action: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Submit a calendar management task"""
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            "action": action,
            "parameters": parameters,
            "user_id": user_id
        }
        
        result = execute_calendar_task.apply_async(args=[task_data], task_id=task_id)
        return result.id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task"""
        result = AsyncResult(task_id, app=self.celery)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "progress": result.info.get("progress", 0) if result.info else 0,
            "result": result.result if result.successful() else None,
            "error": result.info.get("error") if result.failed() else None
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        self.celery.control.revoke(task_id, terminate=True)
        return True


# Global task queue instance
task_queue = TaskQueue() 