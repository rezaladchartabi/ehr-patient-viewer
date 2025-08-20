"""
Base Data Source

Abstract base class for all external medical data sources.
Provides common interface and functionality for data source integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import httpx
from config import get_config

logger = logging.getLogger(__name__)

class BaseDataSource(ABC):
    """Abstract base class for external medical data sources"""
    
    def __init__(self, name: str, api_key: str = "", base_url: str = "", cache_ttl: int = 3600):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.cache_ttl = cache_ttl
        self.config = get_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Dict] = {}
        self._last_request_time = 0
        self._rate_limit_delay = 0.1  # 100ms between requests
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration"""
        if self._client is None:
            limits = httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
                max_requests=100
            )
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=30.0,
                headers={
                    "User-Agent": f"EHR-Proxy/{self.name}/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self._client
    
    async def _rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - time_since_last)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    def _get_cache_key(self, method: str, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for request"""
        param_str = ""
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return f"{self.name}:{method}:{endpoint}:{param_str}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        timestamp = cache_entry.get('timestamp', 0)
        return (datetime.now().timestamp() - timestamp) < self.cache_ttl
    
    async def _cached_request(self, method: str, endpoint: str, params: Dict = None, 
                            headers: Dict = None, data: Dict = None) -> Dict:
        """Make cached HTTP request"""
        cache_key = self._get_cache_key(method, endpoint, params)
        
        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]['data']
        
        # Make actual request
        await self._rate_limit()
        client = await self._get_client()
        
        try:
            url = f"{self.base_url}{endpoint}"
            response = await client.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            # Cache the result
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.debug(f"Cache miss for {cache_key}, stored new data")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {e}")
            raise
    
    @abstractmethod
    async def search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search for data in the source"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Get specific item by ID"""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict:
        """Get source metadata and capabilities"""
        pass
    
    async def health_check(self) -> Dict:
        """Check if the data source is healthy and accessible"""
        try:
            metadata = await self.get_metadata()
            return {
                'status': 'healthy',
                'source': self.name,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return {
                'status': 'unhealthy',
                'source': self.name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info(f"Cache cleared for {self.name}")
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None
