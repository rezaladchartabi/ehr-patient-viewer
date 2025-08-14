import logging
import logging.handlers
import sys
import os
from typing import Optional
from config import get_config

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """Setup application logging with proper configuration"""
    
    config = get_config()
    level = log_level or config.app.log_level
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}, File: {log_file or 'None'}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, logger_name: str = "http.requests"):
        self.logger = logging.getLogger(logger_name)
    
    async def log_request(self, request, response, duration: float):
        """Log HTTP request details"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_length": response.headers.get("content-length", "unknown")
        }
        
        # Log level based on status code
        if response.status_code >= 500:
            self.logger.error(f"Server error: {log_data}")
        elif response.status_code >= 400:
            self.logger.warning(f"Client error: {log_data}")
        else:
            self.logger.info(f"Request: {log_data}")

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_database_query(self, query: str, duration: float, rows_affected: int = None):
        """Log database query performance"""
        self.logger.info(f"DB Query ({duration:.3f}s): {query[:100]}{'...' if len(query) > 100 else ''} "
                        f"(rows: {rows_affected or 'N/A'})")
    
    def log_cache_operation(self, operation: str, key: str, duration: float, hit: bool = None):
        """Log cache operation performance"""
        hit_status = f"({'HIT' if hit else 'MISS'})" if hit is not None else ""
        self.logger.info(f"Cache {operation} {hit_status} ({duration:.3f}s): {key[:50]}{'...' if len(key) > 50 else ''}")
    
    def log_fhir_request(self, url: str, duration: float, status_code: int = None):
        """Log FHIR request performance"""
        status_info = f" (HTTP {status_code})" if status_code else ""
        self.logger.info(f"FHIR Request ({duration:.3f}s){status_info}: {url}")
    
    def log_sync_operation(self, resource_type: str, duration: float, items_processed: int = None):
        """Log synchronization operation performance"""
        items_info = f" ({items_processed} items)" if items_processed is not None else ""
        self.logger.info(f"Sync {resource_type} ({duration:.3f}s){items_info}")

# Initialize logging on module import
setup_logging()

