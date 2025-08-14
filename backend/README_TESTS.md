# Testing Guide for EHR Backend

This document explains the updated test structure and how to run tests with the new architecture.

## Test Structure Overview

### Backend Tests

The backend tests have been completely rewritten to work with the new architecture:

- **`test_main_updated.py`**: Main test file with comprehensive test coverage
- **`pytest.ini`**: Pytest configuration with coverage settings
- **`run_tests.py`**: Test runner script with various options

### Frontend Tests

Frontend tests are located in `src/__tests__/`:

- **`App.test.tsx`**: Tests for the main App component
- **`hooks.test.tsx`**: Tests for custom React hooks

## Running Tests

### Backend Tests

#### Quick Start
```bash
cd backend
python run_tests.py
```

#### Advanced Options
```bash
# Run with verbose output
python run_tests.py --verbose

# Run without coverage
python run_tests.py --no-coverage

# Run specific test
python run_tests.py --test TestCacheSystem::test_cache_basic_operations

# Run only unit tests
python run_tests.py --markers unit

# Run only integration tests
python run_tests.py --markers integration
```

#### Direct Pytest Commands
```bash
# Run all tests
pytest test_main_updated.py -v

# Run with coverage
pytest test_main_updated.py --cov=. --cov-report=html

# Run specific test class
pytest test_main_updated.py::TestCacheSystem -v

# Run specific test method
pytest test_main_updated.py::TestCacheSystem::test_cache_basic_operations -v
```

### Frontend Tests

#### Quick Start
```bash
# From project root
npm test

# Run with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci
```

#### Advanced Options
```bash
# Run specific test file
npm test -- --testPathPattern=App.test.tsx

# Run tests in watch mode
npm test -- --watch

# Run tests with verbose output
npm test -- --verbose
```

### Run All Tests

```bash
# Run both backend and frontend tests
cd backend
python run_tests.py --all
```

## Test Categories

### Backend Test Categories

1. **Configuration Tests** (`TestConfiguration`)
   - Configuration loading
   - Environment detection

2. **Cache System Tests** (`TestCacheSystem`)
   - Basic cache operations
   - Cache expiration
   - Key normalization
   - Cache statistics

3. **Rate Limiter Tests** (`TestRateLimiter`)
   - Basic rate limiting
   - Window expiry
   - Statistics tracking

4. **Database Tests** (`TestDatabaseManager`)
   - Database initialization
   - Basic operations
   - Connection pooling

5. **Exception Handling Tests** (`TestExceptionHandling`)
   - Custom exception classes
   - Error handling

6. **API Endpoint Tests**
   - Health endpoints
   - Local database endpoints
   - FHIR proxy endpoints
   - Error handling

### Frontend Test Categories

1. **Component Tests** (`App.test.tsx`)
   - Component rendering
   - User interactions
   - Error handling
   - Loading states

2. **Hook Tests** (`hooks.test.tsx`)
   - Custom hook functionality
   - State management
   - API integration
   - Error handling

## Test Environment Setup

### Backend Test Environment

The test environment is automatically configured with:

- **In-memory SQLite database**: `:memory:` for fast, isolated tests
- **Short cache TTL**: 0.1 seconds for quick expiration
- **Short rate limit window**: 1 second for quick testing
- **Reduced logging**: WARNING level to reduce noise
- **Test environment detection**: Automatic detection via environment variables

### Frontend Test Environment

- **Mocked API client**: All API calls are mocked
- **Mocked theme provider**: Consistent theme for tests
- **Mocked data**: Realistic test data for all components

## Test Data

### Backend Test Data

The tests use realistic mock data that matches the FHIR specification:

```python
mock_patients = [
    {
        "id": "test-patient-1",
        "family_name": "TestPatient",
        "gender": "male",
        "birth_date": "1990-01-01",
        # ... more fields
    }
]
```

### Frontend Test Data

Frontend tests use TypeScript interfaces that match the backend:

```typescript
const mockPatients: LocalPatient[] = [
  {
    id: 'test-patient-1',
    family_name: 'TestPatient',
    gender: 'male',
    birth_date: '1990-01-01',
    // ... more fields
  }
];
```

## Coverage Requirements

### Backend Coverage

- **Minimum coverage**: 80%
- **Coverage reports**: HTML and terminal output
- **Coverage areas**: All new modules and updated functions

### Frontend Coverage

- **Component coverage**: All React components
- **Hook coverage**: All custom hooks
- **API integration**: All API client functions

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          python run_tests.py --no-coverage

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node.js
        uses: actions/setup-node@v2
        with:
          node-version: 18
      - name: Install dependencies
        run: npm install
      - name: Run tests
        run: npm run test:ci
```

## Debugging Tests

### Backend Test Debugging

1. **Run with verbose output**:
   ```bash
   python run_tests.py --verbose
   ```

2. **Run specific failing test**:
   ```bash
   python run_tests.py --test TestCacheSystem::test_cache_basic_operations
   ```

3. **Use pytest debugger**:
   ```bash
   pytest test_main_updated.py::TestCacheSystem::test_cache_basic_operations -s --pdb
   ```

### Frontend Test Debugging

1. **Run in watch mode**:
   ```bash
   npm test -- --watch
   ```

2. **Run with verbose output**:
   ```bash
   npm test -- --verbose
   ```

3. **Debug specific test**:
   ```bash
   npm test -- --testNamePattern="should render patient list"
   ```

## Common Issues and Solutions

### Backend Test Issues

1. **Import errors**: Make sure all new modules are properly imported
2. **Database errors**: Tests use in-memory database, no file system access needed
3. **Cache conflicts**: Each test resets the cache automatically
4. **Rate limiter conflicts**: Each test resets the rate limiter automatically

### Frontend Test Issues

1. **Mock errors**: Ensure all API calls are properly mocked
2. **Async test failures**: Use `waitFor` for async operations
3. **Component rendering errors**: Check that all required props are provided
4. **Hook testing errors**: Use `renderHook` for testing custom hooks

## Best Practices

### Writing Backend Tests

1. **Use descriptive test names**: Clear, descriptive test method names
2. **Test one thing at a time**: Each test should test one specific behavior
3. **Use proper setup/teardown**: Reset state between tests
4. **Mock external dependencies**: Don't rely on external services
5. **Test error conditions**: Always test error handling

### Writing Frontend Tests

1. **Test user interactions**: Focus on user behavior, not implementation
2. **Use realistic data**: Mock data should match real data structure
3. **Test error states**: Always test error handling and loading states
4. **Test accessibility**: Ensure components are accessible
5. **Use proper assertions**: Use semantic assertions that match user expectations

## Performance Considerations

### Backend Test Performance

- **In-memory database**: Fast database operations
- **Short timeouts**: Quick test execution
- **Minimal logging**: Reduced I/O overhead
- **Parallel execution**: Tests can run in parallel

### Frontend Test Performance

- **Mocked API calls**: No network overhead
- **Fast rendering**: Components render quickly
- **Minimal DOM manipulation**: Focus on essential interactions
- **Efficient assertions**: Use efficient DOM queries

## Future Improvements

1. **Integration tests**: Add end-to-end tests
2. **Performance tests**: Add performance benchmarking
3. **Security tests**: Add security vulnerability tests
4. **Accessibility tests**: Add automated accessibility testing
5. **Visual regression tests**: Add visual testing for UI components
