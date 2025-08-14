import time
import threading
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from collections import OrderedDict
import logging
from config import get_config, is_test_environment
from exceptions import CacheError

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a cache entry with metadata"""
    
    def __init__(self, data: Any, ttl: int, created_at: float = None):
        self.data = data
        self.ttl = ttl
        self.created_at = created_at or time.time()
        self.access_count = 0
        self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        return time.time() - self.created_at > self.ttl
    
    @property
    def age(self) -> float:
        """Get the age of the cache entry in seconds"""
        return time.time() - self.created_at
    
    def access(self):
        """Mark the entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()

class CacheStats:
    """Cache statistics and monitoring"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0
        self.total_requests = 0
        self._lock = threading.Lock()
    
    def record_hit(self):
        """Record a cache hit"""
        with self._lock:
            self.hits += 1
            self.total_requests += 1
    
    def record_miss(self):
        """Record a cache miss"""
        with self._lock:
            self.misses += 1
            self.total_requests += 1
    
    def record_eviction(self):
        """Record a cache eviction"""
        with self._lock:
            self.evictions += 1
    
    def record_expiration(self):
        """Record a cache expiration"""
        with self._lock:
            self.expirations += 1
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "expirations": self.expirations,
                "total_requests": self.total_requests,
                "hit_rate": self.hit_rate
            }

class AdvancedCache:
    """Advanced cache implementation with LRU eviction and monitoring"""
    
    def __init__(self, max_size: int = None, default_ttl: int = None):
        config = get_config()
        self.max_size = max_size or config.cache.max_size
        self.default_ttl = default_ttl or (config.cache.test_ttl_seconds if is_test_environment() else config.cache.ttl_seconds)
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self.stats = CacheStats()
        self._cleanup_interval = config.cache.cleanup_interval
        self._last_cleanup = time.time()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_worker(self):
        """Background worker for cache cleanup"""
        while True:
            try:
                time.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self.stats.record_expiration()
                logger.debug(f"Expired cache entry: {key}")
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if self._cache:
            key, entry = self._cache.popitem(last=False)
            self.stats.record_eviction()
            logger.debug(f"Evicted cache entry: {key}")
    
    def _normalize_key(self, key: str) -> str:
        """Normalize cache key for consistency"""
        # Remove None values and sort parameters for consistent keys
        if '?' in key:
            base, params = key.split('?', 1)
            param_pairs = []
            for param in params.split('&'):
                if '=' in param:
                    k, v = param.split('=', 1)
                    if v != 'None' and v != '':
                        param_pairs.append(f"{k}={v}")
            param_pairs.sort()
            return f"{base}?{'&'.join(param_pairs)}" if param_pairs else base
        return key
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        normalized_key = self._normalize_key(key)
        
        with self._lock:
            if normalized_key in self._cache:
                entry = self._cache[normalized_key]
                
                if entry.is_expired:
                    del self._cache[normalized_key]
                    self.stats.record_miss()
                    self.stats.record_expiration()
                    return None
                
                # Move to end (most recently used)
                self._cache.move_to_end(normalized_key)
                entry.access()
                self.stats.record_hit()
                return entry.data
            
            self.stats.record_miss()
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        normalized_key = self._normalize_key(key)
        cache_ttl = ttl or self.default_ttl
        
        with self._lock:
            # Remove existing entry if present
            if normalized_key in self._cache:
                del self._cache[normalized_key]
            
            # Evict if at capacity
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            # Add new entry
            entry = CacheEntry(value, cache_ttl)
            self._cache[normalized_key] = entry
            
            # Move to end (most recently used)
            self._cache.move_to_end(normalized_key)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        normalized_key = self._normalize_key(key)
        
        with self._lock:
            if normalized_key in self._cache:
                del self._cache[normalized_key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        normalized_key = self._normalize_key(key)
        
        with self._lock:
            if normalized_key in self._cache:
                entry = self._cache[normalized_key]
                if entry.is_expired:
                    del self._cache[normalized_key]
                    return False
                return True
            return False
    
    def get_or_set(self, key: str, default_func: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """Get value from cache or set default if not exists"""
        value = self.get(key)
        if value is not None:
            return value
        
        # Generate default value
        try:
            value = default_func()
            self.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Error generating default value for key {key}: {e}")
            raise CacheError(f"Failed to generate default value: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            stats = self.stats.get_stats()
            stats.update({
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "memory_usage": self._estimate_memory_usage()
            })
            return stats
    
    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of cache in bytes"""
        total_size = 0
        for key, entry in self._cache.items():
            # Rough estimation
            total_size += len(key.encode('utf-8'))
            total_size += len(str(entry.data).encode('utf-8'))
            total_size += 100  # Overhead for CacheEntry object
        return total_size
    
    def get_keys(self) -> List[str]:
        """Get all cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def get_entries_info(self) -> List[Dict[str, Any]]:
        """Get information about all cache entries"""
        with self._lock:
            return [
                {
                    "key": key,
                    "age": entry.age,
                    "ttl": entry.ttl,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed,
                    "is_expired": entry.is_expired
                }
                for key, entry in self._cache.items()
            ]

# Global cache instance
_cache_instance: Optional[AdvancedCache] = None

def get_cache() -> AdvancedCache:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        config = get_config()
        _cache_instance = AdvancedCache(
            max_size=config.cache.max_size,
            default_ttl=config.cache.test_ttl_seconds if is_test_environment() else config.cache.ttl_seconds
        )
    return _cache_instance

def clear_cache():
    """Clear global cache"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.clear()

def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return get_cache().get_stats()

