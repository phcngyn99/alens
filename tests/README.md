# Alens E2E Testing Framework

Automated end-to-end testing using Selenium WebDriver with Python and pytest.

## Overview

This testing framework provides comprehensive UI testing for the Alens application, including:
- User authentication (login/logout)
- Database connections management
- Schema browsing
- Intent definition
- Error handling scenarios

## Prerequisites

- Docker and Docker Compose installed
- Alens application running (`make up`)

## Quick Start

```bash
# 1. Ensure the application is running
make up

# 2. Build the test container (first time only)
make test-build

# 3. Run all tests
make test

# 4. View the test report
make test-report
```

## Test Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all E2E tests |
| `make test-build` | Build the test container |
| `make test-verbose` | Run tests with verbose output |
| `make test-file FILE=test_login.py` | Run a specific test file |
| `make test-report` | Open HTML test report in browser |
| `make test-clean` | Remove test reports |

## Test Structure

```
tests/
├── Dockerfile           # Selenium container configuration
├── requirements.txt     # Python dependencies
├── conftest.py         # Pytest fixtures and configuration
├── pages/              # Page Object Model classes
│   ├── __init__.py
│   ├── base_page.py    # Base page with common methods
│   ├── login_page.py   # Login page interactions
│   ├── connections_page.py
│   ├── schema_page.py
│   └── intent_page.py
├── reports/            # Generated test reports
│   └── report.html
├── test_login.py       # Login functionality tests
├── test_connections.py # Connections page tests
├── test_schema_browser.py
├── test_intent_page.py
└── test_error_handling.py
```

## Test Categories

### 1. Login Tests (`test_login.py`)
- Login page loads correctly
- Successful login with default credentials
- Invalid credentials show error
- Empty credentials handling
- Unauthenticated redirect to login

### 2. Connections Tests (`test_connections.py`)
- Connections page loads after login
- Add Connection button present
- View Schema button for connections
- Define Intent button for connections

### 3. Schema Browser Tests (`test_schema_browser.py`)
- Schema page loads for connections
- Connection error displayed for unavailable DB
- Schema dropdown functionality
- Tables load when schema selected

### 4. Intent Page Tests (`test_intent_page.py`)
- Intent page loads correctly
- Tables of Interest section visible
- Schema/table dropdowns work
- Connection error handling

### 5. Error Handling Tests (`test_error_handling.py`)
- Invalid connection ID handling
- Connection error messages
- API error response format
- Authentication errors (401)

## Configuration

Environment variables (set in docker-compose.yml):

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://frontend` | Application URL |
| `API_URL` | `http://backend:8000` | API URL |
| `DEFAULT_USERNAME` | `wnkadmin` | Test user username |
| `DEFAULT_PASSWORD` | `wnkadmin` | Test user password |
| `HEADLESS` | `true` | Run browser headless |
| `IMPLICIT_WAIT` | `10` | Implicit wait seconds |
| `EXPLICIT_WAIT` | `20` | Explicit wait seconds |

## Test Reports

After running tests, an HTML report is generated at:
```
tests/reports/report.html
```

The report includes:
- Test pass/fail status
- Execution time
- Error messages and stack traces
- Screenshots on failure (if configured)

## Page Object Model

The framework uses the Page Object Model (POM) pattern:

```python
from pages.login_page import LoginPage

def test_login(driver, base_url, credentials):
    login_page = LoginPage(driver, base_url)
    login_page.navigate()
    login_page.login(credentials["username"], credentials["password"])
    login_page.wait_for_redirect()
    assert login_page.is_logged_in()
```

## Adding New Tests

1. Create a new test file (e.g., `test_new_feature.py`)
2. Import required page objects
3. Use fixtures from `conftest.py`

```python
import pytest
from pages.connections_page import ConnectionsPage

class TestNewFeature:
    def test_something(self, logged_in_driver, base_url):
        page = ConnectionsPage(logged_in_driver, base_url)
        # Your test logic here
```

## Troubleshooting

### Tests fail to connect
Ensure the application is running:
```bash
make status
```

### Chrome driver errors
The container automatically installs matching ChromeDriver version.

### Timeout errors
Increase wait times in environment variables or test code.

### View test logs
```bash
docker-compose --profile test logs tests
```

