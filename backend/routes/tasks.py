"""
Task Scheduler API Endpoints

Expose scheduler status, task management, and metrics.
Strategy #2: Background worker pipeline with monitoring.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from backend.tasks.scheduler import get_scheduler, TaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/scheduler/status")
async def get_scheduler_status() -> Dict[str, Any]:
    """Get overall scheduler status."""
    scheduler = get_scheduler()
    
    return {
        "running": scheduler.is_running,
        "total_tasks": len(scheduler.tasks),
        "running_tasks": len(
            [t for t in scheduler.running_tasks.values() if not t.done()]
        ),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/tasks/all")
async def list_all_tasks() -> List[Dict[str, Any]]:
    """List all registered tasks and their status."""
    scheduler = get_scheduler()
    return scheduler.get_all_statuses()


@router.get("/tasks/{task_name}")
async def get_task_status(task_name: str) -> Dict[str, Any]:
    """Get detailed status of a specific task."""
    scheduler = get_scheduler()
    status = scheduler.get_task_status(task_name)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    
    return status


@router.post("/tasks/{task_name}/pause")
async def pause_task(task_name: str) -> Dict[str, Any]:
    """Pause a background task."""
    scheduler = get_scheduler()
    
    if not scheduler.pause_task(task_name):
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    
    return {
        "message": f"Task '{task_name}' paused",
        "task_name": task_name,
        "status": TaskStatus.PAUSED.value,
    }


@router.post("/tasks/{task_name}/resume")
async def resume_task(task_name: str) -> Dict[str, Any]:
    """Resume a paused task."""
    scheduler = get_scheduler()
    
    if not scheduler.resume_task(task_name):
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    
    return {
        "message": f"Task '{task_name}' resumed",
        "task_name": task_name,
        "status": TaskStatus.IDLE.value,
    }


@router.get("/scheduler/metrics")
async def get_scheduler_metrics() -> Dict[str, Any]:
    """Get aggregated metrics across all tasks."""
    scheduler = get_scheduler()
    
    total_runs = 0
    total_successful = 0
    total_failed = 0
    avg_duration = 0.0
    
    durations = []
    
    for task in scheduler.tasks.values():
        metrics = task.metrics
        total_runs += metrics.total_runs
        total_successful += metrics.successful_runs
        total_failed += metrics.failed_runs
        durations.append(metrics.last_run_duration)
    
    if durations:
        avg_duration = sum(durations) / len(durations)
    
    return {
        "total_runs": total_runs,
        "successful": total_successful,
        "failed": total_failed,
        "success_rate": round(
            (total_successful / total_runs * 100) if total_runs > 0 else 0,
            2
        ),
        "average_task_duration": round(avg_duration, 2),
        "timestamp": datetime.now().isoformat(),
    }
