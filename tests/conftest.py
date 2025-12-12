"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test fixtures
@pytest.fixture
def mock_user_id():
    """Sample user ID for testing"""
    return "fd47f678-0c8a-42b5-8af2-936ec0e370c5"

@pytest.fixture
def mock_transaction():
    """Sample transaction data"""
    return {
        "transaction_id": "txn_test_123",
        "user_id": "fd47f678-0c8a-42b5-8af2-936ec0e370c5",
        "amount": -45.67,
        "date": "2024-12-01",
        "name": "AMAZON.COM PURCHASE",
        "merchant_name": "AMAZON.COM",
        "category": ["Shops", "Supermarkets"],
        "personal_finance_category": {
            "primary": "GENERAL_MERCHANDISE",
            "detailed": "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES"
        },
        "payment_channel": "online",
        "transaction_type": "place"
    }

@pytest.fixture
def mock_transactions_list(mock_transaction):
    """List of sample transactions"""
    return [
        mock_transaction,
        {
            **mock_transaction,
            "transaction_id": "txn_test_456",
            "amount": -12.99,
            "merchant_name": "NETFLIX",
            "date": "2024-11-15"
        },
        {
            **mock_transaction,
            "transaction_id": "txn_test_789",
            "amount": -1500.00,
            "merchant_name": "UNKNOWN MERCHANT",
            "date": "2024-11-20"
        }
    ]

@pytest.fixture
def mock_plaid_response():
    """Mock Plaid API response"""
    return {
        "access_token": "access-sandbox-xxx",
        "item_id": "item-xxx",
        "link_token": "link-sandbox-xxx"
    }

@pytest.fixture
def mock_database():
    """Mock database instance"""
    db = MagicMock()
    db.get_user.return_value = {
        "id": "fd47f678-0c8a-42b5-8af2-936ec0e370c5",
        "username": "testuser",
        "email": "test@example.com"
    }
    db.get_user_accounts.return_value = [
        {
            "id": "acc_123",
            "account_id": "plaid_acc_123",
            "name": "Checking Account",
            "type": "depository",
            "balance": 5000.00
        }
    ]
    db.get_transactions.return_value = []
    return db

@pytest.fixture
def mock_gemini_client():
    """Mock Gemini AI client"""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test response"
    client.models.generate_content.return_value = mock_response
    return client

@pytest.fixture
def mock_toolbox():
    """Mock MCP Toolbox client"""
    toolbox = MagicMock()
    toolbox.call_tool.return_value = {
        "status": "success",
        "data": []
    }
    return toolbox

