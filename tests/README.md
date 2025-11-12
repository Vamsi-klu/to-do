# Test Suite

Comprehensive test suite for the Todo application with AI features.

## Test Coverage: 97.61%

### Test Statistics
- **Total Tests**: 71
- **Passing**: 71
- **Coverage**: 97.61%
- **Target**: 95%+ ✅

## Test Modules

### 1. test_ai_summary.py (10 tests)
Unit tests for AI summary endpoint:
- Authentication requirements
- Summary generation with/without todos
- OpenAI API integration
- Error handling (missing API key, API errors)
- Task count limits
- Response format validation
- System prompt and temperature settings

### 2. test_ai_suggestions.py (12 tests)
Unit tests for AI suggestions endpoint:
- Authentication requirements
- Suggestion generation with/without todos
- OpenAI API integration
- Task completion status display
- Error handling
- Task limits in prompts
- Response format validation
- System prompt and temperature settings

### 3. test_integration.py (11 tests)
Integration tests covering:
- **Authentication Flow**: Complete register/login/logout flow
- **Todo Operations**: Full CRUD workflow
- **AI Workflow**: Summary and suggestions with todos
- **User Isolation**: Data access restrictions
- **Error Handling**: 404s, invalid payloads, missing fields

### 4. test_models.py (9 tests)
Unit tests for database models:
- **User Model**: Creation, password hashing, unique usernames, relationships
- **Todo Model**: Creation, defaults, updates, deletion, relationships

### 5. test_routes.py (29 tests)
Unit tests for application routes:
- **Auth Routes**: Login/register pages, success/failure cases, redirects
- **Todo Routes**: CRUD operations, authentication, error handling
- **Serialization**: Todo serialization validation

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run with coverage:
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_ai_summary.py -v
```

### Run specific test class:
```bash
pytest tests/test_ai_summary.py::TestAISummaryEndpoint -v
```

### Run specific test:
```bash
pytest tests/test_ai_summary.py::TestAISummaryEndpoint::test_ai_summary_with_todos_success -v
```

### Run by markers:
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m ai            # Run only AI feature tests
```

## Coverage Reports

After running tests with coverage, view the HTML report:
```bash
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Test Configuration

- **pytest.ini**: Pytest configuration with coverage settings
- **.coveragerc**: Coverage tool configuration
- **conftest.py**: Shared fixtures and test setup

## Key Fixtures

- `app`: Flask application instance
- `client`: Test client for making requests
- `db`: Database instance with test data
- `test_user`: Pre-created test user
- `authenticated_client`: Logged-in test client
- `test_todos`: Sample todo items
- `mock_openai_response`: Mock OpenAI API responses

## Coverage by Module

| Module      | Coverage | Missing Lines |
|-------------|----------|---------------|
| app.py      | 97.21%   | 23-24, 59, 207, 294 |
| database.py | 100.00%  | None |
| models.py   | 100.00%  | None |
| **TOTAL**   | **97.61%** | **5 lines** |

## Test Categories

### Unit Tests (51 tests)
- Individual function/method testing
- Mocked external dependencies
- Fast execution

### Integration Tests (20 tests)
- End-to-end workflows
- Multiple components interaction
- Database integration

## Continuous Integration

These tests are designed to run in CI/CD pipelines with the following requirements:
- Python 3.8+
- All dependencies from requirements.txt
- In-memory SQLite database
- Mocked OpenAI API calls

## Adding New Tests

1. Create test file in `tests/` directory
2. Import required fixtures from `conftest.py`
3. Use pytest markers: `@pytest.mark.unit` or `@pytest.mark.integration`
4. Follow naming convention: `test_*.py`
5. Run tests to verify coverage doesn't drop below 95%
