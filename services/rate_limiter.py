"""
Rate Limiter
محدد المعدل

This module handles rate limiting for API requests to prevent abuse
and ensure fair usage of external services.
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from functools import wraps
from flask import request, jsonify, g
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.models.base import db
from src.models.user import User

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """Rate limiter with multiple storage backends"""
    
    def __init__(self, storage_type: str = "auto", redis_url: Optional[str] = None):
        self.storage_type = storage_type
        self.redis_client = None
        self.memory_store = {}  # For in-memory storage
        
        # Initialize storage backend
        if storage_type == "redis" or (storage_type == "auto" and REDIS_AVAILABLE):
            try:
                if not redis_url:
                    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.storage_type = "redis"
                logger.info("Redis rate limiter initialized")
                
            except Exception as e:
                if storage_type == "redis":
                    raise
                logger.warning(f"Failed to initialize Redis, using memory storage: {e}")
                self.storage_type = "memory"
        else:
            self.storage_type = "memory"
            logger.info("Memory rate limiter initialized")
    
    def _get_key(self, identifier: str, window: str) -> str:
        """Generate storage key"""
        return f"rate_limit:{identifier}:{window}"
    
    def _get_current_window(self, window_size: int) -> int:
        """Get current time window"""
        return int(time.time()) // window_size
    
    def _cleanup_memory_store(self):
        """Clean up expired entries from memory store"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.memory_store.items():
            if current_time - data.get('timestamp', 0) > 3600:  # 1 hour cleanup
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_store[key]
    
    def check_rate_limit(self, identifier: str, limit: int, window: int = 60) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        try:
            current_window = self._get_current_window(window)
            key = self._get_key(identifier, str(current_window))
            
            if self.storage_type == "redis" and self.redis_client:
                # Redis implementation
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
                
                if current_count >= limit:
                    return False, {
                        'allowed': False,
                        'limit': limit,
                        'remaining': 0,
                        'reset_time': (current_window + 1) * window,
                        'retry_after': window - (int(time.time()) % window)
                    }
                
                # Increment counter
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                pipe.execute()
                
                return True, {
                    'allowed': True,
                    'limit': limit,
                    'remaining': limit - current_count - 1,
                    'reset_time': (current_window + 1) * window,
                    'retry_after': 0
                }
            
            else:
                # Memory implementation
                self._cleanup_memory_store()
                
                if key not in self.memory_store:
                    self.memory_store[key] = {
                        'count': 0,
                        'timestamp': time.time()
                    }
                
                data = self.memory_store[key]
                current_count = data['count']
                
                if current_count >= limit:
                    return False, {
                        'allowed': False,
                        'limit': limit,
                        'remaining': 0,
                        'reset_time': (current_window + 1) * window,
                        'retry_after': window - (int(time.time()) % window)
                    }
                
                # Increment counter
                data['count'] += 1
                
                return True, {
                    'allowed': True,
                    'limit': limit,
                    'remaining': limit - current_count - 1,
                    'reset_time': (current_window + 1) * window,
                    'retry_after': 0
                }
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - 1,
                'error': str(e)
            }
    
    def get_rate_limit_info(self, identifier: str, limit: int, window: int = 60) -> Dict:
        """Get current rate limit info without incrementing"""
        try:
            current_window = self._get_current_window(window)
            key = self._get_key(identifier, str(current_window))
            
            if self.storage_type == "redis" and self.redis_client:
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
            else:
                self._cleanup_memory_store()
                data = self.memory_store.get(key, {'count': 0})
                current_count = data['count']
            
            return {
                'limit': limit,
                'remaining': max(0, limit - current_count),
                'reset_time': (current_window + 1) * window,
                'retry_after': window - (int(time.time()) % window) if current_count >= limit else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {
                'limit': limit,
                'remaining': limit,
                'error': str(e)
            }
    
    def reset_rate_limit(self, identifier: str, window: int = 60) -> bool:
        """Reset rate limit for identifier"""
        try:
            current_window = self._get_current_window(window)
            key = self._get_key(identifier, str(current_window))
            
            if self.storage_type == "redis" and self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self.memory_store:
                    del self.memory_store[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False


class RateLimitManager:
    """Manager for different types of rate limits"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        
        # Default rate limits
        self.default_limits = {
            'global': {'limit': 1000, 'window': 3600},  # 1000 requests per hour
            'per_user': {'limit': 100, 'window': 3600},  # 100 requests per hour per user
            'per_ip': {'limit': 200, 'window': 3600},    # 200 requests per hour per IP
            'api_generation': {'limit': 50, 'window': 3600},  # 50 generations per hour
            'expensive_operations': {'limit': 10, 'window': 3600}  # 10 expensive ops per hour
        }
    
    def get_user_identifier(self, user_id: Optional[int] = None) -> str:
        """Get user identifier for rate limiting"""
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        ip_address = self.get_client_ip()
        return f"ip:{ip_address}"
    
    def get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded IP first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def check_global_rate_limit(self) -> Tuple[bool, Dict]:
        """Check global rate limit"""
        config = self.default_limits['global']
        return self.rate_limiter.check_rate_limit(
            'global', config['limit'], config['window']
        )
    
    def check_user_rate_limit(self, user_id: Optional[int] = None) -> Tuple[bool, Dict]:
        """Check per-user rate limit"""
        identifier = self.get_user_identifier(user_id)
        config = self.default_limits['per_user']
        return self.rate_limiter.check_rate_limit(
            identifier, config['limit'], config['window']
        )
    
    def check_ip_rate_limit(self) -> Tuple[bool, Dict]:
        """Check per-IP rate limit"""
        ip_address = self.get_client_ip()
        identifier = f"ip:{ip_address}"
        config = self.default_limits['per_ip']
        return self.rate_limiter.check_rate_limit(
            identifier, config['limit'], config['window']
        )
    
    def check_api_generation_limit(self, user_id: Optional[int] = None) -> Tuple[bool, Dict]:
        """Check API generation rate limit"""
        identifier = f"{self.get_user_identifier(user_id)}:generation"
        config = self.default_limits['api_generation']
        return self.rate_limiter.check_rate_limit(
            identifier, config['limit'], config['window']
        )
    
    def check_expensive_operation_limit(self, user_id: Optional[int] = None) -> Tuple[bool, Dict]:
        """Check expensive operation rate limit"""
        identifier = f"{self.get_user_identifier(user_id)}:expensive"
        config = self.default_limits['expensive_operations']
        return self.rate_limiter.check_rate_limit(
            identifier, config['limit'], config['window']
        )
    
    def check_custom_rate_limit(self, identifier: str, limit: int, window: int = 60) -> Tuple[bool, Dict]:
        """Check custom rate limit"""
        return self.rate_limiter.check_rate_limit(identifier, limit, window)
    
    def get_all_rate_limit_info(self, user_id: Optional[int] = None) -> Dict:
        """Get all rate limit information for user"""
        info = {}
        
        # Global limit
        global_config = self.default_limits['global']
        info['global'] = self.rate_limiter.get_rate_limit_info(
            'global', global_config['limit'], global_config['window']
        )
        
        # User limit
        user_identifier = self.get_user_identifier(user_id)
        user_config = self.default_limits['per_user']
        info['user'] = self.rate_limiter.get_rate_limit_info(
            user_identifier, user_config['limit'], user_config['window']
        )
        
        # IP limit
        ip_address = self.get_client_ip()
        ip_identifier = f"ip:{ip_address}"
        ip_config = self.default_limits['per_ip']
        info['ip'] = self.rate_limiter.get_rate_limit_info(
            ip_identifier, ip_config['limit'], ip_config['window']
        )
        
        # API generation limit
        gen_identifier = f"{user_identifier}:generation"
        gen_config = self.default_limits['api_generation']
        info['api_generation'] = self.rate_limiter.get_rate_limit_info(
            gen_identifier, gen_config['limit'], gen_config['window']
        )
        
        return info


# Global instances
rate_limiter = RateLimiter(
    storage_type=os.getenv('RATE_LIMIT_STORAGE', 'auto'),
    redis_url=os.getenv('REDIS_URL')
)
rate_limit_manager = RateLimitManager(rate_limiter)


def rate_limit(limit_type: str = 'per_user', custom_limit: Optional[int] = None, 
               custom_window: Optional[int] = None):
    """
    Decorator for rate limiting Flask routes
    
    Args:
        limit_type: Type of rate limit ('global', 'per_user', 'per_ip', 'api_generation', 'expensive', 'custom')
        custom_limit: Custom limit for 'custom' type
        custom_window: Custom window for 'custom' type
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = getattr(g, 'current_user_id', None)
                
                # Check appropriate rate limit
                if limit_type == 'global':
                    allowed, info = rate_limit_manager.check_global_rate_limit()
                elif limit_type == 'per_user':
                    allowed, info = rate_limit_manager.check_user_rate_limit(user_id)
                elif limit_type == 'per_ip':
                    allowed, info = rate_limit_manager.check_ip_rate_limit()
                elif limit_type == 'api_generation':
                    allowed, info = rate_limit_manager.check_api_generation_limit(user_id)
                elif limit_type == 'expensive':
                    allowed, info = rate_limit_manager.check_expensive_operation_limit(user_id)
                elif limit_type == 'custom':
                    if not custom_limit:
                        raise ValueError("custom_limit required for custom rate limit")
                    identifier = rate_limit_manager.get_user_identifier(user_id)
                    allowed, info = rate_limit_manager.check_custom_rate_limit(
                        identifier, custom_limit, custom_window or 60
                    )
                else:
                    raise ValueError(f"Unknown rate limit type: {limit_type}")
                
                if not allowed:
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Try again in {info.get("retry_after", 60)} seconds.',
                        'rate_limit_info': info
                    })
                    response.status_code = 429
                    
                    # Add rate limit headers
                    response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                    response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                    response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
                    response.headers['Retry-After'] = str(info.get('retry_after', 60))
                    
                    return response
                
                # Add rate limit info to response headers
                response = f(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                    response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                    response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
                
                return response
                
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # On error, allow the request to proceed
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def check_multiple_rate_limits(user_id: Optional[int] = None, 
                             check_types: List[str] = None) -> Tuple[bool, Dict]:
    """
    Check multiple rate limits at once
    
    Args:
        user_id: User ID
        check_types: List of rate limit types to check
        
    Returns:
        Tuple of (all_allowed, combined_info)
    """
    if not check_types:
        check_types = ['global', 'per_user', 'per_ip']
    
    all_allowed = True
    combined_info = {}
    most_restrictive = None
    
    for limit_type in check_types:
        if limit_type == 'global':
            allowed, info = rate_limit_manager.check_global_rate_limit()
        elif limit_type == 'per_user':
            allowed, info = rate_limit_manager.check_user_rate_limit(user_id)
        elif limit_type == 'per_ip':
            allowed, info = rate_limit_manager.check_ip_rate_limit()
        elif limit_type == 'api_generation':
            allowed, info = rate_limit_manager.check_api_generation_limit(user_id)
        elif limit_type == 'expensive':
            allowed, info = rate_limit_manager.check_expensive_operation_limit(user_id)
        else:
            continue
        
        combined_info[limit_type] = info
        
        if not allowed:
            all_allowed = False
            if most_restrictive is None or info.get('retry_after', 0) > most_restrictive.get('retry_after', 0):
                most_restrictive = info
    
    return all_allowed, {
        'allowed': all_allowed,
        'limits': combined_info,
        'most_restrictive': most_restrictive
    }

