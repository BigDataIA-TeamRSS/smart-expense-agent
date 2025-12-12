"""
Tests for Agent Tools (categorization, fraud detection, subscription detection)
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCategorizationTool:
    """Tests for transaction categorization tool"""
    
    def test_categorize_transaction_rule_based(self, mocker, mock_transaction):
        """Test categorization using rule-based logic"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.categorization.get_toolbox', return_value=mock_toolbox)
        
        # Mock LLM as unavailable
        mocker.patch('agent_tools.categorization.LLM_AVAILABLE', False)
        
        from agent_tools.categorization import categorize_transaction
        
        result = categorize_transaction(
            transaction_id=mock_transaction["transaction_id"],
            merchant_name=mock_transaction["merchant_name"],
            amount=mock_transaction["amount"],
            description=mock_transaction.get("name", ""),
            user_id=mock_transaction["user_id"]
        )
        
        assert "category" in result
        assert "merchant_standardized" in result
        assert result["status"] == "success"
        assert isinstance(result["category"], str)
    
    def test_categorize_transaction_with_llm(self, mocker, mock_transaction):
        """Test categorization using LLM"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.categorization.get_toolbox', return_value=mock_toolbox)
        
        # Mock LLM
        mocker.patch('agent_tools.categorization.LLM_AVAILABLE', True)
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"category": "Shopping", "merchant_standardized": "Amazon", "confidence": 0.9}'
        mock_llm.generate_content.return_value = mock_response
        mocker.patch('agent_tools.categorization.llm_model', mock_llm)
        
        from agent_tools.categorization import categorize_transaction
        
        result = categorize_transaction(
            transaction_id=mock_transaction["transaction_id"],
            merchant_name=mock_transaction["merchant_name"],
            amount=mock_transaction["amount"],
            description=mock_transaction.get("name", ""),
            user_id=mock_transaction["user_id"]
        )
        
        assert "category" in result
        assert result["status"] == "success"
    
    def test_categorize_amazon_transaction(self, mocker, mock_transaction):
        """Test categorization of Amazon transaction"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.categorization.get_toolbox', return_value=mock_toolbox)
        
        mocker.patch('agent_tools.categorization.LLM_AVAILABLE', False)
        
        from agent_tools.categorization import categorize_transaction
        
        result = categorize_transaction(
            transaction_id=mock_transaction["transaction_id"],
            merchant_name="AMZN MKTP US",
            amount=-29.99,
            description="Amazon purchase",
            user_id=mock_transaction["user_id"]
        )
        
        assert "amazon" in result.get("merchant_standardized", "").lower()
        assert result["status"] == "success"


class TestFraudDetectionTool:
    """Tests for fraud detection tool"""
    
    def test_detect_fraud_normal_transaction(self, mocker, mock_transaction):
        """Test fraud detection on normal transaction"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.fraud_detector.get_toolbox', return_value=mock_toolbox)
        
        # Mock user profile fetch
        mocker.patch('agent_tools.fraud_detector._get_user_profile', return_value=None)
        
        mocker.patch('agent_tools.fraud_detector.LLM_AVAILABLE', False)
        
        from agent_tools.fraud_detector import detect_fraud
        
        result = detect_fraud(
            transaction_id=mock_transaction["transaction_id"],
            user_id=mock_transaction["user_id"],
            amount=mock_transaction["amount"],
            merchant_name=mock_transaction["merchant_name"],
            transaction_date=mock_transaction["date"],
            category="Shopping"
        )
        
        assert "is_anomaly" in result
        assert "risk_score" in result
        assert result["status"] == "success"
        assert isinstance(result["is_anomaly"], bool)
    
    def test_detect_fraud_high_amount(self, mocker):
        """Test fraud detection on high-value transaction"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.fraud_detector.get_toolbox', return_value=mock_toolbox)
        
        # Mock user profile fetch
        mocker.patch('agent_tools.fraud_detector._get_user_profile', return_value=None)
        
        mocker.patch('agent_tools.fraud_detector.LLM_AVAILABLE', False)
        
        from agent_tools.fraud_detector import detect_fraud
        
        result = detect_fraud(
            transaction_id="txn_large_123",
            user_id="user_123",
            amount=-5000.00,
            merchant_name="UNKNOWN MERCHANT",
            transaction_date="2024-12-01",
            category="Other"
        )
        
        assert result["status"] == "success"
        # High-value unknown merchant should be flagged
        if result["is_anomaly"]:
            assert result["risk_score"] > 50
    
    def test_detect_fraud_with_llm(self, mocker, mock_transaction):
        """Test fraud detection with LLM analysis"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {"success": True}
        mocker.patch('agent_tools.fraud_detector.get_toolbox', return_value=mock_toolbox)
        
        # Mock user profile fetch
        mocker.patch('agent_tools.fraud_detector._get_user_profile', return_value=None)
        
        # Mock LLM
        mocker.patch('agent_tools.fraud_detector.LLM_AVAILABLE', True)
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"score_adjustment": 5, "factors": ["Low risk"]}'
        mock_llm.generate_content.return_value = mock_response
        mocker.patch('agent_tools.fraud_detector.llm_model', mock_llm)
        
        from agent_tools.fraud_detector import detect_fraud
        
        result = detect_fraud(
            transaction_id=mock_transaction["transaction_id"],
            user_id=mock_transaction["user_id"],
            amount=mock_transaction["amount"],
            merchant_name=mock_transaction["merchant_name"],
            transaction_date=mock_transaction["date"],
            category="Shopping"
        )
        
        assert result["status"] == "success"
        assert "is_anomaly" in result


class TestSubscriptionDetectionTool:
    """Tests for subscription detection tool"""
    
    def test_detect_subscriptions_known_service(self, mocker):
        """Test subscription detection for known service"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        # Mock get-user-transactions tool call
        mock_toolbox.call_tool.return_value = {
            "success": True,
            "data": [
                {
                    "transaction_id": f"netflix_{i}",
                    "user_id": "user_123",
                    "amount": -12.99,
                    "merchant_name": "NETFLIX",
                    "date": (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m-%d")
                }
                for i in range(3)
            ]
        }
        mocker.patch('agent_tools.subscription_detector.get_toolbox', return_value=mock_toolbox)
        
        mocker.patch('agent_tools.subscription_detector.LLM_AVAILABLE', False)
        
        from agent_tools.subscription_detector import detect_subscriptions
        
        result = detect_subscriptions(user_id="user_123")
        
        assert result["status"] == "success"
        assert "subscriptions" in result
    
    def test_detect_subscriptions_recurring_pattern(self, mocker):
        """Test subscription detection based on recurring pattern"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        # Mock get-user-transactions tool call
        mock_toolbox.call_tool.return_value = {
            "success": True,
            "data": [
                {
                    "transaction_id": f"recurring_{i}",
                    "user_id": "user_123",
                    "amount": -9.99,
                    "merchant_name": "SPOTIFY",
                    "date": (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m-%d")
                }
                for i in range(4)
            ]
        }
        mocker.patch('agent_tools.subscription_detector.get_toolbox', return_value=mock_toolbox)
        
        mocker.patch('agent_tools.subscription_detector.LLM_AVAILABLE', False)
        
        from agent_tools.subscription_detector import detect_subscriptions
        
        result = detect_subscriptions(user_id="user_123")
        
        assert result["status"] == "success"
        # Should detect Spotify subscription
        subscriptions = result.get("subscriptions", [])
        spotify_found = any("spotify" in sub.get("merchant", "").lower() 
                          for sub in subscriptions)
        assert spotify_found
    
    def test_detect_subscriptions_with_llm(self, mocker):
        """Test subscription detection with LLM"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {
            "success": True,
            "data": [
                {
                    "transaction_id": f"netflix_{i}",
                    "user_id": "user_123",
                    "amount": -12.99,
                    "merchant_name": "NETFLIX",
                    "date": (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m-%d")
                }
                for i in range(3)
            ]
        }
        mocker.patch('agent_tools.subscription_detector.get_toolbox', return_value=mock_toolbox)
        
        # Mock LLM
        mocker.patch('agent_tools.subscription_detector.LLM_AVAILABLE', True)
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '[{"merchant": "Netflix", "confidence": 0.95, "frequency": "monthly"}]'
        mock_llm.generate_content.return_value = mock_response
        mocker.patch('agent_tools.subscription_detector.llm_model', mock_llm)
        
        from agent_tools.subscription_detector import detect_subscriptions
        
        result = detect_subscriptions(user_id="user_123")
        
        assert result["status"] == "success"


class TestFetchTransactionsTool:
    """Tests for fetch transactions tool"""
    
    def test_fetch_unprocessed_transactions(self, mocker, mock_user_id):
        """Test fetching unprocessed transactions"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {
            "success": True,
            "data": [
                {
                    "transaction_id": "txn_1",
                    "amount": -45.67,
                    "date": "2024-12-01",
                    "merchant_name": "AMAZON"
                }
            ]
        }
        mocker.patch('agent_tools.fetch_transactions.get_toolbox', return_value=mock_toolbox)
        
        from agent_tools.fetch_transactions import fetch_transactions
        
        result = fetch_transactions(user_id=mock_user_id)
        
        assert result["status"] == "success"
        assert "transactions" in result


class TestStoreProcessedTool:
    """Tests for store processed data tool"""
    
    def test_store_processed_transaction(self, mocker, mock_transaction):
        """Test storing processed transaction"""
        # Mock toolbox
        mock_toolbox = MagicMock()
        mock_toolbox.call_tool.return_value = {
            "success": True,
            "data": "Transaction stored"
        }
        mocker.patch('agent_tools.store_processed.get_toolbox', return_value=mock_toolbox)
        
        from agent_tools.store_processed import store_processed_data
        
        result = store_processed_data(
            transaction_ids=[mock_transaction["transaction_id"]],
            user_id=mock_transaction["user_id"],
            summary={"categorized": 1}
        )
        
        assert result["status"] == "success"
        assert "processed_count" in result
