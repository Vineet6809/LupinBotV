"""Simple in-memory cache for API responses."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

logger = logging.getLogger('LupinBot.cache')

class CacheManager:
    """Manages caching for external API calls."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            default_ttl: Default time-to-live in seconds (5 minutes by default)
        """
        # key -> (value, timestamp, ttl_override)
        self.cache: dict[str, Tuple[Any, datetime, Optional[int]]] = {}
        self.default_ttl = default_ttl
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key not in self.cache:
                return None
            
            value, timestamp, ttl_override = self.cache[key]
            age = datetime.now() - timestamp
            ttl_to_use = ttl_override if ttl_override is not None else self.default_ttl
            
            if age.total_seconds() > ttl_to_use:
                # Cache expired
                del self.cache[key]
                return None
            
            return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom time-to-live in seconds
        """
        async with self.lock:
            self.cache[key] = (value, datetime.now(), ttl)
    
    async def clear(self):
        """Clear all cached values."""
        async with self.lock:
            self.cache.clear()
    
    async def invalidate(self, key: str):
        """
        Remove a specific key from the cache.
        
        Args:
            key: Cache key to invalidate
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def size(self) -> int:
        """Get the number of items in the cache."""
        return len(self.cache)

# Global cache instance
cache = CacheManager(default_ttl=600)  # 10 minutes default
