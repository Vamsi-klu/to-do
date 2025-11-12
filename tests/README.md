# Test Suite

This directory contains the comprehensive test suite for the To-Do application.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py -v
```

## Test Files

- **`conftest.py`**: Pytest fixtures and test configuration
- **`test_models.py`**: Unit tests for User and Todo models (29 tests)
- **`test_database.py`**: Unit tests for database operations (14 tests)
- **`test_app.py`**: Unit tests for routes and API endpoints (51 tests)
- **`test_integration.py`**: Integration tests for complete workflows (13 tests)

## Total: 105 Tests | 99.10% Coverage

## Test Categories

### Unit Tests (93 tests)
Test individual components in isolation:
- Models (User, Todo)
- Database operations
- Routes (index, login, register, logout)
- API endpoints (list, create, update, delete)

### Integration Tests (13 tests)
Test complete user workflows:
- Authentication flow
- Todo CRUD operations
- Multi-user scenarios
- End-to-end journeys

## Key Features

✅ **High Coverage**: 99.10% code coverage
✅ **Fast Execution**: ~27 seconds for full suite
✅ **Isolated Tests**: Each test uses fresh database
✅ **Comprehensive**: Covers happy paths, edge cases, and errors
✅ **Well Organized**: Clear structure and naming conventions

## Common Commands

```bash
# Run tests matching pattern
pytest -k "login" -v

# Run specific test class
pytest tests/test_app.py::TestLoginRoute -v

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Enter debugger on failure
pytest --pdb

# Generate HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Writing New Tests

1. Add test to appropriate file
2. Use existing fixtures from `conftest.py`
3. Follow naming convention: `test_<feature>_<scenario>`
4. Include docstring explaining what's being tested
5. Use Arrange-Act-Assert pattern

Example:
```python
def test_user_login_success(client, test_user):
    """Test successful user login with valid credentials."""
    # Arrange
    credentials = {"username": "testuser", "password": "testpass123"}

    # Act
    response = client.post("/login", data=credentials)

    # Assert
    assert response.status_code == 302
    assert "/" in response.location
```

## See Also

- [`TESTING.md`](../TESTING.md) - Comprehensive testing documentation
- [`pytest.ini`](../pytest.ini) - Pytest configuration
- [`.coveragerc`](../.coveragerc) - Coverage configuration
