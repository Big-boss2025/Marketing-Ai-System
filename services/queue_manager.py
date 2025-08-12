"""
Queue Manager
مدير الطوابير

This module handles queuing of API requests and background tasks
to prevent overloading external services and manage high traffic.
"""

import os
import json
import time
import logging
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

from src.models.base import db

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class QueueTask:
    """Queue task data structure"""
    id: str
    task_type: str
    payload: Dict[str, Any]
    user_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
            elif isinstance(value, (TaskStatus, TaskPriority)):
                data[key] = value.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueueTask':
        """Create from dictionary"""
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'started_at', 'completed_at']:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key])
        
        # Convert enum values
        if 'status' in data:
            data['status'] = TaskStatus(data['status'])
        if 'priority' in data:
            data['priority'] = TaskPriority(data['priority'])
        
        return cls(**data)


class BaseQueueManager:
    """Base queue manager interface"""
    
    def add_task(self, task: QueueTask) -> bool:
        """Add task to queue"""
        raise NotImplementedError
    
    def get_task(self, timeout: Optional[int] = None) -> Optional[QueueTask]:
        """Get next task from queue"""
        raise NotImplementedError
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result: Optional[Dict] = None, 
                          error: Optional[str] = None) -> bool:
        """Update task status"""
        raise NotImplementedError
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status"""
        raise NotImplementedError
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        raise NotImplementedError
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        raise NotImplementedError


class MemoryQueueManager(BaseQueueManager):
    """In-memory queue manager for simple deployments"""
    
    def __init__(self):
        self.queues = {
            TaskPriority.URGENT: queue.PriorityQueue(),
            TaskPriority.HIGH: queue.PriorityQueue(),
            TaskPriority.NORMAL: queue.PriorityQueue(),
            TaskPriority.LOW: queue.PriorityQueue()
        }
        self.tasks = {}  # task_id -> QueueTask
        self.lock = threading.RLock()
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'pending_tasks': 0
        }
    
    def add_task(self, task: QueueTask) -> bool:
        """Add task to queue"""
        try:
            with self.lock:
                self.tasks[task.id] = task
                # Use negative timestamp for priority queue (earlier = higher priority)
                priority_value = (-task.priority.value, -time.time())
                self.queues[task.priority].put((priority_value, task.id))
                self.stats['total_tasks'] += 1
                self.stats['pending_tasks'] += 1
                
            logger.info(f"Added task {task.id} to queue with priority {task.priority.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add task to queue: {e}")
            return False
    
    def get_task(self, timeout: Optional[int] = None) -> Optional[QueueTask]:
        """Get next task from queue"""
        try:
            # Try queues in priority order
            for priority in [TaskPriority.URGENT, TaskPriority.HIGH, 
                           TaskPriority.NORMAL, TaskPriority.LOW]:
                try:
                    priority_value, task_id = self.queues[priority].get_nowait()
                    
                    with self.lock:
                        if task_id in self.tasks:
                            task = self.tasks[task_id]
                            if task.status == TaskStatus.PENDING:
                                task.status = TaskStatus.PROCESSING
                                task.started_at = datetime.utcnow()
                                self.stats['pending_tasks'] -= 1
                                return task
                    
                except queue.Empty:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task from queue: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus,
                          result: Optional[Dict] = None,
                          error: Optional[str] = None) -> bool:
        """Update task status"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    return False
                
                task = self.tasks[task_id]
                old_status = task.status
                task.status = status
                
                if status == TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
                    task.result = result
                    if old_status == TaskStatus.PROCESSING:
                        self.stats['completed_tasks'] += 1
                
                elif status == TaskStatus.FAILED:
                    task.completed_at = datetime.utcnow()
                    task.error = error
                    if old_status == TaskStatus.PROCESSING:
                        self.stats['failed_tasks'] += 1
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        try:
            with self.lock:
                if task_id not in self.tasks:
                    return False
                
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    self.stats['pending_tasks'] -= 1
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        with self.lock:
            queue_sizes = {}
            for priority, q in self.queues.items():
                queue_sizes[priority.name] = q.qsize()
            
            return {
                'queue_type': 'memory',
                'queue_sizes': queue_sizes,
                'stats': self.stats.copy()
            }


class RedisQueueManager(BaseQueueManager):
    """Redis-based queue manager for production deployments"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Redis queue manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        # Queue keys
        self.queue_keys = {
            TaskPriority.URGENT: 'queue:urgent',
            TaskPriority.HIGH: 'queue:high',
            TaskPriority.NORMAL: 'queue:normal',
            TaskPriority.LOW: 'queue:low'
        }
        self.task_key_prefix = 'task:'
        self.stats_key = 'queue:stats'
    
    def add_task(self, task: QueueTask) -> bool:
        """Add task to queue"""
        try:
            # Store task data
            task_key = f"{self.task_key_prefix}{task.id}"
            task_data = json.dumps(task.to_dict())
            self.redis_client.set(task_key, task_data)
            
            # Add to priority queue
            queue_key = self.queue_keys[task.priority]
            score = time.time()  # Use timestamp as score for FIFO within priority
            self.redis_client.zadd(queue_key, {task.id: score})
            
            # Update stats
            self.redis_client.hincrby(self.stats_key, 'total_tasks', 1)
            self.redis_client.hincrby(self.stats_key, 'pending_tasks', 1)
            
            logger.info(f"Added task {task.id} to Redis queue with priority {task.priority.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add task to Redis queue: {e}")
            return False
    
    def get_task(self, timeout: Optional[int] = None) -> Optional[QueueTask]:
        """Get next task from queue"""
        try:
            # Try queues in priority order
            for priority in [TaskPriority.URGENT, TaskPriority.HIGH,
                           TaskPriority.NORMAL, TaskPriority.LOW]:
                queue_key = self.queue_keys[priority]
                
                # Get oldest task from this priority queue
                result = self.redis_client.zpopmin(queue_key, count=1)
                if result:
                    task_id, score = result[0]
                    
                    # Get task data
                    task_key = f"{self.task_key_prefix}{task_id}"
                    task_data = self.redis_client.get(task_key)
                    
                    if task_data:
                        task_dict = json.loads(task_data)
                        task = QueueTask.from_dict(task_dict)
                        
                        # Update task status
                        task.status = TaskStatus.PROCESSING
                        task.started_at = datetime.utcnow()
                        
                        # Save updated task
                        updated_data = json.dumps(task.to_dict())
                        self.redis_client.set(task_key, updated_data)
                        
                        # Update stats
                        self.redis_client.hincrby(self.stats_key, 'pending_tasks', -1)
                        
                        return task
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task from Redis queue: {e}")
            return None
    
    def update_task_status(self, task_id: str, status: TaskStatus,
                          result: Optional[Dict] = None,
                          error: Optional[str] = None) -> bool:
        """Update task status"""
        try:
            task_key = f"{self.task_key_prefix}{task_id}"
            task_data = self.redis_client.get(task_key)
            
            if not task_data:
                return False
            
            task_dict = json.loads(task_data)
            task = QueueTask.from_dict(task_dict)
            
            old_status = task.status
            task.status = status
            
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.result = result
                if old_status == TaskStatus.PROCESSING:
                    self.redis_client.hincrby(self.stats_key, 'completed_tasks', 1)
            
            elif status == TaskStatus.FAILED:
                task.completed_at = datetime.utcnow()
                task.error = error
                if old_status == TaskStatus.PROCESSING:
                    self.redis_client.hincrby(self.stats_key, 'failed_tasks', 1)
            
            # Save updated task
            updated_data = json.dumps(task.to_dict())
            self.redis_client.set(task_key, updated_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task status in Redis: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[QueueTask]:
        """Get task status"""
        try:
            task_key = f"{self.task_key_prefix}{task_id}"
            task_data = self.redis_client.get(task_key)
            
            if task_data:
                task_dict = json.loads(task_data)
                return QueueTask.from_dict(task_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task status from Redis: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        try:
            task_key = f"{self.task_key_prefix}{task_id}"
            task_data = self.redis_client.get(task_key)
            
            if not task_data:
                return False
            
            task_dict = json.loads(task_data)
            task = QueueTask.from_dict(task_dict)
            
            if task.status == TaskStatus.PENDING:
                # Remove from queue
                queue_key = self.queue_keys[task.priority]
                self.redis_client.zrem(queue_key, task_id)
                
                # Update task status
                task.status = TaskStatus.CANCELLED
                updated_data = json.dumps(task.to_dict())
                self.redis_client.set(task_key, updated_data)
                
                # Update stats
                self.redis_client.hincrby(self.stats_key, 'pending_tasks', -1)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task in Redis: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        try:
            queue_sizes = {}
            for priority, queue_key in self.queue_keys.items():
                queue_sizes[priority.name] = self.redis_client.zcard(queue_key)
            
            stats = self.redis_client.hgetall(self.stats_key)
            # Convert string values to integers
            stats = {k: int(v) for k, v in stats.items()}
            
            return {
                'queue_type': 'redis',
                'queue_sizes': queue_sizes,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats from Redis: {e}")
            return {'error': str(e)}


class QueueWorker:
    """Queue worker for processing tasks"""
    
    def __init__(self, queue_manager: BaseQueueManager, task_handlers: Dict[str, Callable]):
        self.queue_manager = queue_manager
        self.task_handlers = task_handlers
        self.running = False
        self.worker_thread = None
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register task handler"""
        self.task_handlers[task_type] = handler
    
    def start(self):
        """Start worker"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Queue worker started")
    
    def stop(self):
        """Stop worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Queue worker stopped")
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                task = self.queue_manager.get_task(timeout=1)
                if task:
                    self._process_task(task)
                else:
                    time.sleep(0.1)  # Brief pause if no tasks
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)
    
    def _process_task(self, task: QueueTask):
        """Process a single task"""
        try:
            logger.info(f"Processing task {task.id} of type {task.task_type}")
            
            if task.task_type not in self.task_handlers:
                error_msg = f"No handler registered for task type: {task.task_type}"
                logger.error(error_msg)
                self.queue_manager.update_task_status(
                    task.id, TaskStatus.FAILED, error=error_msg
                )
                return
            
            handler = self.task_handlers[task.task_type]
            result = handler(task.payload)
            
            self.queue_manager.update_task_status(
                task.id, TaskStatus.COMPLETED, result=result
            )
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            error_msg = f"Task processing failed: {str(e)}"
            logger.error(error_msg)
            
            # Handle retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                self.queue_manager.add_task(task)
                logger.info(f"Task {task.id} queued for retry ({task.retry_count}/{task.max_retries})")
            else:
                self.queue_manager.update_task_status(
                    task.id, TaskStatus.FAILED, error=error_msg
                )


class QueueManager:
    """Main queue manager that chooses the appropriate backend"""
    
    def __init__(self, queue_type: str = "auto", redis_url: Optional[str] = None):
        self.queue_type = queue_type
        
        if queue_type == "redis" or (queue_type == "auto" and REDIS_AVAILABLE):
            try:
                self.backend = RedisQueueManager(redis_url)
                self.queue_type = "redis"
            except Exception as e:
                if queue_type == "redis":
                    raise
                logger.warning(f"Failed to initialize Redis queue, falling back to memory: {e}")
                self.backend = MemoryQueueManager()
                self.queue_type = "memory"
        else:
            self.backend = MemoryQueueManager()
            self.queue_type = "memory"
        
        logger.info(f"Queue manager initialized with {self.queue_type} backend")
    
    def add_task(self, task_type: str, payload: Dict[str, Any], 
                user_id: Optional[int] = None, 
                priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Add task to queue and return task ID"""
        task = QueueTask(
            id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            user_id=user_id,
            priority=priority
        )
        
        if self.backend.add_task(task):
            return task.id
        else:
            raise Exception("Failed to add task to queue")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        task = self.backend.get_task_status(task_id)
        return task.to_dict() if task else None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel task"""
        return self.backend.cancel_task(task_id)
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return self.backend.get_queue_stats()
    
    def create_worker(self, task_handlers: Dict[str, Callable]) -> QueueWorker:
        """Create queue worker"""
        return QueueWorker(self.backend, task_handlers)


# Global queue manager instance
queue_manager = QueueManager(
    queue_type=os.getenv('QUEUE_TYPE', 'auto'),
    redis_url=os.getenv('REDIS_URL')
)

