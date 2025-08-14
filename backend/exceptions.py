from typing import Optional, Dict, Any
from fastapi import HTTPException

class EHRBaseException(Exception):
    """Base exception for EHR application"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class FHIRConnectionError(EHRBaseException):
    """Raised when there's an issue connecting to FHIR server"""
    pass

class FHIRDataError(EHRBaseException):
    """Raised when there's an issue with FHIR data format or content"""
    pass

class DatabaseError(EHRBaseException):
    """Raised when there's a database operation error"""
    pass

class CacheError(EHRBaseException):
    """Raised when there's a cache operation error"""
    pass

class SyncError(EHRBaseException):
    """Raised when there's a synchronization error"""
    pass

class ValidationError(EHRBaseException):
    """Raised when data validation fails"""
    pass

class RateLimitExceeded(EHRBaseException):
    """Raised when rate limit is exceeded"""
    pass

def handle_ehr_exception(exc: EHRBaseException) -> HTTPException:
    """Convert EHR exceptions to HTTP exceptions"""
    status_code = 500
    error_code = exc.error_code or "INTERNAL_ERROR"
    
    if isinstance(exc, FHIRConnectionError):
        status_code = 503  # Service Unavailable
        error_code = "FHIR_CONNECTION_ERROR"
    elif isinstance(exc, FHIRDataError):
        status_code = 502  # Bad Gateway
        error_code = "FHIR_DATA_ERROR"
    elif isinstance(exc, DatabaseError):
        status_code = 500  # Internal Server Error
        error_code = "DATABASE_ERROR"
    elif isinstance(exc, CacheError):
        status_code = 500  # Internal Server Error
        error_code = "CACHE_ERROR"
    elif isinstance(exc, SyncError):
        status_code = 500  # Internal Server Error
        error_code = "SYNC_ERROR"
    elif isinstance(exc, ValidationError):
        status_code = 400  # Bad Request
        error_code = "VALIDATION_ERROR"
    elif isinstance(exc, RateLimitExceeded):
        status_code = 429  # Too Many Requests
        error_code = "RATE_LIMIT_EXCEEDED"
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": exc.message,
            "error_code": error_code,
            "details": exc.details
        }
    )

