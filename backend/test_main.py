import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from main import app, cache, rate_limiter, get_cache_key, is_cacheable, fetch_from_fhir

# Create test client
client = TestClient(app)

class TestCacheFunctions:
    """Test cache-related functions"""
    
    def test_get_cache_key(self):
        """Test cache key generation"""
        key = get_cache_key("GET", "/Patient", "count=50&name=test")
        expected = "GET:/Patient:count=50&name=test"
        assert key == expected
    
    def test_is_cacheable(self):
        """Test cacheable endpoint detection"""
        # Test cacheable endpoints
        assert is_cacheable("/Patient") == True
        assert is_cacheable("/Condition") == True
        assert is_cacheable("/MedicationRequest") == True
        assert is_cacheable("/MedicationAdministration") == True
        assert is_cacheable("/Encounter") == True
        assert is_cacheable("/Observation") == True
        assert is_cacheable("/Procedure") == True
        assert is_cacheable("/Specimen") == True
        
        # Test non-cacheable endpoints
        assert is_cacheable("/cache/status") == False
        assert is_cacheable("/cache/clear") == False
        assert is_cacheable("/") == False

class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Reset rate limiter before each test"""
        self.rate_limiter = rate_limiter
        self.rate_limiter.requests.clear()
    
    def test_rate_limiter_initial_state(self):
        """Test rate limiter initial state"""
        assert self.rate_limiter.max_requests == 100
        assert self.rate_limiter.window_seconds == 60
        assert len(self.rate_limiter.requests) == 0
    
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        client_id = "test_client"
        
        # Should allow first 100 requests
        for i in range(100):
            assert self.rate_limiter.is_allowed(client_id) == True
        
        # 101st request should be blocked
        assert self.rate_limiter.is_allowed(client_id) == False
    
    def test_rate_limiter_window_expiry(self):
        """Test that old requests are cleaned up after window expires"""
        client_id = "test_client"
        
        # Add a request
        self.rate_limiter.is_allowed(client_id)
        assert len(self.rate_limiter.requests[client_id]) == 1
        
        # Simulate time passing (61 seconds)
        old_time = self.rate_limiter.requests[client_id][0]
        self.rate_limiter.requests[client_id] = [old_time - 61]
        
        # Should clean up old requests and allow new one
        assert self.rate_limiter.is_allowed(client_id) == True
        assert len(self.rate_limiter.requests[client_id]) == 1

class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "fhir_server" in data
        assert "cache_ttl" in data
        assert "rate_limit" in data
    
    def test_cache_status_endpoint(self):
        """Test cache status endpoint"""
        response = client.get("/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "total_cache_entries" in data
        assert "active_cache_entries" in data
        assert "expired_cache_entries" in data
        assert "cache_ttl_seconds" in data
        assert "rate_limit_requests" in data
        assert "rate_limit_window_seconds" in data
    
    def test_cache_clear_endpoint(self):
        """Test cache clear endpoint"""
        # Add some test data to cache
        cache["test_key"] = {"data": "test", "timestamp": time.time()}
        assert len(cache) > 0
        
        # Clear cache
        response = client.post("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache cleared successfully"
        assert len(cache) == 0

class TestFHIREndpoints:
    """Test FHIR proxy endpoints"""
    
    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()
    
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
        
        # Verify cache was used
        assert len(cache) > 0
    
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
    
    @patch('main.fetch_from_fhir')
    def test_medication_request_endpoint(self, mock_fetch):
        """Test medication request endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-med-1",
                        "medicationCodeableConcept": {
                            "coding": [{"code": "TestMed", "display": "Test Medication"}]
                        },
                        "status": "active"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test medication request endpoint
        response = client.get("/MedicationRequest?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-med-1"
    
    @patch('main.fetch_from_fhir')
    def test_medication_administration_endpoint(self, mock_fetch):
        """Test medication administration endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-admin-1",
                        "medicationCodeableConcept": {
                            "coding": [{"code": "TestMed", "display": "Test Medication"}]
                        },
                        "status": "completed"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test medication administration endpoint
        response = client.get("/MedicationAdministration?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-admin-1"
    
    @patch('main.fetch_from_fhir')
    def test_encounter_endpoint(self, mock_fetch):
        """Test encounter endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-encounter-1",
                        "class": {"display": "Emergency"},
                        "status": "finished"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test encounter endpoint
        response = client.get("/Encounter?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-encounter-1"
    
    @patch('main.fetch_from_fhir')
    def test_observation_endpoint(self, mock_fetch):
        """Test observation endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-obs-1",
                        "code": {"text": "Blood Pressure"},
                        "status": "final"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test observation endpoint
        response = client.get("/Observation?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-obs-1"
    
    @patch('main.fetch_from_fhir')
    def test_procedure_endpoint(self, mock_fetch):
        """Test procedure endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-proc-1",
                        "code": {"text": "Surgery"},
                        "status": "completed"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test procedure endpoint
        response = client.get("/Procedure?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-proc-1"
    
    @patch('main.fetch_from_fhir')
    def test_specimen_endpoint(self, mock_fetch):
        """Test specimen endpoint"""
        # Mock FHIR response
        mock_response = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "id": "test-spec-1",
                        "type": {"text": "Blood Sample"},
                        "status": "available"
                    }
                }
            ]
        }
        mock_fetch.return_value = mock_response
        
        # Test specimen endpoint
        response = client.get("/Specimen?patient=Patient/test-patient&_count=100")
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert len(data["entry"]) == 1
        assert data["entry"][0]["resource"]["id"] == "test-spec-1"

class TestCacheFunctionality:
    """Test caching functionality"""
    
    def setup_method(self):
        """Clear cache before each test"""
        cache.clear()
    
    @patch('main.fetch_from_fhir')
    def test_cache_hit(self, mock_fetch):
        """Test that cache is used for repeated requests"""
        # Mock FHIR response
        mock_response = {"resourceType": "Bundle", "entry": []}
        mock_fetch.return_value = mock_response
        
        # First request - should call FHIR server
        response1 = client.get("/Patient?_count=50")
        assert response1.status_code == 200
        assert mock_fetch.call_count == 1
        
        # Second request - should use cache
        response2 = client.get("/Patient?_count=50")
        assert response2.status_code == 200
        assert mock_fetch.call_count == 1  # Should not call FHIR again
        
        # Verify cache contains the data
        cache_key = get_cache_key("GET", "/Patient", "count=50&name=None")
        assert cache_key in cache
    
    @patch('main.fetch_from_fhir')
    def test_cache_expiry(self, mock_fetch):
        """Test that cache expires after TTL"""
        # Mock FHIR response
        mock_response = {"resourceType": "Bundle", "entry": []}
        mock_fetch.return_value = mock_response
        
        # First request
        response1 = client.get("/Patient?_count=50")
        assert response1.status_code == 200
        assert mock_fetch.call_count == 1
        
        # Manually expire cache by setting old timestamp
        cache_key = get_cache_key("GET", "/Patient", "count=50&name=None")
        cache[cache_key]["timestamp"] = time.time() - 400  # 400 seconds ago (expired)
        
        # Second request - should call FHIR again due to expiry
        response2 = client.get("/Patient?_count=50")
        assert response2.status_code == 200
        assert mock_fetch.call_count == 2  # Should call FHIR again

class TestErrorHandling:
    """Test error handling"""
    
    @patch('main.fetch_from_fhir')
    def test_fhir_server_error(self, mock_fetch):
        """Test handling of FHIR server errors"""
        # Mock FHIR server error
        mock_fetch.side_effect = Exception("FHIR server error")
        
        # Test that error is handled gracefully
        response = client.get("/Patient?_count=50")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal server error" in data["detail"]
    
    @patch('main.fetch_from_fhir')
    def test_http_exception(self, mock_fetch):
        """Test handling of HTTP exceptions"""
        from fastapi import HTTPException
        
        # Mock HTTP exception
        mock_fetch.side_effect = HTTPException(status_code=404, detail="Not found")
        
        # Test that HTTP exception is handled
        response = client.get("/Patient?_count=50")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Not found"

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        """Reset rate limiter before each test"""
        rate_limiter.requests.clear()
    
    @patch('main.fetch_from_fhir')
    def test_rate_limiting_middleware(self, mock_fetch):
        """Test that rate limiting middleware works"""
        # Mock FHIR response
        mock_response = {"resourceType": "Bundle", "entry": []}
        mock_fetch.return_value = mock_response
        
        # Make requests up to the limit
        for i in range(100):
            response = client.get("/Patient?_count=1")
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.get("/Patient?_count=1")
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data["detail"]

class TestParameterHandling:
    """Test parameter handling"""
    
    @patch('main.fetch_from_fhir')
    def test_optional_parameters(self, mock_fetch):
        """Test that optional parameters are handled correctly"""
        # Mock FHIR response
        mock_response = {"resourceType": "Bundle", "entry": []}
        mock_fetch.return_value = mock_response
        
        # Test with different parameter combinations
        test_cases = [
            "/Patient?_count=50",
            "/Patient?name=test",
            "/Patient?_count=50&name=test",
            "/Condition?patient=Patient/test",
            "/MedicationRequest?patient=Patient/test&medication=test",
        ]
        
        for url in test_cases:
            response = client.get(url)
            assert response.status_code == 200
            # Verify fetch_from_fhir was called with correct parameters
            assert mock_fetch.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
