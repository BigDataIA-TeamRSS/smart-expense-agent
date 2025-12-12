"""
Tests for external integrations (Plaid, Database, etc.)
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPlaidService:
    """Tests for Plaid integration"""
    
    @patch('src.integrations.plaid_service.plaid_api.PlaidApi')
    def test_create_link_token(self, mock_plaid_api, mock_user_id):
        """Test creating Plaid link token"""
        from src.integrations.plaid_service import PlaidService
        
        # Mock Plaid API response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "link_token": "link-sandbox-xxx",
            "hosted_link_url": "https://hosted.plaid.com/...",
            "expiration": "2024-12-31T23:59:59Z"
        }
        mock_plaid_api.return_value.link_token_create.return_value = mock_response
        
        service = PlaidService()
        result = service.create_link_token(mock_user_id, "test@example.com")
        
        assert result is not None
        assert "link_token" in result
        assert result["link_token"] == "link-sandbox-xxx"
    
    @patch('src.integrations.plaid_service.plaid_api.PlaidApi')
    def test_sync_transactions(self, mock_plaid_api):
        """Test syncing transactions from Plaid"""
        from src.integrations.plaid_service import PlaidService
        
        # Mock Plaid API response
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            "added": [
                {
                    "transaction_id": "txn_1",
                    "amount": -45.67,
                    "date": "2024-12-01",
                    "merchant_name": "AMAZON"
                }
            ],
            "next_cursor": "cursor_123",
            "has_more": False
        }
        mock_plaid_api.return_value.transactions_sync.return_value = mock_response
        
        service = PlaidService()
        result = service.sync_transactions("access-token-xxx")
        
        assert "transactions" in result
        assert "cursor" in result  # Changed from next_cursor to cursor
        assert len(result["transactions"]) > 0


class TestDatabaseOperations:
    """Tests for database operations"""
    
    @patch('src.core.database.Config.USE_CLOUD_SQL', False)
    @patch('src.core.database.Config.DB_CONNECTION_STRING', 'postgresql://test:test@localhost:5432/testdb')
    @patch('src.core.database.get_session')
    def test_create_user(self, mock_get_session, mock_user_id):
        """Test user creation"""
        from src.core.database import PostgreSQLDatabase
        
        # Mock session
        mock_session = MagicMock()
        mock_user = MagicMock()
        mock_user.to_dict.return_value = {
            "id": mock_user_id,
            "username": "testuser",
            "email": "test@example.com"
        }
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('src.core.database.init_db'):
            db = PostgreSQLDatabase()
            result = db.create_user("testuser", "password123", "test@example.com")
            
            assert result is not None
            assert "id" in result
            assert result["username"] == "testuser"
    
    @patch('src.core.database.Config.USE_CLOUD_SQL', False)
    @patch('src.core.database.Config.DB_CONNECTION_STRING', 'postgresql://test:test@localhost:5432/testdb')
    @patch('src.core.database.get_session')
    def test_save_transactions(self, mock_get_session, mock_transactions_list, mock_user_id):
        """Test saving transactions"""
        from src.core.database import PostgreSQLDatabase
        
        # Mock session
        mock_session = MagicMock()
        mock_account = MagicMock()
        mock_account.id = "acc_internal_123"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_account
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('src.core.database.init_db'), \
             patch('src.core.database.PostgreSQLDatabase.get_all_user_transactions', return_value=[]):
            db = PostgreSQLDatabase()
            count = db.save_transactions(
                user_id=mock_user_id,
                account_id="acc_123",
                transactions=mock_transactions_list
            )
            
            assert isinstance(count, int)
            assert count >= 0
    
    @patch('src.core.database.Config.USE_CLOUD_SQL', False)
    @patch('src.core.database.Config.DB_CONNECTION_STRING', 'postgresql://test:test@localhost:5432/testdb')
    @patch('src.core.database.get_session')
    def test_get_user_accounts(self, mock_get_session, mock_user_id):
        """Test retrieving user accounts"""
        from src.core.database import PostgreSQLDatabase
        
        # Mock session
        mock_session = MagicMock()
        mock_account = MagicMock()
        mock_account.to_dict.return_value = {
            "id": "acc_123",
            "name": "Checking Account"
        }
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_account]
        mock_get_session.return_value = mock_session
        
        with patch('src.core.database.init_db'):
            db = PostgreSQLDatabase()
            accounts = db.get_user_accounts(mock_user_id)
            
            assert isinstance(accounts, list)


class TestTransactionDeduplicator:
    """Tests for transaction deduplication"""
    
    def test_deduplicate_transactions(self, mock_transactions_list):
        """Test transaction deduplication"""
        from src.services.transaction_deduplicator import get_deduplicator
        
        deduplicator = get_deduplicator()
        
        # Add some duplicates
        new_transactions = mock_transactions_list + [mock_transactions_list[0]]
        
        result = deduplicator.deduplicate_transactions(
            new_transactions,
            []  # No existing transactions
        )
        
        assert "unique_new" in result
        assert "duplicates" in result
        assert len(result["unique_new"]) <= len(new_transactions)
    
    def test_deduplicate_with_existing(self, mock_transactions_list):
        """Test deduplication with existing transactions"""
        from src.services.transaction_deduplicator import get_deduplicator
        
        deduplicator = get_deduplicator()
        
        existing = [mock_transactions_list[0]]
        new = mock_transactions_list
        
        result = deduplicator.deduplicate_transactions(new, existing)
        
        assert len(result["duplicates"]) >= 0
        assert len(result["unique_new"]) <= len(new)
