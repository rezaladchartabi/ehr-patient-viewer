import os
from typing import Optional
from dataclasses import dataclass
from functools import lru_cache

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    path: str = "local_ehr.db"
    search_index_path: str = "search_index.sqlite3"
    max_connections: int = 20
    connection_timeout: float = 30.0

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    ttl_seconds: int = 300  # 5 minutes
    test_ttl_seconds: float = 0.2  # For tests
    max_size: int = 2000
    cleanup_interval: int = 60  # seconds

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    max_requests: int = 100
    window_seconds: int = 60
    test_window_seconds: int = 1  # For tests

@dataclass
class FHIRConfig:
    """FHIR server configuration"""
    base_url: str = "https://imagination-promptly-subsequent-truck.trycloudflare.com/fhir"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 5.0

@dataclass
class SyncConfig:
    """Synchronization configuration"""
    interval_seconds: int = 300  # 5 minutes
    batch_size: int = 1000
    resource_types: list = None

    def __post_init__(self):
        if self.resource_types is None:
            self.resource_types = [
                'Patient',
                'AllergyIntolerance', 
                'Condition',
                'Encounter',
                'MedicationRequest',
                'MedicationAdministration',
                'Observation',
                'Procedure',
                'Specimen'
            ]

@dataclass
class AppConfig:
    """Main application configuration"""
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list = None
    log_level: str = "INFO"

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]

@dataclass
class Config:
    """Complete application configuration"""
    app: AppConfig
    database: DatabaseConfig
    cache: CacheConfig
    rate_limit: RateLimitConfig
    fhir: FHIRConfig
    sync: SyncConfig

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables"""
        return cls(
            app=AppConfig(
                debug=os.getenv("DEBUG", "false").lower() == "true",
                host=os.getenv("HOST", "127.0.0.1"),
                port=int(os.getenv("PORT", "8000")),
                log_level=os.getenv("LOG_LEVEL", "INFO")
            ),
            database=DatabaseConfig(
                path=os.getenv("DB_PATH", "local_ehr.db"),
                search_index_path=os.getenv("SEARCH_DB_PATH", "search_index.sqlite3"),
                max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
                connection_timeout=float(os.getenv("DB_TIMEOUT", "30.0"))
            ),
            cache=CacheConfig(
                ttl_seconds=int(os.getenv("CACHE_TTL", "300")),
                max_size=int(os.getenv("CACHE_MAX_SIZE", "2000")),
                cleanup_interval=int(os.getenv("CACHE_CLEANUP_INTERVAL", "60"))
            ),
            rate_limit=RateLimitConfig(
                max_requests=int(os.getenv("RATE_LIMIT_MAX", "100")),
                window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
            ),
            fhir=FHIRConfig(
                base_url=os.getenv("FHIR_BASE_URL", "https://fdfbc9a33dc5.ngrok-free.app/fhir"),
                timeout=float(os.getenv("FHIR_TIMEOUT", "30.0")),
                max_retries=int(os.getenv("FHIR_MAX_RETRIES", "3")),
                retry_delay=float(os.getenv("FHIR_RETRY_DELAY", "5.0"))
            ),
            sync=SyncConfig(
                interval_seconds=int(os.getenv("SYNC_INTERVAL", "300")),
                batch_size=int(os.getenv("SYNC_BATCH_SIZE", "1000"))
            )
        )

@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance"""
    return Config.from_env()

def is_test_environment() -> bool:
    """Check if running in test environment"""
    return (
        'pytest' in __import__('sys').modules or
        bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("PYTEST_ADDOPTS") or os.getenv("PYTEST_RUNNING"))
    )
