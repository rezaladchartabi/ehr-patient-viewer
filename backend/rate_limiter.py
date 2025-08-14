import time
import threading
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import logging
from config import get_config, is_test_environment
from exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiter with sliding window and monitoring"""
    
    def __init__(self, max_requests: int = None, window_seconds: int = None):
        config = get_config()
        self.max_requests = max_requests or config.rate_limit.max_requests
        self.window_seconds = window_seconds or (
            config.rate_limit.test_window_seconds if is_test_environment() 
            else config.rate_limit.window_seconds
        )
        
        # Use deque for efficient sliding window
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.RLock()
        
        # Statistics
        self._stats = {
            'total_requests': 0,
            'allowed_requests': 0,
            'blocked_requests': 0,
            'unique_clients': set()
        }
        self._stats_lock = threading.Lock()
    
    def _cleanup_old_requests(self, client_id: str) -> None:
        """Remove requests older than the window"""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Remove old requests from the front of the deque
        while (self._requests[client_id] and 
               self._requests[client_id][0] < cutoff_time):
            self._requests[client_id].popleft()
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for the client"""
        current_time = time.time()
        
        with self._lock:
            # Clean up old requests
            self._cleanup_old_requests(client_id)
            
            # Check if under limit
            if len(self._requests[client_id]) < self.max_requests:
                self._requests[client_id].append(current_time)
                self._record_request(client_id, True)
                return True
            else:
                self._record_request(client_id, False)
                return False
    
    def _record_request(self, client_id: str, allowed: bool) -> None:
        """Record request statistics"""
        with self._stats_lock:
            self._stats['total_requests'] += 1
            self._stats['unique_clients'].add(client_id)
            
            if allowed:
                self._stats['allowed_requests'] += 1
            else:
                self._stats['blocked_requests'] += 1
    
    def get_client_status(self, client_id: str) -> Dict[str, any]:
        """Get current status for a specific client"""
        with self._lock:
            self._cleanup_old_requests(client_id)
            
            current_requests = len(self._requests[client_id])
            remaining_requests = max(0, self.max_requests - current_requests)
            
            # Calculate time until next available slot
            time_until_reset = 0
            if current_requests >= self.max_requests:
                oldest_request = self._requests[client_id][0]
                time_until_reset = self.window_seconds - (time.time() - oldest_request)
                time_until_reset = max(0, time_until_reset)
            
            return {
                'client_id': client_id,
                'current_requests': current_requests,
                'max_requests': self.max_requests,
                'remaining_requests': remaining_requests,
                'time_until_reset': time_until_reset,
                'is_allowed': remaining_requests > 0
            }
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self._stats_lock:
            stats = {
                'total_requests': self._stats['total_requests'],
                'allowed_requests': self._stats['allowed_requests'],
                'blocked_requests': self._stats['blocked_requests'],
                'unique_clients': len(self._stats['unique_clients']),
                'max_requests': self.max_requests,
                'window_seconds': self.window_seconds
            }
            
            # Calculate success rate
            if stats['total_requests'] > 0:
                stats['success_rate'] = stats['allowed_requests'] / stats['total_requests']
            else:
                stats['success_rate'] = 1.0
            
            return stats
    
    def reset_client(self, client_id: str) -> bool:
        """Reset rate limit for a specific client"""
        with self._lock:
            if client_id in self._requests:
                self._requests[client_id].clear()
                return True
            return False
    
    def reset_all(self) -> None:
        """Reset rate limits for all clients"""
        with self._lock:
            self._requests.clear()
        
        with self._stats_lock:
            self._stats['total_requests'] = 0
            self._stats['allowed_requests'] = 0
            self._stats['blocked_requests'] = 0
            self._stats['unique_clients'].clear()
    
    def get_active_clients(self) -> List[str]:
        """Get list of active clients with recent requests"""
        with self._lock:
            active_clients = []
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds
            
            for client_id, requests in self._requests.items():
                # Check if client has any recent requests
                if requests and requests[-1] >= cutoff_time:
                    active_clients.append(client_id)
            
            return active_clients

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    def __call__(self, request, call_next):
        # Get client identifier (IP address or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id):
            raise RateLimitExceeded(
                f"Rate limit exceeded for client {client_id}",
                error_code="RATE_LIMIT_EXCEEDED",
                details={
                    "client_id": client_id,
                    "max_requests": self.rate_limiter.max_requests,
                    "window_seconds": self.rate_limiter.window_seconds
                }
            )
        
        # Add rate limit headers to response
        response = call_next(request)
        self._add_rate_limit_headers(response, client_id)
        
        return response
    
    def _get_client_id(self, request) -> str:
        """Extract client identifier from request"""
        # Try to get from X-Forwarded-For header (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host
        
        # For testing, use a consistent client ID
        if is_test_environment():
            return "test_client"
        
        return client_ip
    
    def _add_rate_limit_headers(self, response, client_id: str) -> None:
        """Add rate limit headers to response"""
        status = self.rate_limiter.get_client_status(client_id)
        
        response.headers["X-RateLimit-Limit"] = str(status['max_requests'])
        response.headers["X-RateLimit-Remaining"] = str(status['remaining_requests'])
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + status['time_until_reset']))

# Global rate limiter instance
_rate_limiter_instance: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        config = get_config()
        _rate_limiter_instance = RateLimiter(
            max_requests=config.rate_limit.max_requests,
            window_seconds=config.rate_limit.test_window_seconds if is_test_environment() 
                          else config.rate_limit.window_seconds
        )
    return _rate_limiter_instance

def reset_rate_limiter():
    """Reset global rate limiter"""
    global _rate_limiter_instance
    if _rate_limiter_instance:
        _rate_limiter_instance.reset_all()

def get_rate_limit_stats() -> Dict[str, any]:
    """Get global rate limiter statistics"""
    return get_rate_limiter().get_stats()

