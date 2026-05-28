# Test Suite for Vulnerable Todo Application

This directory contains comprehensive tests for the deliberately vulnerable todo application.

## Overview

The test suite is designed to:
- Verify application functionality
- Document security vulnerabilities through tests
- Achieve ~80% code coverage
- Serve as educational examples

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_models.py           # Database models tests (12 tests)
├── test_auth.py             # Authentication tests (17 tests)
├── test_database.py         # Todo operations tests (24 tests)
├── test_utils.py            # Utility functions tests (27 tests)
└── test_routes.py           # Flask routes tests (22 tests)
```

**Total: ~102 tests covering all major functionality**

## Running Tests

### Install Dependencies

```bash
# Using uv (recommended)
uv pip install pytest pytest-cov pytest-flask

# Or using pip
pip install pytest pytest-cov pytest-flask
```

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Tests

```bash
# Run single test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestAuthentication

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_authenticate_user_success

# Run tests matching pattern
pytest -k "authentication"
```

### Coverage Options

```bash
# Fail if coverage is below 75%
pytest --cov=src --cov-fail-under=75

# Generate multiple report formats
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term

# Show lines not covered
pytest --cov=src --cov-report=term-missing
```

## Test Coverage by Module

### models.py (Database Layer)
- Database initialization and schema
- Query execution methods
- Connection handling
- Admin user setup

### auth.py (Authentication)
- User registration (validation, duplicates)
- User authentication (success/failure paths)
- Session management (create, retrieve, delete)
- SQL injection vulnerabilities
- Authentication bypass demonstrations

### database.py (Todo Operations)
- CRUD operations (Create, Read, Update, Delete)
- IDOR (Insecure Direct Object Reference) vulnerabilities
- SQL injection in queries
- Search functionality
- Todo sharing features

### utils.py (Utility Functions)
- Password hashing (MD5 weakness demonstration)
- Session token generation (predictability)
- Session serialization (pickle security issues)
- Command injection (shell=True vulnerability)
- Path traversal (directory traversal)
- XXE (XML External Entity) attacks
- SSRF (Server-Side Request Forgery)
- File operations

### routes (Flask Application)
- Authentication routes (login, register, logout)
- Todo management endpoints
- File upload/download (path traversal)
- Search functionality (SQL injection)
- Admin panel (authorization checks)
- API endpoints (no authentication)
- XSS, CSRF vulnerability verification

## Fixtures

### Available Fixtures

- `app`: Flask application instance with test database
- `client`: Flask test client for making HTTP requests
- `runner`: Flask CLI test runner
- `test_user`: Test user credentials
- `admin_user`: Admin user credentials

### Example Usage

```python
def test_example(client, test_user):
    response = client.post('/login', data={
        'username': test_user['username'],
        'password': test_user['password']
    })
    assert response.status_code == 200
```

## Writing New Tests

### Test Class Structure

```python
class TestFeature:
    """Test feature description."""

    def test_success_case(self, app):
        """Test successful operation."""
        with app.app_context():
            # Test code
            pass

    def test_failure_case(self, app):
        """Test failure handling."""
        with app.app_context():
            # Test code
            pass

    def test_vulnerability(self, app):
        """Test that vulnerability exists (educational)."""
        with app.app_context():
            # Demonstrate vulnerability
            pass
```

### Best Practices

1. **One assertion focus per test** - Keep tests focused
2. **Descriptive names** - Name tests `test_what_when_expected`
3. **Use fixtures** - Reuse common setup via fixtures
4. **Document vulnerabilities** - Add comments explaining security issues
5. **Handle errors** - Use try/except for network-dependent tests

## Coverage Goals

- **Target**: 75-80% overall coverage
- **Priority areas**: Authentication, authorization, data operations
- **Lower priority**: Static routes, simple getters

## Educational Value

These tests serve multiple purposes:

1. **Verify Functionality**: Ensure the app works as intended
2. **Document Vulnerabilities**: Each vulnerability has tests demonstrating it
3. **Security Learning**: Students can see how vulnerabilities are exploited
4. **Good Testing Practices**: Examples of pytest best practices

## Important Notes

⚠️ **For Educational Use Only**

- These tests intentionally verify that vulnerabilities exist
- They demonstrate how vulnerabilities can be exploited
- Never use this code or these patterns in production
- Always follow secure coding practices in real applications

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Import Errors

If you get import errors, ensure:
- You're running from the project root
- `src/` is in PYTHONPATH
- All dependencies are installed

### Database Errors

Tests use temporary databases. If you see database errors:
- Check file permissions
- Ensure /tmp is writable
- Verify SQLite is installed

### Network Tests

Some tests (SSRF, URL fetching) require network access:
- They're marked to skip if network is unavailable
- Use pytest markers to skip: `pytest -m "not slow"`

## Questions?

For educational questions about the vulnerabilities or testing patterns, refer to:
- `VULNERABILITIES.md` - Detailed vulnerability documentation
- `EXPLOITS.md` - Exploitation examples
- Test file comments - Inline explanations
