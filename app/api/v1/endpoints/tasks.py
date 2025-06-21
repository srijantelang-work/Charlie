"""
Task management endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi import status as http_status  # Fix the import using an alias
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_current_user
from app.services.tasks.task_queue import task_queue
from app.services.tasks.execution_engine import task_executor

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Define task types
class TaskType(str, Enum):
    DATA_PROCESSING = "data_processing"
    NOTIFICATION = "notification" 
    FILE_OPERATION = "file_operation"
    SYNC = "sync"


@router.post("/execute", response_model=dict)
@limiter.limit("20/minute")
async def execute_task(
    request: Request,  # Add request parameter for rate limiting
    task_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute a task based on the provided data"""
    try:
        task_type = task_data.get("task_type")
        task_params = task_data.get("parameters", {})
        user_id = current_user.get("id")
        
        # Route to appropriate task handler
        if task_type == "python_script":
            task_id = await task_queue.submit_script_task(
                script_content=task_params.get("script"),
                parameters=task_params.get("script_params", {}),
                security_level=task_params.get("security_level", "medium"),
                user_id=user_id
            )
        elif task_type == "email":
            task_id = await task_queue.submit_email_task(
                action=task_params.get("action", "send"),
                parameters=task_params,
                user_id=user_id
            )
        elif task_type == "file_operation":
            task_id = await task_queue.submit_file_task(
                operation=task_params.get("operation"),
                parameters=task_params,
                user_id=user_id
            )
        elif task_type == "app_control":
            task_id = await task_queue.submit_app_control_task(
                action=task_params.get("action"),
                parameters=task_params,
                user_id=user_id
            )
        elif task_type == "calendar":
            task_id = await task_queue.submit_calendar_task(
                action=task_params.get("action"),
                parameters=task_params,
                user_id=user_id
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        
        return {
            "success": True,
            "task_id": task_id,
            "task_type": task_type,
            "status": "queued",
            "message": f"Task {task_type} queued for execution"
        }
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get status of a specific task"""
    try:
        # Get task status from queue
        status = task_queue.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}"
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/list")
async def list_user_tasks(
    status: str = Query(None, description="Filter tasks by status"),
    limit: int = Query(10, ge=1, le=100, description="Number of tasks to return"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List tasks for the current user"""
    try:
        # This would query tasks from database
        # Example implementation
        
        tasks = []
        for i in range(1, 4):
            tasks.append({
                "task_id": f"task_{i}",
                "task_type": "data_processing",
                "status": "completed",
                "created_at": "2023-04-01T12:00:00Z",
                "completed_at": "2023-04-01T12:02:00Z"
            })
            
        return {
            "tasks": tasks,
            "total": len(tasks),
            "limit": limit,
            "status_filter": status
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Cancel a running task"""
    try:
        # Cancel the task
        cancelled = task_queue.cancel_task(task_id)
        
        if not cancelled:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Task not found or cannot be cancelled: {task_id}"
            )
        
        return {
            "message": f"Task {task_id} cancelled successfully",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.post("/batch", response_model=dict)
@limiter.limit("10/minute")
async def batch_execute_tasks(
    request: Request,  # Add request parameter for rate limiting
    tasks: List[dict],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Execute multiple tasks in batch"""
    try:
        batch_id = "batch_123"  # Would be generated in real implementation
        
        # This would process each task in the batch
        # Example implementation
        
        processed = []
        for i, task in enumerate(tasks):
            processed.append({
                "task_id": f"task_{i+1}",
                "status": "queued",
                "task_type": task.get("task_type")
            })
            
        return {
            "batch_id": batch_id,
            "submitted_tasks": len(tasks),
            "processed_tasks": processed,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Batch task execution failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch task execution failed: {str(e)}"
        )


@router.get("/history")
async def get_task_history(
    limit: int = Query(10, ge=1, le=50),
    task_type: Optional[TaskType] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get task execution history"""
    try:
        user_id = current_user["id"]
        
        # This would query task history from database
        # For now, return mock history
        
        tasks = [
            {
                "id": "task-1",
                "task_type": "email",
                "status": "completed",
                "started_at": "2024-01-01T00:00:00Z",
                "completed_at": "2024-01-01T00:01:00Z",
                "success": True
            }
        ]
        
        return {
            "tasks": tasks,
            "total": len(tasks),
            "limit": limit,
            "task_type_filter": task_type
        }
        
    except Exception as e:
        logger.error(f"Task history retrieval failed: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task history retrieval failed: {str(e)}"
        )


@router.get("/types")
async def get_task_types():
    """Get available task types"""
    # This would return supported task types
    return {
        "task_types": [
            "data_processing", 
            "notification", 
            "file_operation", 
            "sync"
        ],
        "total": 4
    }


# Task execution functions (placeholders)
async def _execute_email_task(parameters: dict, user_id: str) -> dict:
    """Execute email-related task"""
    action = parameters.get("action", "send")
    
    if action == "send":
        return {
            "action": "send",
            "to": parameters.get("to"),
            "subject": parameters.get("subject"),
            "status": "sent",
            "message_id": "mock-message-id"
        }
    else:
        return {"action": action, "status": "completed"}


async def _execute_calendar_task(parameters: dict, user_id: str) -> dict:
    """Execute calendar-related task"""
    action = parameters.get("action", "create_event")
    
    if action == "create_event":
        return {
            "action": "create_event",
            "title": parameters.get("title"),
            "start_time": parameters.get("start_time"),
            "event_id": "mock-event-id",
            "status": "created"
        }
    else:
        return {"action": action, "status": "completed"}


async def _execute_file_task(parameters: dict, user_id: str) -> dict:
    """Execute file operation task"""
    action = parameters.get("action", "create")
    path = parameters.get("path", "")
    
    return {
        "action": action,
        "path": path,
        "status": "completed",
        "size": 1024 if action == "create" else None
    }


async def _execute_app_control_task(parameters: dict, user_id: str) -> dict:
    """Execute app control task"""
    action = parameters.get("action", "launch")
    app_name = parameters.get("app_name", "")
    
    return {
        "action": action,
        "app_name": app_name,
        "status": "completed",
        "pid": 12345 if action == "launch" else None
    } 