import os
import json
import redis
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
from dataclasses import dataclass, asdict
from src.models.base import db
from src.models.task import Task
from src.models.user import User

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class QueueTask:
    id: str
    user_id: str
    task_type: str
    data: Dict[str, Any]
    priority: int = TaskPriority.NORMAL.value
    status: str = TaskStatus.PENDING.value
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

class TaskQueueManager:
    """Advanced task queue manager with Redis backend"""
    
    def __init__(self):
        # Redis connection
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        
        # Queue names
        self.queues = {
            TaskPriority.URGENT.value: 'queue:urgent',
            TaskPriority.HIGH.value: 'queue:high',
            TaskPriority.NORMAL.value: 'queue:normal',
            TaskPriority.LOW.value: 'queue:low'
        }
        
        # Task processors
        self.processors = {}
        
        # Worker settings
        self.max_workers = int(os.getenv('MAX_WORKERS', 4))
        self.worker_timeout = int(os.getenv('WORKER_TIMEOUT', 300))  # 5 minutes
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_retried': 0,
            'average_processing_time': 0
        }
        
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis with required keys"""
        try:
            # Test connection
            self.redis_client.ping()
            
            # Initialize counters if they don't exist
            if not self.redis_client.exists('stats:total_processed'):
                self.redis_client.set('stats:total_processed', 0)
            if not self.redis_client.exists('stats:total_failed'):
                self.redis_client.set('stats:total_failed', 0)
            if not self.redis_client.exists('stats:total_retried'):
                self.redis_client.set('stats:total_retried', 0)
            
            logger.info("Redis connection established successfully")
        
        except redis.ConnectionError:
            logger.warning("Redis not available, falling back to in-memory queue")
            self.redis_client = None
    
    def register_processor(self, task_type: str, processor_func: Callable):
        """Register a task processor function"""
        self.processors[task_type] = processor_func
        logger.info(f"Registered processor for task type: {task_type}")
    
    async def add_task(self, task: QueueTask) -> bool:
        """Add task to appropriate priority queue"""
        try:
            task_data = asdict(task)
            task_data['created_at'] = task.created_at.isoformat()
            
            if self.redis_client:
                # Add to Redis queue
                queue_name = self.queues[task.priority]
                self.redis_client.lpush(queue_name, json.dumps(task_data))
                
                # Store task details
                self.redis_client.hset(f"task:{task.id}", mapping=task_data)
                
                # Add to user's task list
                self.redis_client.sadd(f"user_tasks:{task.user_id}", task.id)
            else:
                # Fallback to database
                db_task = Task(
                    id=task.id,
                    user_id=task.user_id,
                    title=f"Queue Task: {task.task_type}",
                    description=json.dumps(task.data),
                    task_type=task.task_type,
                    status=task.status,
                    priority=task.priority
                )
                db_task.save()
            
            logger.info(f"Task {task.id} added to queue with priority {task.priority}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add task to queue: {str(e)}")
            return False
    
    async def get_next_task(self) -> Optional[QueueTask]:
        """Get next task from highest priority queue"""
        try:
            if not self.redis_client:
                return await self._get_next_task_from_db()
            
            # Check queues in priority order
            for priority in sorted(self.queues.keys(), reverse=True):
                queue_name = self.queues[priority]
                task_data = self.redis_client.rpop(queue_name)
                
                if task_data:
                    task_dict = json.loads(task_data)
                    task_dict['created_at'] = datetime.fromisoformat(task_dict['created_at'])
                    
                    if task_dict.get('started_at'):
                        task_dict['started_at'] = datetime.fromisoformat(task_dict['started_at'])
                    if task_dict.get('completed_at'):
                        task_dict['completed_at'] = datetime.fromisoformat(task_dict['completed_at'])
                    
                    return QueueTask(**task_dict)
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get next task: {str(e)}")
            return None
    
    async def _get_next_task_from_db(self) -> Optional[QueueTask]:
        """Fallback method to get task from database"""
        try:
            db_task = Task.query.filter_by(
                status=TaskStatus.PENDING.value
            ).order_by(
                Task.priority.desc(),
                Task.created_at.asc()
            ).first()
            
            if db_task:
                task_data = json.loads(db_task.description) if db_task.description else {}
                
                return QueueTask(
                    id=db_task.id,
                    user_id=db_task.user_id,
                    task_type=db_task.task_type,
                    data=task_data,
                    priority=db_task.priority,
                    status=db_task.status,
                    created_at=db_task.created_at
                )
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get task from database: {str(e)}")
            return None
    
    async def update_task_status(self, task_id: str, status: TaskStatus, 
                                result: Optional[Dict] = None, 
                                error_message: Optional[str] = None):
        """Update task status and result"""
        try:
            if self.redis_client:
                # Update Redis
                updates = {
                    'status': status.value,
                    'completed_at': datetime.utcnow().isoformat()
                }
                
                if result:
                    updates['result'] = json.dumps(result)
                if error_message:
                    updates['error_message'] = error_message
                
                self.redis_client.hmset(f"task:{task_id}", updates)
            
            # Update database
            db_task = Task.query.get(task_id)
            if db_task:
                db_task.status = status.value
                db_task.completed_at = datetime.utcnow()
                
                if result:
                    db_task.set_output_data(result)
                if error_message:
                    db_task.error_message = error_message
                
                db_task.save()
            
            logger.info(f"Task {task_id} status updated to {status.value}")
        
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
    
    async def retry_task(self, task: QueueTask) -> bool:
        """Retry a failed task"""
        try:
            if task.retry_count >= task.max_retries:
                await self.update_task_status(
                    task.id, 
                    TaskStatus.FAILED, 
                    error_message="Max retries exceeded"
                )
                return False
            
            # Increment retry count
            task.retry_count += 1
            task.status = TaskStatus.RETRYING.value
            task.error_message = None
            
            # Add back to queue with delay
            await asyncio.sleep(min(task.retry_count * 30, 300))  # Exponential backoff
            await self.add_task(task)
            
            if self.redis_client:
                self.redis_client.incr('stats:total_retried')
            
            logger.info(f"Task {task.id} retried (attempt {task.retry_count})")
            return True
        
        except Exception as e:
            logger.error(f"Failed to retry task: {str(e)}")
            return False
    
    async def process_task(self, task: QueueTask) -> Dict[str, Any]:
        """Process a single task"""
        try:
            # Update status to processing
            task.status = TaskStatus.PROCESSING.value
            task.started_at = datetime.utcnow()
            
            await self.update_task_status(task.id, TaskStatus.PROCESSING)
            
            # Get processor for task type
            processor = self.processors.get(task.task_type)
            if not processor:
                raise Exception(f"No processor registered for task type: {task.task_type}")
            
            # Process task
            start_time = datetime.utcnow()
            result = await processor(task.data)
            end_time = datetime.utcnow()
            
            processing_time = (end_time - start_time).total_seconds()
            
            if result.get('success', False):
                await self.update_task_status(task.id, TaskStatus.COMPLETED, result)
                
                # Update statistics
                if self.redis_client:
                    self.redis_client.incr('stats:total_processed')
                    
                    # Update average processing time
                    current_avg = float(self.redis_client.get('stats:avg_processing_time') or 0)
                    total_processed = int(self.redis_client.get('stats:total_processed'))
                    new_avg = ((current_avg * (total_processed - 1)) + processing_time) / total_processed
                    self.redis_client.set('stats:avg_processing_time', new_avg)
                
                logger.info(f"Task {task.id} completed successfully in {processing_time:.2f}s")
                return result
            else:
                # Task failed, try to retry
                task.error_message = result.get('error', 'Unknown error')
                
                if await self.retry_task(task):
                    return {'success': False, 'retrying': True}
                else:
                    if self.redis_client:
                        self.redis_client.incr('stats:total_failed')
                    
                    logger.error(f"Task {task.id} failed permanently: {task.error_message}")
                    return result
        
        except Exception as e:
            error_message = str(e)
            task.error_message = error_message
            
            # Try to retry
            if await self.retry_task(task):
                return {'success': False, 'retrying': True, 'error': error_message}
            else:
                await self.update_task_status(task.id, TaskStatus.FAILED, error_message=error_message)
                
                if self.redis_client:
                    self.redis_client.incr('stats:total_failed')
                
                logger.error(f"Task {task.id} failed with exception: {error_message}")
                return {'success': False, 'error': error_message}
    
    async def start_worker(self, worker_id: str):
        """Start a worker to process tasks"""
        logger.info(f"Starting worker {worker_id}")
        
        while True:
            try:
                # Get next task
                task = await self.get_next_task()
                
                if task:
                    logger.info(f"Worker {worker_id} processing task {task.id}")
                    await self.process_task(task)
                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
                await asyncio.sleep(10)
    
    async def start_workers(self):
        """Start multiple workers"""
        workers = []
        
        for i in range(self.max_workers):
            worker_id = f"worker_{i+1}"
            worker = asyncio.create_task(self.start_worker(worker_id))
            workers.append(worker)
        
        logger.info(f"Started {self.max_workers} workers")
        
        # Wait for all workers
        await asyncio.gather(*workers)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            if not self.redis_client:
                return {'error': 'Redis not available'}
            
            stats = {}
            
            # Queue lengths
            for priority, queue_name in self.queues.items():
                stats[f'queue_{priority}_length'] = self.redis_client.llen(queue_name)
            
            # Processing statistics
            stats['total_processed'] = int(self.redis_client.get('stats:total_processed') or 0)
            stats['total_failed'] = int(self.redis_client.get('stats:total_failed') or 0)
            stats['total_retried'] = int(self.redis_client.get('stats:total_retried') or 0)
            stats['avg_processing_time'] = float(self.redis_client.get('stats:avg_processing_time') or 0)
            
            # Active workers (approximate)
            stats['active_workers'] = len(self.redis_client.keys('worker:*:heartbeat'))
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {'error': str(e)}
    
    def get_user_tasks(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get tasks for a specific user"""
        try:
            if self.redis_client:
                task_ids = self.redis_client.smembers(f"user_tasks:{user_id}")
                tasks = []
                
                for task_id in task_ids:
                    task_data = self.redis_client.hgetall(f"task:{task_id}")
                    if task_data and (not status or task_data.get('status') == status):
                        tasks.append(task_data)
                
                return tasks
            else:
                # Fallback to database
                query = Task.query.filter_by(user_id=user_id)
                if status:
                    query = query.filter_by(status=status)
                
                db_tasks = query.all()
                return [task.to_dict() for task in db_tasks]
        
        except Exception as e:
            logger.error(f"Failed to get user tasks: {str(e)}")
            return []
    
    async def cancel_task(self, task_id: str, user_id: str) -> bool:
        """Cancel a pending task"""
        try:
            if self.redis_client:
                task_data = self.redis_client.hgetall(f"task:{task_id}")
                
                if not task_data:
                    return False
                
                if task_data.get('user_id') != user_id:
                    return False
                
                if task_data.get('status') not in [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]:
                    return False
                
                # Update status
                await self.update_task_status(task_id, TaskStatus.CANCELLED)
                
                # Remove from queues
                for queue_name in self.queues.values():
                    # This is inefficient but necessary for Redis lists
                    # In production, consider using a different data structure
                    pass
            
            # Update database
            db_task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            if db_task and db_task.status in [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]:
                db_task.status = TaskStatus.CANCELLED.value
                db_task.save()
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to cancel task: {str(e)}")
            return False
    
    def cleanup_completed_tasks(self, days_old: int = 7):
        """Clean up old completed tasks"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            if self.redis_client:
                # Get all task keys
                task_keys = self.redis_client.keys('task:*')
                
                for key in task_keys:
                    task_data = self.redis_client.hgetall(key)
                    
                    if task_data.get('status') in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                        completed_at = task_data.get('completed_at')
                        if completed_at:
                            completed_date = datetime.fromisoformat(completed_at)
                            if completed_date < cutoff_date:
                                task_id = key.split(':')[1]
                                user_id = task_data.get('user_id')
                                
                                # Remove from Redis
                                self.redis_client.delete(key)
                                if user_id:
                                    self.redis_client.srem(f"user_tasks:{user_id}", task_id)
            
            # Clean up database
            Task.query.filter(
                Task.status.in_([TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]),
                Task.completed_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up tasks older than {days_old} days")
        
        except Exception as e:
            logger.error(f"Failed to cleanup tasks: {str(e)}")

# Global task queue manager
task_queue = TaskQueueManager()

