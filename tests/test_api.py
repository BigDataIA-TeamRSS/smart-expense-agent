"""
Tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import app module
import src.app.main as app_module


@pytest.fixture
def app_client():
    """Create test client"""
    # Patch the imported functions in the app module
    with patch.object(app_module, 'exchange_public_token') as mock_exchange, \
         patch.object(app_module, 'get_transactions') as mock_get_transactions:
        
        # Set default return values
        mock_exchange.return_value = ("access-token", "item-id")
        mock_get_transactions.return_value = []
        
        client = TestClient(app_module.app)
        
        # Store mocks for use in tests
        client.mock_exchange = mock_exchange
        client.mock_get_transactions = mock_get_transactions
        
        yield client


class TestPlaidEndpoints:
    """Tests for Plaid-related API endpoints"""
    
    def test_exchange_token_success(self, app_client):
        """Test successful token exchange"""
        app_client.mock_exchange.return_value = ("access-sandbox-xxx", "item-xxx")
        
        response = app_client.post(
            "/api/plaid/exchange",
            json={"public_token": "public-sandbox-xxx"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["item_id"] == "item-xxx"
        assert "message" in data
        app_client.mock_exchange.assert_called_once_with("public-sandbox-xxx")
    
    def test_exchange_token_failure(self, app_client):
        """Test token exchange failure"""
        app_client.mock_exchange.side_effect = Exception("Invalid token")
        
        response = app_client.post(
            "/api/plaid/exchange",
            json={"public_token": "invalid-token"}
        )
        
        assert response.status_code == 400
        assert "detail" in response.json()
    
    def test_exchange_token_missing_field(self, app_client):
        """Test token exchange with missing field"""
        response = app_client.post(
            "/api/plaid/exchange",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_fetch_transactions_success(self, app_client, mock_transactions_list):
        """Test successful transaction fetch"""
        app_client.mock_get_transactions.return_value = mock_transactions_list
        
        response = app_client.get(
            "/api/plaid/transactions",
            params={"access_token": "access-sandbox-xxx"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "transactions" in data
        assert data["count"] == len(mock_transactions_list)
        assert len(data["transactions"]) == len(mock_transactions_list)
        app_client.mock_get_transactions.assert_called_once()
    
    def test_fetch_transactions_failure(self, app_client):
        """Test transaction fetch failure"""
        app_client.mock_get_transactions.side_effect = Exception("Invalid access token")
        
        response = app_client.get(
            "/api/plaid/transactions",
            params={"access_token": "invalid-token"}
        )
        
        assert response.status_code == 400
    
    def test_fetch_transactions_missing_token(self, app_client):
        """Test transaction fetch without access token"""
        response = app_client.get("/api/plaid/transactions")
        
        assert response.status_code == 422  # Validation error


class TestAPIHealth:
    """Tests for API health and basic functionality"""
    
    def test_app_initialization(self, app_client):
        """Test that the FastAPI app initializes correctly"""
        assert app_module.app is not None
        assert app_module.app.title == "Smart Expense Analyzer"
    
    def test_api_docs_available(self, app_client):
        """Test that API documentation is available"""
        response = app_client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_schema(self, app_client):
        """Test that OpenAPI schema is available"""
        response = app_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
