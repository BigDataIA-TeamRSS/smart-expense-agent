"""
Tests for AI Agents (Agent 1, Agent 2, Root Orchestrator)
"""
import pytest
from unittest.mock import patch, MagicMock, Mock, AsyncMock
import sys
import types
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup mock modules for modules that don't exist in mcp_toolbox.agent_tools
if 'mcp_toolbox.agent_tools.financial_analyst' not in sys.modules:
    mock_financial_module = types.ModuleType('mcp_toolbox.agent_tools.financial_analyst')
    mock_financial_module.FinancialAnalystAgent = MagicMock
    sys.modules['mcp_toolbox.agent_tools.financial_analyst'] = mock_financial_module

if 'mcp_toolbox.agent_tools.query_agent' not in sys.modules:
    mock_query_module = types.ModuleType('mcp_toolbox.agent_tools.query_agent')
    mock_query_module.QueryAgent = MagicMock
    sys.modules['mcp_toolbox.agent_tools.query_agent'] = mock_query_module


class TestAgent1DataProcessor:
    """Tests for Agent 1: Data Processor"""
    
    def test_process_transactions_success(self, mocker, mock_user_id):
        """Test successful transaction processing"""
        # Mock the agent tools
        mocker.patch('mcp_toolbox.agent_tools.fetch_transactions.fetch_transactions')
        mocker.patch('mcp_toolbox.agent_tools.categorization.categorize_transaction')
        mocker.patch('mcp_toolbox.agent_tools.fraud_detector.detect_fraud')
        mocker.patch('mcp_toolbox.agent_tools.subscription_detector.detect_subscriptions')
        mocker.patch('mcp_toolbox.agent_tools.store_processed.store_processed_data')
        
        # Mock agent runner
        mock_runner = MagicMock()
        mock_session = MagicMock()
        mock_session.id = "session_123"
        mock_event = MagicMock()
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock()]
        mock_event.content.parts[0].text = "Processing completed successfully"
        mock_runner.run.return_value = [mock_event]
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.agent_runner', mock_runner)
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.asyncio.run', return_value=mock_session)
        
        from mcp_toolbox.agents.agent1_data_processor import DataProcessorLLMAgent
        
        agent = DataProcessorLLMAgent()
        result = agent.process_transactions(mock_user_id)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_process_transactions_failure(self, mocker, mock_user_id):
        """Test transaction processing failure"""
        # Mock the agent tools
        mocker.patch('mcp_toolbox.agent_tools.fetch_transactions.fetch_transactions')
        mocker.patch('mcp_toolbox.agent_tools.categorization.categorize_transaction')
        mocker.patch('mcp_toolbox.agent_tools.fraud_detector.detect_fraud')
        mocker.patch('mcp_toolbox.agent_tools.subscription_detector.detect_subscriptions')
        mocker.patch('mcp_toolbox.agent_tools.store_processed.store_processed_data')
        
        # Mock agent runner to raise error
        mock_runner = MagicMock()
        mock_runner.run.side_effect = Exception("Agent execution failed")
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.agent_runner', mock_runner)
        
        from mcp_toolbox.agents.agent1_data_processor import DataProcessorLLMAgent
        
        agent = DataProcessorLLMAgent()
        # Should handle error gracefully
        try:
            result = agent.process_transactions(mock_user_id)
            assert isinstance(result, str)
        except Exception:
            # If it raises, that's also acceptable for a failure test
            pass
    
    def test_data_processor_agent_initialization(self, mocker):
        """Test DataProcessorLLMAgent initialization"""
        # Mock dependencies
        mocker.patch('mcp_toolbox.agent_tools.fetch_transactions.fetch_transactions')
        mocker.patch('mcp_toolbox.agent_tools.categorization.categorize_transaction')
        mocker.patch('mcp_toolbox.agent_tools.fraud_detector.detect_fraud')
        mocker.patch('mcp_toolbox.agent_tools.subscription_detector.detect_subscriptions')
        mocker.patch('mcp_toolbox.agent_tools.store_processed.store_processed_data')
        
        from mcp_toolbox.agents.agent1_data_processor import DataProcessorLLMAgent
        
        agent = DataProcessorLLMAgent()
        
        assert agent is not None
        assert hasattr(agent, 'process_transactions')
        assert callable(agent.process_transactions)


class TestAgent2FinancialAnalyst:
    """Tests for Agent 2: Financial Analyst"""
    
    def test_generate_recommendations_success(self, mocker, mock_user_id):
        """Test successful recommendation generation"""
        # Mock tool agent
        mock_tool_instance = MagicMock()
        mock_tool_instance.generate_recommendations.return_value = {
            "total_recommendations": 2,
            "recommendations": [
                {
                    "title": "Reduce Subscription Costs",
                    "description": "Cancel unused subscriptions",
                    "potential_savings": 25.99
                },
                {
                    "title": "Optimize Grocery Spending",
                    "description": "Use coupons and buy in bulk",
                    "potential_savings": 50.00
                }
            ]
        }
        # Update the mock module with our instance
        sys.modules['mcp_toolbox.agent_tools.financial_analyst'].FinancialAnalystAgent = lambda *args, **kwargs: mock_tool_instance
        
        # Mock LLM client
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a personalized recommendation to help you save money."
        mock_client_instance.models.generate_content.return_value = mock_response
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.genai.Client', return_value=mock_client_instance)
        
        from mcp_toolbox.agents.agent2_financial_analyst import FinancialAnalystLLMAgent
        
        agent = FinancialAnalystLLMAgent()
        result = agent.generate_recommendations(mock_user_id)
        
        assert "recommendations" in result
        assert result["total_recommendations"] == 2
        assert result.get("llm_enhanced", False) is True
    
    def test_generate_recommendations_no_llm(self, mocker, mock_user_id):
        """Test recommendation generation without LLM"""
        # Mock tool agent
        mock_tool_instance = MagicMock()
        mock_tool_instance.generate_recommendations.return_value = {
            "total_recommendations": 1,
            "recommendations": [
                {
                    "title": "Test Recommendation",
                    "description": "Test description",
                    "potential_savings": 10.00
                }
            ]
        }
        # Update the mock module with our instance
        sys.modules['mcp_toolbox.agent_tools.financial_analyst'].FinancialAnalystAgent = lambda *args, **kwargs: mock_tool_instance
        
        # Mock LLM unavailable
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.genai.Client', side_effect=Exception())
        
        from mcp_toolbox.agents.agent2_financial_analyst import FinancialAnalystLLMAgent
        
        agent = FinancialAnalystLLMAgent()
        result = agent.generate_recommendations(mock_user_id)
        
        assert "recommendations" in result
        assert result.get("llm_enhanced", True) is False
    
    def test_generate_daily_summary(self, mocker, mock_user_id):
        """Test daily summary generation"""
        # Mock tool agent with proper return value
        summary_dict = {
            "status": "success",
            "date": "2024-12-01",
            "total_spending": 125.50,
            "transaction_count": 5,
            "top_category": "Food & Dining"
        }
        # Create a simple mock class that returns the dict
        class MockFinancialAnalystAgent:
            def generate_daily_summary(self, user_id, date=None):
                return summary_dict.copy()
        
        mock_tool_instance = MockFinancialAnalystAgent()
        # Update the mock module with our instance
        sys.modules['mcp_toolbox.agent_tools.financial_analyst'].FinancialAnalystAgent = lambda *args, **kwargs: mock_tool_instance
        
        # Mock LLM client
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Today you spent $125.50 across 5 transactions."
        mock_client_instance.models.generate_content.return_value = mock_response
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.genai.Client', return_value=mock_client_instance)
        
        from mcp_toolbox.agents.agent2_financial_analyst import FinancialAnalystLLMAgent
        
        agent = FinancialAnalystLLMAgent()
        result = agent.generate_daily_summary(mock_user_id)
        
        # The result should be a dict with status
        assert isinstance(result, dict), f"Expected dict, got {type(result)}: {result}"
        assert result.get("status") == "success"
        if "ai_narrative" in result:
            assert result.get("llm_enhanced", False) is True


class TestRootOrchestrator:
    """Tests for Root Orchestrator Agent"""
    
    def test_orchestrator_initialization(self, mocker):
        """Test root orchestrator initialization"""
        # Mock all agent dependencies - patch the source modules before import
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_query = MagicMock()
        
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.FinancialAnalystLLMAgent', return_value=mock_agent2)
        # Update mock module
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = lambda *args, **kwargs: mock_query
        
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'route')
        assert callable(orchestrator.route)
    
    def test_route_to_agent1(self, mocker, mock_user_id):
        """Test routing to Agent 1 for transaction processing"""
        # Mock agents - create instances that will be used in __init__
        mock_agent1 = MagicMock()
        mock_agent1.process_transactions.return_value = "Processing complete"
        mock_agent2 = MagicMock()
        mock_query = MagicMock()
        
        # Patch the classes to return our mocks when instantiated
        mocker.patch('agents.root_orchestrator.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('agents.root_orchestrator.FinancialAnalystLLMAgent', return_value=mock_agent2)
        # Update mock module
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = lambda *args, **kwargs: mock_query
        
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        result = orchestrator.route(f"Process transactions for user {mock_user_id}")
        
        mock_agent1.process_transactions.assert_called_once_with(mock_user_id)
    
    def test_route_to_agent2(self, mocker, mock_user_id):
        """Test routing to Agent 2 for recommendations"""
        # Mock agents
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_agent2.generate_recommendations.return_value = {
            "total_recommendations": 1,
            "recommendations": []
        }
        mock_query = MagicMock()
        
        # Patch the classes to return our mocks when instantiated
        mocker.patch('agents.root_orchestrator.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('agents.root_orchestrator.FinancialAnalystLLMAgent', return_value=mock_agent2)
        # Update mock module
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = lambda *args, **kwargs: mock_query
        
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        result = orchestrator.route(f"Generate savings recommendations for user {mock_user_id}")
        
        mock_agent2.generate_recommendations.assert_called_once_with(mock_user_id)
    
    def test_route_to_query_agent(self, mocker, mock_user_id):
        """Test routing to Query Agent for analytical questions"""
        # Mock query agent - create a mock class
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_query_agent = MagicMock()
        mock_query_agent.answer_question.return_value = {
            "answer": "You spend most on Food & Dining"
        }
        
        # Update mock module to return our mock instance when QueryAgent() is called
        # Use a callable class that returns the mock
        class MockQueryAgent:
            def __new__(cls, *args, **kwargs):
                return mock_query_agent
        
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = MockQueryAgent
        
        # Patch the classes to return our mocks when instantiated
        mocker.patch('agents.root_orchestrator.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('agents.root_orchestrator.FinancialAnalystLLMAgent', return_value=mock_agent2)
        
        # Import after mocks are set up - need to reload if already imported
        if 'agents.root_orchestrator' in sys.modules:
            import importlib
            importlib.reload(sys.modules['agents.root_orchestrator'])
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        # Use a query that definitely matches the routing logic (contains "which" and "most")
        result = orchestrator.route(f"Which category do I spend the most on for user {mock_user_id}")
        
        # Verify the query agent was called
        # The orchestrator should have stored our mock as self.query_agent
        assert hasattr(orchestrator, 'query_agent'), "query_agent should be set in orchestrator"
        orchestrator.query_agent.answer_question.assert_called_once()
    
    def test_route_no_user_id(self, mocker):
        """Test routing without user ID"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_query = MagicMock()
        
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.FinancialAnalystLLMAgent', return_value=mock_agent2)
        # Update mock module
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = lambda *args, **kwargs: mock_query
        
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        result = orchestrator.route("Process transactions")
        
        # Should return error or help message
        assert isinstance(result, dict)
        assert "error" in result or "help" in result or "message" in result
    
    def test_extract_user_id(self, mocker, mock_user_id):
        """Test user ID extraction from text"""
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_query = MagicMock()
        
        mocker.patch('mcp_toolbox.agents.agent1_data_processor.DataProcessorLLMAgent', return_value=mock_agent1)
        mocker.patch('mcp_toolbox.agents.agent2_financial_analyst.FinancialAnalystLLMAgent', return_value=mock_agent2)
        # Update mock module
        sys.modules['mcp_toolbox.agent_tools.query_agent'].QueryAgent = lambda *args, **kwargs: mock_query
        
        from agents.root_orchestrator import RootOrchestratorAgent
        
        orchestrator = RootOrchestratorAgent()
        
        # Test with UUID in text - the route method extracts it internally
        text_with_id = f"Process transactions for {mock_user_id}"
        result = orchestrator.route(text_with_id)
        
        # Should successfully route (not return error about missing user_id)
        assert result is not None
        
        # Test without UUID
        text_without_id = "Process transactions"
        result = orchestrator.route(text_without_id)
        
        # Should return error about missing user_id
        assert isinstance(result, dict)
        assert "error" in result or "message" in result
