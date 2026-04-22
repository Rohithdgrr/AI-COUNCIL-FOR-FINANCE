"""
Comprehensive Background Task Scheduler for Real-Time Data Ingestion

Manages continuous data collection from multiple sources with proper
lifecycle management, error handling, and WebSocket broadcasting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class TaskMetrics:
    """Metrics for a scheduled task."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run_at: Optional[datetime] = None
    last_run_duration: float = 0.0
    last_error: Optional[str] = None
    success_rate: float = 0.0
    
    def update_run(self, duration: float, success: bool, error: str = None):
        """Update metrics after task execution."""
        self.total_runs += 1
        self.last_run_at = datetime.now()
        self.last_run_duration = duration
        
        if success:
            self.successful_runs += 1
            self.last_error = None
        else:
            self.failed_runs += 1
            self.last_error = error
        
        self.success_rate = (
            (self.successful_runs / self.total_runs * 100)
            if self.total_runs > 0
            else 0
        )


class BackgroundTask(ABC):
    """Base class for background tasks."""
    
    def __init__(
        self,
        name: str,
        interval_seconds: int,
        enabled: bool = True,
        priority: int = 50,
    ):
        self.name = name
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.priority = priority  # Higher = runs first (0-100)
        self.metrics = TaskMetrics()
        self.status = TaskStatus.IDLE
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Execute the task. Return dict with results or error info."""
        pass
    
    async def run_with_metrics(self) -> Dict[str, Any]:
        """Execute task and track metrics."""
        import time
        
        if not self.enabled:
            return {"status": "skipped", "reason": "task disabled"}
        
        self.status = TaskStatus.RUNNING
        start_time = time.time()
        result = None
        
        try:
            result = await self.execute()
            duration = time.time() - start_time
            self.metrics.update_run(duration, True)
            self.status = TaskStatus.COMPLETED
            
            logger.info(
                f"Task {self.name} completed in {duration:.2f}s",
                extra={"task": self.name, "duration": duration}
            )
            return {"status": "success", "data": result, "duration": duration}
        
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.metrics.update_run(duration, False, error_msg)
            self.status = TaskStatus.FAILED
            
            logger.error(
                f"Task {self.name} failed: {error_msg}",
                extra={"task": self.name, "error": error_msg},
                exc_info=True
            )
            return {"status": "error", "error": error_msg, "duration": duration}


class TaskScheduler:
    """Manages a collection of background tasks with scheduling."""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        self.shutdown_event = asyncio.Event()
    
    def register_task(self, task: BackgroundTask) -> None:
        """Register a background task."""
        if task.name in self.tasks:
            logger.warning(f"Task {task.name} already registered, overwriting")
        
        self.tasks[task.name] = task
        logger.info(f"Registered task: {task.name} (interval: {task.interval_seconds}s)")
    
    def register_tasks(self, tasks: List[BackgroundTask]) -> None:
        """Register multiple tasks."""
        for task in tasks:
            self.register_task(task)
    
    async def start(self) -> None:
        """Start the scheduler and all registered tasks."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        logger.info(f"Starting scheduler with {len(self.tasks)} tasks")
        
        # Sort tasks by priority (higher first)
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: t.priority,
            reverse=True
        )
        
        # Create task runners for each task
        for task in sorted_tasks:
            task_runner = asyncio.create_task(self._run_task_loop(task))
            self.running_tasks[task.name] = task_runner
        
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler and cancel all running tasks."""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping scheduler...")
        
        # Cancel all running tasks
        for name, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.running_tasks.clear()
        logger.info("Scheduler stopped")
    
    async def _run_task_loop(self, task: BackgroundTask) -> None:
        """Run a single task in a loop."""
        logger.info(f"Starting task loop for {task.name}")
        
        while self.is_running:
            try:
                # Wait for next execution time
                await asyncio.sleep(task.interval_seconds)
                
                if not self.is_running:
                    break
                
                # Execute task with metrics
                result = await task.run_with_metrics()
                
                # Broadcast update via WebSocket if available
                await self._broadcast_task_update(task.name, result)
                
                # Dispatch webhook event if available
                await self._dispatch_webhook_event(task.name, result)
            
            except asyncio.CancelledError:
                logger.info(f"Task loop cancelled for {task.name}")
                break
            
            except Exception as e:
                logger.error(
                    f"Unexpected error in task loop for {task.name}: {e}",
                    exc_info=True
                )
    
    async def _broadcast_task_update(self, task_name: str, result: Dict[str, Any]) -> None:
        """Broadcast task update via WebSocket if available."""
        try:
            from backend.ws.events import emit_event, EventType, Topic
            
            # Only broadcast successful results
            if result.get("status") == "success":
                await emit_event(
                    EventType.INGEST_UPDATE if "ingest" in task_name.lower() else EventType.DATA_UPDATE,
                    {"task": task_name, "result": result},
                    Topic.DASHBOARD,
                )
        except ImportError:
            # WebSocket not available
            pass
        except Exception as e:
            logger.warning(f"Failed to broadcast task update: {e}")
    
    async def _dispatch_webhook_event(self, task_name: str, result: Dict[str, Any]) -> None:
        """Dispatch webhook event if dispatcher is available."""
        try:
            from backend.webhooks.event_dispatcher import get_webhook_dispatcher
            
            dispatcher = get_webhook_dispatcher()
            success = result.get("status") == "success"
            
            # Dispatch task completion webhook
            await dispatcher.dispatch_task_completion(task_name, result, success)
        
        except ImportError:
            # Webhook dispatcher not available
            pass
        except Exception as e:
            logger.warning(f"Failed to dispatch webhook event: {e}")
    
    def get_task_status(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a task."""
        task = self.tasks.get(task_name)
        if not task:
            return None
        
        return {
            "name": task.name,
            "enabled": task.enabled,
            "status": task.status.value,
            "interval_seconds": task.interval_seconds,
            "priority": task.priority,
            "metrics": {
                "total_runs": task.metrics.total_runs,
                "successful_runs": task.metrics.successful_runs,
                "failed_runs": task.metrics.failed_runs,
                "success_rate": round(task.metrics.success_rate, 2),
                "last_run_at": task.metrics.last_run_at.isoformat() if task.metrics.last_run_at else None,
                "last_run_duration": round(task.metrics.last_run_duration, 2),
                "last_error": task.metrics.last_error,
            },
        }
    
    def get_all_statuses(self) -> List[Dict[str, Any]]:
        """Get status of all tasks."""
        return [
            status
            for task_name in self.tasks.keys()
            if (status := self.get_task_status(task_name))
        ]
    
    def pause_task(self, task_name: str) -> bool:
        """Pause a task."""
        task = self.tasks.get(task_name)
        if not task:
            return False
        
        task.enabled = False
        task.status = TaskStatus.PAUSED
        logger.info(f"Task {task_name} paused")
        return True
    
    def resume_task(self, task_name: str) -> bool:
        """Resume a paused task."""
        task = self.tasks.get(task_name)
        if not task:
            return False
        
        task.enabled = True
        task.status = TaskStatus.IDLE
        logger.info(f"Task {task_name} resumed")
        return True


# Global scheduler instance
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    return _scheduler_instance
