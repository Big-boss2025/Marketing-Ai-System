"""
Cache Manager
مدير التخزين المؤقت

This module handles caching of API responses and generated media
to reduce API calls and improve performance.
"""

import os
import json
import hashlib
import pickle
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import base64

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """Manager for caching API responses and generated content"""
    
    def __init__(self, cache_type: str = "auto", redis_url: Optional[str] = None,
                 file_cache_dir: Optional[str] = None, default_ttl: int = 3600):
        """
        Initialize cache manager
        
        Args:
            cache_type: "redis", "file", or "auto"
            redis_url: Redis connection URL
            file_cache_dir: Directory for file-based cache
            default_ttl: Default time-to-live in seconds
        """
        self.default_ttl = default_ttl
        self.cache_type = cache_type
        self.redis_client = None
        self.file_cache_dir = file_cache_dir or os.path.join(
            os.path.dirname(__file__), '..', '..', 'cache'
        )
        
        # Initialize cache backend
        self._initialize_cache(redis_url)
        
        # Ensure cache directory exists for file-based cache
        if self.cache_type in ["file", "auto"]:
            Path(self.file_cache_dir).mkdir(parents=True, exist_ok=True)
    
    def _initialize_cache(self, redis_url: Optional[str] = None):
        """Initialize cache backend"""
        if self.cache_type == "redis" or (self.cache_type == "auto" and REDIS_AVAILABLE):
            try:
                if not redis_url:
                    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis_client.ping()
                self.cache_type = "redis"
                logger.info("Redis cache initialized successfully")
                
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                if self.cache_type == "redis":
                    raise
                else:
                    self.cache_type = "file"
                    logger.info("Falling back to file-based cache")
        else:
            self.cache_type = "file"
            logger.info("Using file-based cache")
    
    def _generate_cache_key(self, prefix: str, data: Dict) -> str:
        """Generate cache key from data"""
        # Create a deterministic hash of the data
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key"""
        # Create subdirectories based on key prefix
        parts = key.split(':', 1)
        if len(parts) == 2:
            prefix, hash_key = parts
            subdir = os.path.join(self.file_cache_dir, prefix)
            Path(subdir).mkdir(parents=True, exist_ok=True)
            return os.path.join(subdir, f"{hash_key}.cache")
        else:
            return os.path.join(self.file_cache_dir, f"{key}.cache")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.cache_type == "redis" and self.redis_client:
                # For Redis, serialize the value
                serialized_value = pickle.dumps({
                    'data': value,
                    'timestamp': time.time(),
                    'ttl': ttl
                })
                self.redis_client.setex(key, ttl, serialized_value)
                return True
            
            else:
                # File-based cache
                cache_data = {
                    'data': value,
                    'timestamp': time.time(),
                    'ttl': ttl
                }
                
                file_path = self._get_file_path(key)
                with open(file_path, 'wb') as f:
                    pickle.dump(cache_data, f)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            if self.cache_type == "redis" and self.redis_client:
                serialized_value = self.redis_client.get(key)
                if serialized_value:
                    cache_data = pickle.loads(serialized_value)
                    return cache_data['data']
                return None
            
            else:
                # File-based cache
                file_path = self._get_file_path(key)
                if not os.path.exists(file_path):
                    return None
                
                with open(file_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                # Check if expired
                if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                    self.delete(key)
                    return None
                
                return cache_data['data']
                
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete cache value"""
        try:
            if self.cache_type == "redis" and self.redis_client:
                self.redis_client.delete(key)
                return True
            
            else:
                # File-based cache
                file_path = self._get_file_path(key)
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            if self.cache_type == "redis" and self.redis_client:
                return bool(self.redis_client.exists(key))
            
            else:
                # File-based cache
                file_path = self._get_file_path(key)
                if not os.path.exists(file_path):
                    return False
                
                # Check if expired
                with open(file_path, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                    self.delete(key)
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def clear_expired(self) -> int:
        """Clear expired cache entries (file-based only)"""
        if self.cache_type == "redis":
            # Redis handles expiration automatically
            return 0
        
        cleared_count = 0
        try:
            for root, dirs, files in os.walk(self.file_cache_dir):
                for file in files:
                    if file.endswith('.cache'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'rb') as f:
                                cache_data = pickle.load(f)
                            
                            if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                                os.remove(file_path)
                                cleared_count += 1
                                
                        except Exception:
                            # If we can't read the file, remove it
                            os.remove(file_path)
                            cleared_count += 1
            
            logger.info(f"Cleared {cleared_count} expired cache entries")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.cache_type == "redis" and self.redis_client:
                self.redis_client.flushdb()
                return True
            
            else:
                # File-based cache
                import shutil
                if os.path.exists(self.file_cache_dir):
                    shutil.rmtree(self.file_cache_dir)
                    Path(self.file_cache_dir).mkdir(parents=True, exist_ok=True)
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            if self.cache_type == "redis" and self.redis_client:
                info = self.redis_client.info()
                return {
                    'cache_type': 'redis',
                    'total_keys': info.get('db0', {}).get('keys', 0),
                    'memory_usage': info.get('used_memory_human', 'Unknown'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
            
            else:
                # File-based cache stats
                total_files = 0
                total_size = 0
                expired_files = 0
                
                for root, dirs, files in os.walk(self.file_cache_dir):
                    for file in files:
                        if file.endswith('.cache'):
                            file_path = os.path.join(root, file)
                            total_files += 1
                            total_size += os.path.getsize(file_path)
                            
                            try:
                                with open(file_path, 'rb') as f:
                                    cache_data = pickle.load(f)
                                
                                if time.time() - cache_data['timestamp'] > cache_data['ttl']:
                                    expired_files += 1
                            except Exception:
                                expired_files += 1
                
                return {
                    'cache_type': 'file',
                    'total_files': total_files,
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'expired_files': expired_files,
                    'cache_directory': self.file_cache_dir
                }
                
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
    
    # Specialized methods for different content types
    
    def cache_image_generation(self, prompt: str, width: int, height: int, 
                             style: str, service: str, result: Dict, 
                             ttl: int = 86400) -> bool:
        """Cache image generation result"""
        cache_key = self._generate_cache_key('image_gen', {
            'prompt': prompt,
            'width': width,
            'height': height,
            'style': style,
            'service': service
        })
        
        return self.set(cache_key, result, ttl)
    
    def get_cached_image_generation(self, prompt: str, width: int, height: int,
                                  style: str, service: str) -> Optional[Dict]:
        """Get cached image generation result"""
        cache_key = self._generate_cache_key('image_gen', {
            'prompt': prompt,
            'width': width,
            'height': height,
            'style': style,
            'service': service
        })
        
        return self.get(cache_key)
    
    def cache_video_generation(self, prompt: str, duration: int, fps: int,
                             service: str, result: Dict, ttl: int = 86400) -> bool:
        """Cache video generation result"""
        cache_key = self._generate_cache_key('video_gen', {
            'prompt': prompt,
            'duration': duration,
            'fps': fps,
            'service': service
        })
        
        return self.set(cache_key, result, ttl)
    
    def get_cached_video_generation(self, prompt: str, duration: int, fps: int,
                                  service: str) -> Optional[Dict]:
        """Get cached video generation result"""
        cache_key = self._generate_cache_key('video_gen', {
            'prompt': prompt,
            'duration': duration,
            'fps': fps,
            'service': service
        })
        
        return self.get(cache_key)
    
    def cache_speech_generation(self, text: str, voice: str, language: str,
                              service: str, result: Dict, ttl: int = 86400) -> bool:
        """Cache speech generation result"""
        cache_key = self._generate_cache_key('speech_gen', {
            'text': text,
            'voice': voice,
            'language': language,
            'service': service
        })
        
        return self.set(cache_key, result, ttl)
    
    def get_cached_speech_generation(self, text: str, voice: str, language: str,
                                   service: str) -> Optional[Dict]:
        """Get cached speech generation result"""
        cache_key = self._generate_cache_key('speech_gen', {
            'text': text,
            'voice': voice,
            'language': language,
            'service': service
        })
        
        return self.get(cache_key)
    
    def cache_api_response(self, service: str, endpoint: str, params: Dict,
                         response: Dict, ttl: int = 3600) -> bool:
        """Cache general API response"""
        cache_key = self._generate_cache_key('api_response', {
            'service': service,
            'endpoint': endpoint,
            'params': params
        })
        
        return self.set(cache_key, response, ttl)
    
    def get_cached_api_response(self, service: str, endpoint: str, 
                              params: Dict) -> Optional[Dict]:
        """Get cached API response"""
        cache_key = self._generate_cache_key('api_response', {
            'service': service,
            'endpoint': endpoint,
            'params': params
        })
        
        return self.get(cache_key)
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a specific user"""
        # This is a simplified implementation
        # In a real scenario, you'd need to track user-specific cache keys
        cleared_count = 0
        
        try:
            if self.cache_type == "redis" and self.redis_client:
                # Redis pattern matching
                pattern = f"*user_{user_id}_*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    cleared_count = len(keys)
            
            else:
                # File-based cache - would need more sophisticated tracking
                # For now, just return 0
                pass
            
            return cleared_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager(
    cache_type=os.getenv('CACHE_TYPE', 'auto'),
    redis_url=os.getenv('REDIS_URL'),
    file_cache_dir=os.getenv('CACHE_DIR'),
    default_ttl=int(os.getenv('CACHE_TTL', '3600'))
)

