# FHIR Proxy Backend Tests

This directory contains comprehensive unit tests for the FHIR proxy backend service.

## 🧪 Test Structure

### Test Classes

1. **TestCacheFunctions** - Tests cache-related utility functions
   - `test_get_cache_key()` - Tests cache key generation
   - `test_is_cacheable()` - Tests cacheable endpoint detection

2. **TestRateLimiter** - Tests rate limiting functionality
   - `test_rate_limiter_initial_state()` - Tests initial configuration
   - `test_rate_limiter_allows_requests()` - Tests request allowance within limits
   - `test_rate_limiter_window_expiry()` - Tests cleanup of expired requests

3. **TestHealthEndpoints** - Tests health and status endpoints
   - `test_root_endpoint()` - Tests root health check
   - `test_cache_status_endpoint()` - Tests cache statistics
   - `test_cache_clear_endpoint()` - Tests cache clearing

4. **TestFHIREndpoints** - Tests all FHIR proxy endpoints
   - `test_patient_endpoint()` - Tests patient data retrieval
   - `test_condition_endpoint()` - Tests condition data retrieval
   - `test_medication_request_endpoint()` - Tests medication request data
   - `test_medication_administration_endpoint()` - Tests medication administration data
   - `test_encounter_endpoint()` - Tests encounter data
   - `test_observation_endpoint()` - Tests observation data
   - `test_procedure_endpoint()` - Tests procedure data
   - `test_specimen_endpoint()` - Tests specimen data

5. **TestCacheFunctionality** - Tests caching behavior
   - `test_cache_hit()` - Tests cache usage for repeated requests
   - `test_cache_expiry()` - Tests cache expiration after TTL

6. **TestErrorHandling** - Tests error scenarios
   - `test_fhir_server_error()` - Tests FHIR server error handling
   - `test_http_exception()` - Tests HTTP exception handling

7. **TestRateLimiting** - Tests rate limiting middleware
   - `test_rate_limiting_middleware()` - Tests rate limiting enforcement

8. **TestParameterHandling** - Tests parameter processing
   - `test_optional_parameters()` - Tests optional parameter handling

## 🚀 Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# Using pytest directly
pytest test_main.py -v

# Using the test runner
python run_tests.py run
```

### Run Specific Tests

```bash
# Run a specific test class
pytest test_main.py::TestCacheFunctions -v

# Run a specific test method
pytest test_main.py::TestCacheFunctions::test_get_cache_key -v

# Using the test runner
python run_tests.py run TestCacheFunctions::test_get_cache_key
```

### List Available Tests

```bash
python run_tests.py list
```

## 📊 Test Coverage

The tests cover:

- ✅ **Cache Management**: Key generation, cacheable detection, TTL handling
- ✅ **Rate Limiting**: Request counting, window management, cleanup
- ✅ **API Endpoints**: All FHIR resource endpoints
- ✅ **Error Handling**: FHIR server errors, HTTP exceptions
- ✅ **Parameter Processing**: Optional parameters, query string handling
- ✅ **Health Checks**: Status endpoints, cache statistics

## 🔧 Test Configuration

### Mocking Strategy

- **FHIR Server**: All tests mock `fetch_from_fhir()` to avoid external dependencies
- **Time-based Tests**: Cache expiry tests manually manipulate timestamps
- **Rate Limiting**: Tests use isolated rate limiter instances

### Test Data

- **Mock Responses**: Realistic FHIR Bundle responses
- **Test Parameters**: Various parameter combinations
- **Error Scenarios**: Network errors, HTTP exceptions

## 🐛 Debugging Tests

### Verbose Output

```bash
pytest test_main.py -v -s
```

### Debug Specific Test

```bash
# Add breakpoint in test
import pdb; pdb.set_trace()

# Run with debugger
python -m pdb -m pytest test_main.py::TestCacheFunctions::test_get_cache_key
```

### Test Isolation

Each test class uses `setup_method()` to ensure clean state:
- Cache is cleared before each test
- Rate limiter is reset
- Mock objects are reset

## 📈 Continuous Integration

The tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Backend Tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest test_main.py -v
```

## 🎯 Test Quality

- **Isolation**: Tests don't depend on each other
- **Mocking**: No external dependencies
- **Coverage**: All major functionality tested
- **Realistic**: Uses real FHIR data structures
- **Maintainable**: Clear test names and documentation

## 🔄 Adding New Tests

When adding new functionality:

1. **Add test class** for new feature
2. **Mock external dependencies**
3. **Test both success and error cases**
4. **Update this documentation**
5. **Run all tests** to ensure no regressions

Example:
```python
class TestNewFeature:
    def test_new_feature_success(self):
        # Test successful case
        pass
    
    def test_new_feature_error(self):
        # Test error case
        pass
```
