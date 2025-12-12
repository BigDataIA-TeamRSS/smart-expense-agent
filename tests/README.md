# Test Suite Documentation

This directory contains comprehensive tests for the Smart Expense Analyzer project.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_api.py              # API endpoint tests
├── test_agents.py           # Agent tests (Agent 1, Agent 2, Orchestrator)
├── test_agent_tools.py      # Agent tool tests (categorization, fraud, subscriptions)
└── test_integrations.py     # Integration tests (Plaid, Database)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_api.py
```

### Run specific test class
```bash
pytest tests/test_api.py::TestPlaidEndpoints
```

### Run specific test function
```bash
pytest tests/test_api.py::TestPlaidEndpoints::test_exchange_token_success
```

### Run with coverage
```bash
pytest --cov=src --cov=agents --cov=agent_tools --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

### Run only fast tests (exclude slow markers)
```bash
pytest -m "not slow"
```

## Test Categories

### Unit Tests
- Test individual functions and methods in isolation
- Use mocks for external dependencies
- Fast execution

### Integration Tests
- Test interactions between components
- May use real database connections (test database)
- Slower execution

### API Tests
- Test FastAPI endpoints
- Use TestClient for HTTP requests
- Mock external services (Plaid, Gemini)

## Mocking Strategy

### External Services
- **Plaid API**: Mocked using `unittest.mock`
- **Gemini AI**: Mocked LLM responses
- **Database**: Mocked database sessions
- **MCP Toolbox**: Mocked toolbox client

### Fixtures
Common fixtures are defined in `conftest.py`:
- `mock_user_id`: Sample user ID
- `mock_transaction`: Sample transaction data
- `mock_transactions_list`: List of sample transactions
- `mock_plaid_response`: Mock Plaid API response
- `mock_database`: Mock database instance
- `mock_gemini_client`: Mock Gemini AI client

## Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import patch, MagicMock

class TestMyFeature:
    """Tests for MyFeature"""
    
    @patch('module.external_dependency')
    def test_feature_success(self, mock_dependency, mock_fixture):
        """Test successful feature execution"""
        # Arrange
        mock_dependency.return_value = "expected_value"
        
        # Act
        result = my_function(mock_fixture)
        
        # Assert
        assert result == "expected_result"
        mock_dependency.assert_called_once()
```

## Best Practices

1. **Use descriptive test names**: `test_feature_scenario_expected_result`
2. **One assertion per test**: Focus on one behavior
3. **Arrange-Act-Assert pattern**: Clear test structure
4. **Mock external dependencies**: Keep tests fast and isolated
5. **Use fixtures**: Share common test data
6. **Test edge cases**: Include error scenarios
7. **Keep tests independent**: No test should depend on another

## Continuous Integration

Tests should be run in CI/CD pipeline:
- On every pull request
- Before merging to main
- On scheduled basis

## Coverage Goals

- **Unit Tests**: >80% code coverage
- **API Tests**: All endpoints covered
- **Agent Tests**: All agent workflows covered
- **Integration Tests**: Critical paths covered

