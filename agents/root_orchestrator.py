"""
Root Orchestrator - Routes to Agent 1, Agent 2, or Query Agent
File: agents/root_orchestrator.py
"""

import re
from agents.agent1_data_processor import DataProcessorLLMAgent
from agents.agent2_financial_analyst import FinancialAnalystLLMAgent
from agent_tools.query_agent import QueryAgent


class RootOrchestratorAgent:

    def __init__(self):
        print("Initializing Root Orchestrator...")
        self.agent1 = DataProcessorLLMAgent()
        self.agent2 = FinancialAnalystLLMAgent()
        self.query_agent = QueryAgent()
        print("✓ Orchestrator ready\n")

    def route(self, user_input: str):
        text = user_input.lower()
        
        print(f"\nRouting: {user_input[:80]}...")
        
        # Extract user_id
        user_id_match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', user_input)
        user_id = user_id_match.group(0) if user_id_match else None
        
        # Agent 1: Process transactions
        if any(k in text for k in ["process", "categorize"]) and "transaction" in text:
            print("→ Agent 1: Data Processor\n")
            if not user_id:
                return {'status': 'error', 'message': 'Provide user ID'}
            return self.agent1.process_transactions(user_id)
        
        # Agent 2: Recommendations
        elif any(k in text for k in ["recommend", "savings", "optimize budget"]):
            print("→ Agent 2: Recommendations\n")
            if not user_id:
                return {'status': 'error', 'message': 'Provide user ID'}
            return self.agent2.generate_recommendations(user_id)
        
        # Agent 2: Summary
        elif any(k in text for k in ["summary", "report", "daily"]) and not any(w in text for w in ["which", "what"]):
            print("→ Agent 2: Daily Summary\n")
            if not user_id:
                return {'status': 'error', 'message': 'Provide user ID'}
            return self.agent2.generate_daily_summary(user_id)
        
        # Query Agent: Analytical questions
        elif any(k in text for k in ["which", "what", "how much", "how many", "show me", 
                                      "subscription", "bill", "merchant", "category",
                                      "most", "highest", "total", "list", "where", "compare", "unusual"]):
            print("→ Query Agent: Analytical Question\n")
            if not user_id:
                return {'status': 'error', 'message': 'Provide user ID'}
            return self.query_agent.answer_question(user_id, user_input)
        
        else:
            return {'status': 'help', 'message': 'I can: process transactions, generate recommendations, show summary, or answer questions about your spending.'}


if __name__ == "__main__":
    import sys
    import json
    
    orchestrator = RootOrchestratorAgent()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            while True:
                try:
                    cmd = input("\n🤖 Question: ")
                    if cmd.lower() in ['exit', 'quit']:
                        break
                    result = orchestrator.route(cmd)
                    print("\n" + (result.get('answer') or result.get('message') or json.dumps(result, indent=2)))
                except KeyboardInterrupt:
                    break
        else:
            result = orchestrator.route(" ".join(sys.argv[1:]))
            print(result.get('answer') or result.get('message') or json.dumps(result, indent=2))
    else:
        print("Usage: python root_orchestrator.py interactive")
        print("   or: python root_orchestrator.py 'your question for user USER_ID'")