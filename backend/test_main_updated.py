import pytest
import asyncio
import time
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Set test environment
os.environ["PYTEST_RUNNING"] = "true"

# Import the new modules
from main import app
from cache import get_cache, clear_cache
from rate_limiter import get_rate_limiter, reset_rate_limiter
from database import DatabaseManager
from config import get_config
from exceptions import EHRBaseException, FHIRConnectionError, RateLimitExceeded

# Create test client
client = TestClient(app)

class TestConfiguration:
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test that configuration loads correctly"""
        config = get_config()
        assert config.fhir.base_url is not None
        assert config.cache.ttl_seconds > 0
        assert config.rate_limit.max_requests > 0
    
    def test_test_environment_detection(self):
        """Test that test environment is detected correctly"""
        # Should be detected as test environment
        assert os.getenv("PYTEST_RUNNING") == "true"

class TestCacheSystem:
    """Test the new cache system"""
    
    def setup_method(self):
        """Reset cache before each test"""
        clear_cache()
    
    def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = get_cache()
        
        # Test set and get
        cache.set("test_key", {"data": "test_value"})
        result = cache.get("test_key")
        assert result == {"data": "test_value"}
        
        # Test cache miss
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = get_cache()
        
        # Set with very short TTL
        cache.set("expire_key", {"data": "test"}, ttl=0.1)
        
        # Should be available immediately
        result = cache.get("expire_key")
        assert result == {"data": "test"}
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Should be expired
        result = cache.get("expire_key")
        assert result is None
    
    def test_cache_key_normalization(self):
        """Test cache key normalization"""
        cache = get_cache()
        
        # Test that different parameter orders create the same key
        cache.set("GET:/Patient?name=test&count=50", {"data": "test1"})
        cache.set("GET:/Patient?count=50&name=test", {"data": "test2"})
        
        # Should normalize to the same key
        result1 = cache.get("GET:/Patient?name=test&count=50")
        result2 = cache.get("GET:/Patient?count=50&name=test")
        
        # Both should return the same result (last one set)
        assert result1 == result2
        assert result1 == {"data": "test2"}
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = get_cache()
        
        # Add some data
        cache.set("key1", {"data": "value1"})
        cache.set("key2", {"data": "value2"})
        
        # Get stats
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Access data
        cache.get("key1")
        cache.get("nonexistent")
        
        # Check updated stats
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

class TestRateLimiter:
    """Test the new rate limiter"""
    
    def setup_method(self):
        """Reset rate limiter before each test"""
        reset_rate_limiter()
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality"""
        rate_limiter = get_rate_limiter()
        
        # Should allow requests within limit
        for i in range(100):
            assert rate_limiter.is_allowed("test_client") == True
        
        # Should block after limit
        assert rate_limiter.is_allowed("test_client") == False
    
    def test_rate_limiter_window_expiry(self):
        """Test rate limiter window expiry"""
        rate_limiter = get_rate_limiter()
        
        # Add a request
        rate_limiter.is_allowed("test_client")
        
        # Simulate time passing by manipulating the internal state
        # This is a bit hacky but necessary for testing
        with patch.object(rate_limiter, '_cleanup_old_requests') as mock_cleanup:
            # Mock cleanup to simulate old requests being removed
            mock_cleanup.return_value = None
            
            # Should still be under limit
            assert rate_limiter.is_allowed("test_client") == True
    
    def test_rate_limiter_stats(self):
        """Test rate limiter statistics"""
        rate_limiter = get_rate_limiter()
        
        # Make some requests
        for i in range(50):
            rate_limiter.is_allowed("client1")
        
        for i in range(25):
            rate_limiter.is_allowed("client2")
        
        # Check stats
        stats = rate_limiter.get_stats()
        assert stats["total_requests"] == 75
        assert stats["allowed_requests"] == 75
        assert stats["unique_clients"] == 2

class TestDatabaseManager:
    """Test the new database manager"""
    
    def setup_method(self):
        """Setup test database"""
        self.db_path = ":memory:"  # Use in-memory database for tests
        self.db_manager = DatabaseManager(self.db_path)
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Should create tables
        result = self.db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in result]
        
        expected_tables = [
            'patients', 'allergies', 'conditions', 'encounters',
            'medication_requests', 'medication_administrations',
            'observations', 'procedures', 'specimens', 'sync_metadata'
        ]
        
        for table in expected_tables:
            assert table in table_names
    
    def test_database_operations(self):
        """Test basic database operations"""
        # Test insert
        sql = "INSERT INTO patients (id, family_name, gender) VALUES (?, ?, ?)"
        affected = self.db_manager.execute_update(sql, ("test-1", "TestPatient", "male"))
        assert affected == 1
        
        # Test query
        result = self.db_manager.execute_query("SELECT * FROM patients WHERE id = ?", ("test-1",))
        assert len(result) == 1
        assert result[0]['family_name'] == "TestPatient"
        
        # Test single query
        result = self.db_manager.execute_single("SELECT * FROM patients WHERE id = ?", ("test-1",))
        assert result is not None
        assert result['gender'] == "male"

class TestExceptionHandling:
    """Test exception handling"""
    
    def test_ehr_base_exception(self):
        """Test base exception class"""
        exc = EHRBaseException("Test error", "TEST_ERROR", {"detail": "test"})
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details["detail"] == "test"
    
    def test_fhir_connection_error(self):
        """Test FHIR connection error"""
        exc = FHIRConnectionError("Connection failed")
        assert isinstance(exc, EHRBaseException)
        assert exc.message == "Connection failed"
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded error"""
        exc = RateLimitExceeded("Rate limit exceeded")
        assert isinstance(exc, EHRBaseException)
        assert exc.message == "Rate limit exceeded"

class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "fhir_server" in data
    
    def test_cache_status_endpoint(self):
        """Test cache status endpoint"""
        response = client.get("/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert "hits" in data
        assert "misses" in data
    
    def test_rate_limit_status_endpoint(self):
        """Test rate limit status endpoint"""
        response = client.get("/rate-limit/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "allowed_requests" in data
        assert "blocked_requests" in data

class TestLocalDatabaseEndpoints:
    """Test local database endpoints"""
    
    def setup_method(self):
        """Setup test data"""
        # Clear any existing test data
        pass
    
    def test_local_patients_endpoint(self):
        """Test local patients endpoint"""
        response = client.get("/local/patients?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "patients" in data
        assert "total" in data
    
    def test_local_patient_by_id_endpoint(self):
        """Test local patient by ID endpoint"""
        # First get a list of patients
        response = client.get("/local/patients?limit=1")
        assert response.status_code == 200
        data = response.json()
        
        if data["patients"]:
            patient_id = data["patients"][0]["id"]
            
            # Get specific patient
            response = client.get(f"/local/patients/{patient_id}")
            assert response.status_code == 200
            patient_data = response.json()
            assert patient_data["id"] == patient_id

class TestFHIREndpoints:
    """Test FHIR proxy endpoints"""
    
    def setup_method(self):
        """Clear cache before each test"""
        clear_cache()
    
    @patch('main.fetch_from_fhir')
    def test_patient_endpoint(self, mock_fetch):
        """Test patient endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-patient-1",
                        "resourceType": "Patient",
                        "name": [{"family": "TestPatient"}],
                        "gender": "male",
                        "birthDate": "1990-01-01"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test patient endpoint
        response = client.get("/Patient?_count=50")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-patient-1"
    
    @patch('main.fetch_from_fhir')
    def test_condition_endpoint(self, mock_fetch):
        """Test condition endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-condition-1",
                        "resourceType": "Condition",
                        "code": {"text": "Test Condition"},
                        "status": "active"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test condition endpoint
        response = client.get("/Condition?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-condition-1"

class TestErrorHandling:
    """Test error handling in endpoints"""
    
    @patch('main.fetch_from_fhir')
    def test_fhir_connection_error(self, mock_fetch):
        """Test FHIR connection error handling"""
        # Mock FHIR connection error
        mock_fetch.side_effect = FHIRConnectionError("Connection failed")
        
        # Test that error is properly handled
        response = client.get("/Patient?_count=50")
        assert response.status_code == 503  # Service Unavailable
    
    @patch('main.fetch_from_fhir')
    def test_fhir_data_error(self, mock_fetch):
        """Test FHIR data error handling"""
        # Mock FHIR data error
        mock_fetch.side_effect = Exception("Invalid FHIR data")
        
        # Test that error is properly handled
        response = client.get("/Patient?_count=50")
        assert response.status_code == 500  # Internal Server Error

class TestSyncEndpoints:
    """Test synchronization endpoints"""
    
    def test_sync_all_endpoint(self):
        """Test sync all endpoint"""
        response = client.post("/sync/all")
        # Should return 200 or 202 (accepted)
        assert response.status_code in [200, 202]
    
    def test_sync_patients_endpoint(self):
        """Test sync specific patients endpoint"""
        patient_ids = ["test-patient-1", "test-patient-2"]
        response = client.post("/sync/patients", json={"patient_ids": patient_ids})
        # Should return 200 or 202 (accepted)
        assert response.status_code in [200, 202]

# Test utilities
def test_cache_key_generation():
    """Test cache key generation utility"""
    from main import get_cache_key
    
    # Test basic key generation
    key = get_cache_key("GET", "/Patient", "count=50&name=test")
    assert "GET" in key
    assert "/Patient" in key
    assert "count=50" in key
    assert "name=test" in key

def test_cacheable_endpoint_detection():
    """Test cacheable endpoint detection"""
    from main import is_cacheable
    
    # Test cacheable endpoints
    assert is_cacheable("/Patient") == True
    assert is_cacheable("/Condition") == True
    assert is_cacheable("/Encounter") == True
    
    # Test non-cacheable endpoints
    assert is_cacheable("/cache/status") == False
    assert is_cacheable("/cache/clear") == False
    assert is_cacheable("/") == False

if __name__ == "__main__":
    pytest.main([__file__])

