# Testing Documentation

## Overview

This document provides comprehensive information about the testing strategy, infrastructure, and guidelines for the To-Do application. The test suite achieves **99.10% code coverage** across all modules, exceeding the 95% target.

## Test Statistics

- **Total Tests**: 105 tests
- **Code Coverage**: 99.10%
- **Branch Coverage**: 98.65%
- **All Tests Passing**: ✅ Yes

### Coverage by Module

| Module | Statements | Coverage |
|--------|-----------|----------|
| app.py | 119 | 98.95% |
| database.py | 7 | 100.00% |
| models.py | 23 | 100.00% |
| **Overall** | **149** | **99.10%** |

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_models.py              # Unit tests for database models
├── test_database.py            # Unit tests for database operations
├── test_app.py                 # Unit tests for routes and API endpoints
└── test_integration.py         # Integration tests for complete workflows
```

## Running Tests

### Run All Tests

```bash
python3 -m pytest
```

### Run with Coverage Report

```bash
python3 -m pytest --cov=. --cov-report=term-missing
```

### Run Specific Test File

```bash
python3 -m pytest tests/test_models.py -v
```

### Run Specific Test Class

```bash
python3 -m pytest tests/test_app.py::TestLoginRoute -v
```

### Run Specific Test

```bash
python3 -m pytest tests/test_app.py::TestLoginRoute::test_login_post_success -v
```

### Generate HTML Coverage Report

```bash
python3 -m pytest --cov=. --cov-report=html
# Open htmlcov/index.html in a browser
```

## Test Categories

### 1. Unit Tests - Models (`test_models.py`)

**Purpose**: Test individual model behavior and database constraints.

**Test Classes**:
- `TestUserModel`: 12 tests covering user creation, authentication, and relationships
- `TestTodoModel`: 17 tests covering todo creation, validation, and relationships

**Key Test Areas**:
- User password hashing and validation
- Model field constraints (required, unique, max length)
- Database relationships and cascading deletes
- Timestamp management (created_at, updated_at)
- Data isolation between users

### 2. Unit Tests - Database (`test_database.py`)

**Purpose**: Test database initialization and operations.

**Test Classes**:
- `TestDatabaseInitialization`: 14 tests covering database setup and operations

**Key Test Areas**:
- Database initialization and table creation
- CRUD operations (Create, Read, Update, Delete)
- Transaction management and rollbacks
- Query functionality
- Constraint enforcement (foreign keys, unique constraints)
- Cascade delete operations

### 3. Unit Tests - Application (`test_app.py`)

**Purpose**: Test individual routes and API endpoints.

**Test Classes**:
- `TestAppCreation`: Application initialization and configuration
- `TestIndexRoute`: Main page access control
- `TestLoginRoute`: Login functionality and validation
- `TestRegisterRoute`: User registration and validation
- `TestLogoutRoute`: Logout functionality
- `TestAPIListTodos`: Todo listing API
- `TestAPICreateTodo`: Todo creation API
- `TestAPIUpdateTodo`: Todo update API
- `TestAPIDeleteTodo`: Todo deletion API
- `TestSerializeTodo`: Todo serialization

**Key Test Areas**:
- Route access control (authentication required)
- Form validation and error handling
- Session management
- API input validation
- API response formats
- User data isolation
- Edge cases (empty inputs, whitespace, special characters)

### 4. Integration Tests (`test_integration.py`)

**Purpose**: Test complete user workflows and multi-step operations.

**Test Classes**:
- `TestAuthenticationFlow`: Complete authentication workflows
- `TestTodoCRUDFlow`: Complete todo management workflows
- `TestCompleteUserJourney`: End-to-end user scenarios

**Key Test Areas**:
- Registration → Login → Logout workflows
- Complete todo lifecycle (Create → Read → Update → Delete)
- Multi-user scenarios and data isolation
- Session persistence across requests
- Error recovery and handling
- Concurrent operations
- Real-world user journeys

## Test Fixtures

### Core Fixtures (`conftest.py`)

- `app`: Fresh Flask application instance for each test
- `client`: Test client for making HTTP requests
- `authenticated_client`: Pre-authenticated test client
- `test_user`: Test user with credentials (username: testuser, password: testpass123)
- `another_user`: Second test user for multi-user scenarios
- `test_todos`: Pre-created sample todos for testing
- `app_context`: Application context for tests that need it

### Fixture Characteristics

- **Function Scope**: All fixtures use function scope for test isolation
- **Automatic Cleanup**: Fixtures automatically clean up after each test
- **In-Memory Database**: Tests use SQLite in-memory database for speed
- **Isolated Sessions**: Each test gets a fresh database session

## Testing Best Practices

### 1. Test Isolation

Each test is completely independent:
- Fresh database for each test
- No shared state between tests
- Automatic cleanup after each test
- Tests can run in any order

### 2. Test Naming

Tests follow a clear naming convention:
```python
def test_<feature>_<scenario>_<expected_result>():
    """Test that <feature> <scenario> <expected_result>."""
```

Example: `test_login_post_invalid_username()`

### 3. Test Organization

Tests are organized by:
1. **Module**: Separate files for each module
2. **Class**: Related tests grouped in classes
3. **Functionality**: Tests ordered from basic to complex

### 4. Assertions

Tests use clear, specific assertions:
- Check status codes
- Verify response content
- Confirm database state
- Validate session data

### 5. Edge Cases

Tests cover:
- Empty inputs
- Whitespace-only inputs
- Maximum length inputs
- Invalid data types
- Missing required fields
- Unauthorized access attempts
- Concurrent operations

## Coverage Goals

- **Target**: 95% code coverage minimum
- **Achieved**: 99.10% code coverage
- **Branch Coverage**: Included in coverage metrics
- **Excluded**: Static files, templates, bootstrap utilities

## Continuous Integration

### Running Tests in CI

Tests are designed to run in CI environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    python3 -m pytest --cov=. --cov-report=xml --cov-report=term

- name: Check coverage
  run: |
    python3 -m pytest --cov=. --cov-fail-under=95
```

## Common Testing Scenarios

### Testing Authentication

```python
# Login a user
client.post("/login", data={
    "username": "testuser",
    "password": "testpass123"
})

# Access protected route
response = client.get("/")
assert response.status_code == 200
```

### Testing API Endpoints

```python
# Create a todo
response = client.post("/api/todos",
                       data=json.dumps({"text": "New task"}),
                       content_type="application/json")

assert response.status_code == 201
data = json.loads(response.data)
assert data["text"] == "New task"
```

### Testing Database Operations

```python
with app.app_context():
    # Create a user
    user = User(username="testuser")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Verify
    assert user.id is not None
```

## Troubleshooting

### Tests Failing Locally

1. **Check dependencies**: `pip install -r requirements.txt`
2. **Clean cache**: `rm -rf .pytest_cache __pycache__`
3. **Verify Python version**: Python 3.11+ recommended
4. **Check for stale database**: Tests use in-memory DB, no cleanup needed

### Coverage Not Meeting Target

1. **Generate detailed report**: `pytest --cov=. --cov-report=html`
2. **Open HTML report**: `htmlcov/index.html`
3. **Identify uncovered lines**: Look for red highlighting
4. **Write targeted tests**: Add tests for uncovered scenarios

### Slow Test Execution

Tests typically run in 25-30 seconds. If slower:
1. Check for network operations (should be mocked)
2. Verify using in-memory database
3. Reduce test data where possible
4. Run specific test files instead of full suite

## Adding New Tests

### Step 1: Identify Test Type

- **Unit Test**: Tests single function or method
- **Integration Test**: Tests multiple components together
- **End-to-End Test**: Tests complete user workflow

### Step 2: Create Test

```python
class TestNewFeature:
    """Test cases for new feature."""

    def test_feature_basic_case(self, client, test_user):
        """Test basic functionality of new feature."""
        # Arrange
        # ... setup

        # Act
        response = client.get("/new-feature")

        # Assert
        assert response.status_code == 200
```

### Step 3: Run and Verify

```bash
# Run new test
pytest tests/test_app.py::TestNewFeature -v

# Verify coverage
pytest --cov=. --cov-report=term-missing
```

## Test Data Management

### Test Users

- **testuser**: Primary test user (password: testpass123)
- **anotheruser**: Secondary test user (password: anotherpass123)

### Test Todos

Standard test todos include:
- "Buy groceries" (incomplete)
- "Write tests" (completed)
- "Deploy application" (incomplete)

### Database State

- Each test starts with clean database
- Fixtures create necessary data
- Tests can create additional data as needed
- Automatic cleanup after each test

## Security Testing

Tests include security scenarios:
- **Authentication**: Unauthorized access attempts
- **Authorization**: Accessing other users' data
- **Input Validation**: SQL injection, XSS attempts
- **Session Management**: Session hijacking scenarios

## Performance Testing

While not dedicated performance tests, integration tests verify:
- Multiple concurrent operations
- Bulk data operations
- Session persistence
- Database query efficiency

## Future Enhancements

Potential testing improvements:
1. **Frontend Testing**: Add JavaScript unit tests (Jest/Mocha)
2. **E2E Testing**: Add browser automation tests (Selenium/Playwright)
3. **Load Testing**: Add performance/load tests (Locust/k6)
4. **Security Scanning**: Add SAST/DAST tools
5. **Mutation Testing**: Add mutation testing for test quality

## Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Flask Testing**: https://flask.palletsprojects.com/en/latest/testing/
- **Coverage.py**: https://coverage.readthedocs.io/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/latest/core/testing.html

## Support

For questions or issues with tests:
1. Check this documentation
2. Review existing tests for examples
3. Run tests with `-v` flag for verbose output
4. Use `--pdb` flag to drop into debugger on failure

---

**Last Updated**: 2025-11-12
**Coverage Version**: 99.10%
**Total Tests**: 105
