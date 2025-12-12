"""
Agent 3: Supervisor
Central orchestrator that coordinates Agent 1 (Data Processor) and Agent 2 (Financial Analyst).

Responsibilities:
- Route incoming requests to the appropriate agent
- Execute multi-step workflows (process → analyze → recommend)
- Track processing state and mark transactions complete
- Handle errors and retry failed operations
- Provide unified response formatting
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Agent 3: Supervisor - Central orchestration agent.
    
    Coordinates Agent 1 (Data Processor) and Agent 2 (Financial Analyst),
    handles error recovery, and manages the full transaction processing pipeline.
    """
    
    def __init__(self):
        logger.info("Initializing Agent 3: Supervisor...")
        
        # Lazy load agents to avoid circular imports
        self._agent1 = None
        self._agent2 = None
        self._query_agent = None
        
        # Track processing state
        self._processing_state = {}
        
        logger.info("✓ Supervisor initialized")
    
    @property
    def agent1(self):
        """Lazy load Agent 1: Data Processor"""
        if self._agent1 is None:
            try:
                from agents.agent1_data_processor import DataProcessorLLMAgent
                self._agent1 = DataProcessorLLMAgent()
                logger.info("✓ Agent 1 (Data Processor) loaded")
            except Exception as e:
                logger.error(f"Failed to load Agent 1: {e}")
                self._agent1 = None
        return self._agent1
    
    @property
    def agent2(self):
        """Lazy load Agent 2: Financial Analyst"""
        if self._agent2 is None:
            try:
                from agents.agent2_financial_analyst import FinancialAnalystLLMAgent
                self._agent2 = FinancialAnalystLLMAgent()
                logger.info("✓ Agent 2 (Financial Analyst) loaded")
            except Exception as e:
                logger.error(f"Failed to load Agent 2: {e}")
                self._agent2 = None
        return self._agent2
    
    @property
    def query_agent(self):
        """Lazy load Query Agent"""
        if self._query_agent is None:
            try:
                from agent_tools.query_agent import QueryAgent
                self._query_agent = QueryAgent()
                logger.info("✓ Query Agent loaded")
            except Exception as e:
                logger.warning(f"Query Agent not available: {e}")
                self._query_agent = None
        return self._query_agent
    
    # =========================================================================
    # MAIN ENTRY POINTS
    # =========================================================================
    
    def handle_request(self, user_id: str, request: str) -> Dict[str, Any]:
        """
        Main entry point for handling user requests.
        Routes to the appropriate agent based on intent detection.
        
        Args:
            user_id: The user's unique identifier
            request: Natural language request from user
            
        Returns:
            Dict with 'status', 'message', 'data', and agent-specific results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"SUPERVISOR: Processing request for user {user_id[:8]}...")
        logger.info(f"Request: {request[:100]}...")
        logger.info(f"{'='*60}\n")
        
        try:
            # Detect intent and route to appropriate handler
            intent = self._detect_intent(request.lower())
            logger.info(f"Detected intent: {intent}")
            
            # Route based on intent
            if intent == 'full_pipeline':
                return self.run_full_pipeline(user_id)
            
            elif intent == 'process_transactions':
                return self._run_agent1(user_id)
            
            elif intent == 'recommendations':
                return self._run_agent2_recommendations(user_id)
            
            elif intent == 'daily_summary':
                return self._run_agent2_summary(user_id)
            
            elif intent == 'query':
                return self._run_query(user_id, request)
            
            else:
                return self._handle_unknown(request)
                
        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            return self._handle_error(e, {'user_id': user_id, 'request': request})
    
    def run_full_pipeline(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Execute the full processing pipeline:
        1. Agent 1: Process new transactions (categorize, fraud, subscriptions)
        2. Agent 2: Generate recommendations based on processed data
        
        Args:
            user_id: User identifier
            limit: Max transactions to process
            
        Returns:
            Combined results from both agents
        """
        logger.info(f"\n{'='*60}")
        logger.info("SUPERVISOR: Running FULL PIPELINE")
        logger.info(f"{'='*60}\n")
        
        results = {
            'status': 'success',
            'pipeline': 'full',
            'stages': {},
            'errors': []
        }
        
        # Stage 1: Process transactions with Agent 1
        logger.info("STAGE 1: Data Processing (Agent 1)")
        logger.info("-" * 40)
        
        try:
            agent1_result = self._run_agent1(user_id, limit)
            results['stages']['data_processing'] = agent1_result
            
            if agent1_result.get('status') == 'error':
                results['errors'].append(f"Agent 1: {agent1_result.get('message')}")
        except Exception as e:
            logger.error(f"Agent 1 failed: {e}")
            results['stages']['data_processing'] = {'status': 'error', 'message': str(e)}
            results['errors'].append(f"Agent 1: {str(e)}")
        
        # Stage 2: Generate recommendations with Agent 2
        logger.info("\nSTAGE 2: Financial Analysis (Agent 2)")
        logger.info("-" * 40)
        
        try:
            agent2_result = self._run_agent2_recommendations(user_id)
            results['stages']['recommendations'] = agent2_result
            
            if agent2_result.get('status') == 'error':
                results['errors'].append(f"Agent 2: {agent2_result.get('message')}")
        except Exception as e:
            logger.error(f"Agent 2 failed: {e}")
            results['stages']['recommendations'] = {'status': 'error', 'message': str(e)}
            results['errors'].append(f"Agent 2: {str(e)}")
        
        # Finalize
        results['status'] = 'success' if not results['errors'] else 'partial'
        results['message'] = self._generate_pipeline_summary(results)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"PIPELINE COMPLETE: {results['status']}")
        logger.info(f"{'='*60}\n")
        
        return results
    
    # =========================================================================
    # AGENT EXECUTION METHODS
    # =========================================================================
    
    def _run_agent1(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Execute Agent 1: Data Processor"""
        if self.agent1 is None:
            return {
                'status': 'error',
                'message': 'Agent 1 (Data Processor) is not available'
            }
        
        try:
            result = self.agent1.process_transactions(user_id, limit)
            
            # Wrap string result in dict
            if isinstance(result, str):
                return {
                    'status': 'success',
                    'message': result,
                    'agent': 'data_processor'
                }
            
            return result if isinstance(result, dict) else {'status': 'success', 'data': result}
            
        except Exception as e:
            logger.error(f"Agent 1 execution error: {e}")
            return {'status': 'error', 'message': str(e), 'agent': 'data_processor'}
    
    def _run_agent2_recommendations(self, user_id: str) -> Dict[str, Any]:
        """Execute Agent 2: Generate Recommendations"""
        if self.agent2 is None:
            return {
                'status': 'error',
                'message': 'Agent 2 (Financial Analyst) is not available'
            }
        
        try:
            result = self.agent2.generate_recommendations(user_id)
            result['agent'] = 'financial_analyst'
            return result
            
        except Exception as e:
            logger.error(f"Agent 2 recommendations error: {e}")
            return {'status': 'error', 'message': str(e), 'agent': 'financial_analyst'}
    
    def _run_agent2_summary(self, user_id: str, date: str = None) -> Dict[str, Any]:
        """Execute Agent 2: Generate Daily Summary"""
        if self.agent2 is None:
            return {
                'status': 'error',
                'message': 'Agent 2 (Financial Analyst) is not available'
            }
        
        try:
            result = self.agent2.generate_daily_summary(user_id, date)
            result['agent'] = 'financial_analyst'
            return result
            
        except Exception as e:
            logger.error(f"Agent 2 summary error: {e}")
            return {'status': 'error', 'message': str(e), 'agent': 'financial_analyst'}
    
    def _run_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Execute Query Agent for analytical questions"""
        if self.query_agent is None:
            return {
                'status': 'error',
                'message': 'Query Agent is not available. MCP Toolbox may not be running.'
            }
        
        try:
            result = self.query_agent.answer_question(user_id, question)
            result['agent'] = 'query_agent'
            return result
            
        except Exception as e:
            logger.error(f"Query Agent error: {e}")
            return {'status': 'error', 'message': str(e), 'agent': 'query_agent'}
    
    # =========================================================================
    # INTENT DETECTION
    # =========================================================================
    
    def _detect_intent(self, request: str) -> str:
        """
        Detect user intent from natural language request.
        
        Returns one of:
        - 'full_pipeline': Run complete processing workflow
        - 'process_transactions': Just process new transactions
        - 'recommendations': Generate savings recommendations
        - 'daily_summary': Generate daily spending summary
        - 'query': Analytical question about finances
        - 'unknown': Unable to determine intent
        """
        request = request.lower()
        
        # Full pipeline keywords
        if any(kw in request for kw in ['full pipeline', 'process everything', 'run all', 'complete analysis']):
            return 'full_pipeline'
        
        # Agent 1: Transaction processing
        if any(kw in request for kw in ['process', 'categorize']) and 'transaction' in request:
            return 'process_transactions'
        
        # Agent 2: Recommendations
        if any(kw in request for kw in ['recommend', 'savings', 'optimize', 'budget advice', 'save money']):
            return 'recommendations'
        
        # Agent 2: Daily summary
        if any(kw in request for kw in ['summary', 'report', 'daily', 'today']) and not any(w in request for w in ['which', 'what', 'how']):
            return 'daily_summary'
        
        # Query Agent: Analytical questions
        if any(kw in request for kw in [
            'which', 'what', 'how much', 'how many', 'show me', 'list',
            'subscription', 'bill', 'merchant', 'category', 'spending',
            'most', 'highest', 'total', 'where', 'compare', 'unusual'
        ]):
            return 'query'
        
        return 'unknown'
    
    # =========================================================================
    # ERROR HANDLING & RECOVERY
    # =========================================================================
    
    def _handle_error(self, error: Exception, context: Dict) -> Dict[str, Any]:
        """Handle errors with appropriate recovery or user feedback"""
        error_msg = str(error)
        
        # Connection errors
        if 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            return {
                'status': 'error',
                'error_type': 'connection',
                'message': 'Unable to connect to the database. Please ensure the MCP Toolbox is running.',
                'recoverable': True,
                'suggestion': 'Run: cd mcp_toolbox && ./toolbox --tools-file tools.yaml'
            }
        
        # Authentication errors
        if 'credential' in error_msg.lower() or 'auth' in error_msg.lower():
            return {
                'status': 'error',
                'error_type': 'authentication',
                'message': 'Authentication failed. Please check your API keys.',
                'recoverable': False
            }
        
        # Generic error
        return {
            'status': 'error',
            'error_type': 'unknown',
            'message': f'An error occurred: {error_msg}',
            'context': context,
            'recoverable': False
        }
    
    def _handle_unknown(self, request: str) -> Dict[str, Any]:
        """Handle requests that couldn't be understood"""
        return {
            'status': 'help',
            'message': "I can help you with:",
            'capabilities': [
                "**Process transactions** - Categorize and analyze new transactions",
                "**Generate recommendations** - Get personalized savings advice",
                "**Daily summary** - See today's spending report",
                "**Ask questions** - 'Which subscription costs the most?', 'What's my biggest expense?'",
                "**Run full pipeline** - Process everything and generate recommendations"
            ],
            'examples': [
                "Process my transactions",
                "Give me savings recommendations",
                "Show my daily summary",
                "Which merchant do I spend the most at?",
                "Run full pipeline"
            ]
        }
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _generate_pipeline_summary(self, results: Dict) -> str:
        """Generate human-readable summary of pipeline execution"""
        stages = results.get('stages', {})
        errors = results.get('errors', [])
        
        summary_parts = ["Pipeline execution complete:"]
        
        # Data processing summary
        dp = stages.get('data_processing', {})
        if dp.get('status') == 'success':
            summary_parts.append("✓ Transactions processed successfully")
        elif dp.get('status') == 'error':
            summary_parts.append(f"✗ Transaction processing failed: {dp.get('message', 'Unknown error')}")
        
        # Recommendations summary
        rec = stages.get('recommendations', {})
        if rec.get('status') == 'success':
            total_recs = rec.get('total_recommendations', 0)
            savings = rec.get('potential_monthly_savings', 0)
            summary_parts.append(f"✓ Generated {total_recs} recommendations (${savings:.2f}/month potential savings)")
        elif rec.get('status') == 'error':
            summary_parts.append(f"✗ Recommendations failed: {rec.get('message', 'Unknown error')}")
        
        return "\n".join(summary_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all agents"""
        return {
            'supervisor': 'active',
            'agent1_available': self._agent1 is not None or True,  # Can be lazy loaded
            'agent2_available': self._agent2 is not None or True,  # Can be lazy loaded
            'query_agent_available': self._query_agent is not None,
            'timestamp': datetime.now().isoformat()
        }


# =========================================================================
# MODULE-LEVEL FUNCTIONS
# =========================================================================

# Global supervisor instance
_supervisor = None


def get_supervisor() -> SupervisorAgent:
    """Get or create the global Supervisor instance"""
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorAgent()
    return _supervisor


def handle_user_request(user_id: str, request: str) -> Dict[str, Any]:
    """Convenience function to handle a user request through the Supervisor"""
    supervisor = get_supervisor()
    return supervisor.handle_request(user_id, request)


# =========================================================================
# CLI INTERFACE
# =========================================================================

if __name__ == "__main__":
    import sys
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 60)
    print("AGENT 3: SUPERVISOR")
    print("=" * 60 + "\n")
    
    supervisor = SupervisorAgent()
    
    # Check status
    print("Agent Status:")
    print(json.dumps(supervisor.get_status(), indent=2))
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            print("\nInteractive mode (type 'exit' to quit):\n")
            while True:
                try:
                    user_input = input("🤖 Request: ")
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    
                    # Extract user_id if provided, otherwise use default
                    user_id = "test-user-id"
                    
                    result = supervisor.handle_request(user_id, user_input)
                    
                    print("\n" + "-" * 40)
                    if result.get('answer'):
                        print(result['answer'])
                    elif result.get('message'):
                        print(result['message'])
                    elif result.get('capabilities'):
                        print(result['message'])
                        for cap in result['capabilities']:
                            print(f"  • {cap}")
                    else:
                        print(json.dumps(result, indent=2))
                    print("-" * 40 + "\n")
                    
                except KeyboardInterrupt:
                    break
        else:
            # Handle command line request
            request = " ".join(sys.argv[1:])
            result = supervisor.handle_request("cli-user", request)
            print(json.dumps(result, indent=2))
    else:
        print("\nUsage:")
        print("  python agent3_supervisor.py interactive    # Interactive mode")
        print("  python agent3_supervisor.py 'your request' # Single request")

