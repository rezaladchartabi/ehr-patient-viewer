import httpx
import asyncio
import time
from typing import Dict, Optional, Any
from contextlib import asynccontextmanager
import logging
from config import get_config
from exceptions import FHIRConnectionError, FHIRDataError

logger = logging.getLogger(__name__)

class HTTPClientManager:
    """HTTP client manager with connection pooling and retry logic"""
    
    def __init__(self):
        self.config = get_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0
        }
    
    async def _create_client(self) -> httpx.AsyncClient:
        """Create a new HTTP client with proper configuration"""
        limits = httpx.Limits(
            max_connections=self.config.database.max_connections,
            max_keepalive_connections=10,
            max_requests=1000
        )
        
        return httpx.AsyncClient(
            limits=limits,
            timeout=self.config.fhir.timeout,
            headers={
                "User-Agent": "EHR-Proxy/1.0",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"
            },
            follow_redirects=True
        )
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    self._client = await self._create_client()
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            async with self._lock:
                if self._client:
                    await self._client.aclose()
                    self._client = None
    
    async def request(
        self, 
        method: str, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: Optional[int] = None
    ) -> httpx.Response:
        """Make HTTP request with retry logic"""
        retry_count = retries or self.config.fhir.max_retries
        last_exception = None
        
        for attempt in range(retry_count + 1):
            try:
                client = await self.get_client()
                
                # Prepare request
                request_headers = {}
                if headers:
                    request_headers.update(headers)
                
                # Make request
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=request_headers
                )
                
                # Record statistics
                self._stats['total_requests'] += 1
                
                # Check for HTTP errors
                response.raise_for_status()
                
                self._stats['successful_requests'] += 1
                return response
                
            except httpx.TimeoutException as e:
                last_exception = FHIRConnectionError(
                    f"Request timeout after {self.config.fhir.timeout}s",
                    error_code="TIMEOUT",
                    details={"attempt": attempt + 1, "url": url}
                )
                logger.warning(f"Request timeout (attempt {attempt + 1}): {url}")
                
            except httpx.HTTPStatusError as e:
                last_exception = FHIRDataError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    error_code=f"HTTP_{e.response.status_code}",
                    details={
                        "status_code": e.response.status_code,
                        "url": url,
                        "attempt": attempt + 1
                    }
                )
                logger.warning(f"HTTP error {e.response.status_code} (attempt {attempt + 1}): {url}")
                
            except httpx.RequestError as e:
                last_exception = FHIRConnectionError(
                    f"Request failed: {str(e)}",
                    error_code="REQUEST_ERROR",
                    details={"attempt": attempt + 1, "url": url}
                )
                logger.warning(f"Request error (attempt {attempt + 1}): {url} - {e}")
                
            except Exception as e:
                last_exception = FHIRConnectionError(
                    f"Unexpected error: {str(e)}",
                    error_code="UNEXPECTED_ERROR",
                    details={"attempt": attempt + 1, "url": url}
                )
                logger.error(f"Unexpected error (attempt {attempt + 1}): {url} - {e}")
            
            # Record failed attempt
            self._stats['failed_requests'] += 1
            
            # Retry logic
            if attempt < retry_count:
                self._stats['retry_attempts'] += 1
                wait_time = self.config.fhir.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying request in {wait_time}s (attempt {attempt + 1}/{retry_count})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All retry attempts failed for: {url}")
                raise last_exception
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make GET request"""
        return await self.request("GET", url, params=params)
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Make POST request"""
        return await self.request("POST", url, json=data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP client statistics"""
        return {
            **self._stats,
            "config": {
                "timeout": self.config.fhir.timeout,
                "max_retries": self.config.fhir.max_retries,
                "retry_delay": self.config.fhir.retry_delay,
                "max_connections": self.config.database.max_connections
            }
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0
        }

# Global HTTP client manager
_http_client_manager: Optional[HTTPClientManager] = None

async def get_http_client() -> HTTPClientManager:
    """Get global HTTP client manager"""
    global _http_client_manager
    if _http_client_manager is None:
        _http_client_manager = HTTPClientManager()
    return _http_client_manager

@asynccontextmanager
async def get_http_client_context():
    """Context manager for HTTP client"""
    client = await get_http_client()
    try:
        yield client
    finally:
        # Don't close the client here as it's shared
        pass

async def close_http_client():
    """Close global HTTP client"""
    global _http_client_manager
    if _http_client_manager:
        await _http_client_manager.close()
        _http_client_manager = None

def get_http_stats() -> Dict[str, Any]:
    """Get HTTP client statistics"""
    if _http_client_manager:
        return _http_client_manager.get_stats()
    return {}

def reset_http_stats():
    """Reset HTTP client statistics"""
    if _http_client_manager:
        _http_client_manager.reset_stats()

