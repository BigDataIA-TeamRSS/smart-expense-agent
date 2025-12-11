# # #supervisor:
# # from google.adk.agents import Agent
# # from mcp_toolbox.agents.agent_data_processor import DataProcessorLLMAgent
# # from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent

# # class RootOrchestratorAgent:

# #     def __init__(self, transaction_checker):
# #         self.agent1 = DataProcessorLLMAgent()
# #         self.agent2 = FinancialAnalystLLMAgent()
# #         self.transaction_checker = transaction_checker  # Function to detect new transactions

# #     def route(self, user_input: str):
# #         text = user_input.lower()

# #         # ----- Agent 1 routing -----
# #         if any(p in text for p in ["process", "categorize", "transactions", "clean data"]):
# #             if self.transaction_checker():
# #                 return self.agent1.handle(user_input)
# #             else:
# #                 return "No new transactions to process."

# #         # ----- Agent 2 routing -----
# #         if any(p in text for p in ["budget", "savings", "spending", "financial"]):
# #             return self.agent2.handle(user_input)

# #         return "I am not sure which agent to use. Please clarify."


# # # Wrapper to create ADK-compatible root agent
# # def create_root_agent(transaction_checker):
# #     root = RootOrchestratorAgent(transaction_checker=transaction_checker)

# #     return Agent(
# #         name="root_orchestrator",
# #         model="gemini-2.5-flash",
# #         instruction="""
# # You are the Smart Expense AI Orchestrator.
# # You do not run tools yourself. You decide which sub-agent should handle the request:

# # - If task involves transactions → send to Agent 1 (Data Processor) only if new transactions exist
# # - If task involves budget analysis → send to Agent 2 (Financial Analyst)
# # """,
# #         tools=[],  # Root has no tools
# #         handler=root.route  # This is the important part: ADK will call root.route()
# #     )


# # """
# # Root Orchestrator Agent
# # File: mcp_toolbox/agents/root_orchestrator.py
# # """

# # import re
# # from mcp_toolbox.agents.agent_data_processor import DataProcessorLLMAgent
# # from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent


# # class RootOrchestratorAgent:

# #     def __init__(self):
# #         print("Initializing Root Orchestrator...")
# #         self.agent1 = DataProcessorLLMAgent()
# #         self.agent2 = FinancialAnalystLLMAgent()
# #         print("Root Orchestrator ready\n")

# #     def route(self, user_input: str):
# #         text = user_input.lower()
        
# #         print(f"\nORCHESTRATOR: Routing request")
# #         print(f"Input: {user_input}\n")
        
# #         user_id_match = re.search(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', user_input)
# #         user_id = user_id_match.group(0) if user_id_match else None
        
# #         if any(keyword in text for keyword in ["process", "categorize", "transactions"]):
# #             print("-> Routing to Agent 1: Data Processor\n")
            
# #             if not user_id:
# #                 return "Please provide a user ID"
            
# #             return self.agent1.process_transactions(user_id)
        
# #         elif any(keyword in text for keyword in ["recommend", "savings", "optimize", "budget"]):
# #             print("-> Routing to Agent 2: Recommendations\n")
            
# #             if not user_id:
# #                 return "Please provide a user ID"
            
# #             return self.agent2.generate_recommendations(user_id)
        
# #         elif any(keyword in text for keyword in ["summary", "report", "today", "daily"]):
# #             print("-> Routing to Agent 2: Daily Summary\n")
            
# #             if not user_id:
# #                 return "Please provide a user ID"
            
# #             return self.agent2.generate_daily_summary(user_id)
        
# #         else:
# #             return "I can help with: process transactions, generate recommendations, or show daily summary"


# # if __name__ == "__main__":
# #     import sys
# #     import json
    
# #     orchestrator = RootOrchestratorAgent()
    
# #     if len(sys.argv) > 1:
# #         user_request = " ".join(sys.argv[1:])
# #         result = orchestrator.route(user_request)
# #         print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
# #     else:
# #         print("Interactive mode:")
# #         while True:
# #             try:
# #                 cmd = input("\nYour command: ")
# #                 if cmd.lower() in ['exit', 'quit']:
# #                     break
# #                 result = orchestrator.route(cmd)
# #                 print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
# #             except KeyboardInterrupt:
# #                 break


# """
# Root Orchestrator Agent
# File: mcp_toolbox/agents/root_orchestrator.py
# """

# import re
# from mcp_toolbox.agents.agent_data_processor import DataProcessorLLMAgent
# from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
# from mcp_toolbox.tools.ans_queries import QueryAgent


# class RootOrchestratorAgent:

#     def __init__(self, transaction_checker, db_connection):
#         print("Initializing Root Orchestrator...")

#         # ---- AGENTS ----
#         self.agent1 = DataProcessorLLMAgent()
#         self.agent2 = FinancialAnalystLLMAgent()
#         self.agent3 = QueryAgent(db_connection)      # <-- NEW QUERY AGENT

#         # ---- UTILS ----
#         self.transaction_checker = transaction_checker
#         self.db = db_connection

#         print("Root Orchestrator ready.\n")

#     # -----------------------------------------------------------
#     # Extracts UUID style user_id from user text
#     # -----------------------------------------------------------
#     def extract_user_id(self, text):
#         match = re.search(
#             r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
#             text
#         )
#         return match.group(0) if match else None

#     # -----------------------------------------------------------
#     # ROUTER: Main Brain
#     # -----------------------------------------------------------
#     def route(self, user_input: str):

#         print("\nORCHESTRATOR: Incoming request")
#         print(f"→ {user_input}\n")

#         text = user_input.lower()
#         user_id = self.extract_user_id(text)
#         session_id = "default-session"  # optional but required by QueryAgent

#         if not user_id:
#             return "❗ Please provide a valid user ID (UUID)."

#         # --------------------------------------------------------
#         # 1️⃣ Transaction Processing (Agent 1)
#         # --------------------------------------------------------
#         if any(k in text for k in ["process", "categorize", "clean transactions"]):
#             print("Routing → Agent 1 (Data Processor)")

#             if not self.transaction_checker():
#                 return "No new transactions to process."

#             return self.agent1.process_transactions(user_id)

#         # --------------------------------------------------------
#         # 2️⃣ Financial Recommendations (Agent 2)
#         # --------------------------------------------------------
#         if any(k in text for k in ["recommend", "savings", "optimize", "budget"]):
#             print("Routing → Agent 2 (Financial Analyst)")
#             return self.agent2.generate_recommendations(user_id)

#         if any(k in text for k in ["summary", "report", "today", "daily"]):
#             print("Routing → Agent 2 (Daily Summary)")
#             return self.agent2.generate_daily_summary(user_id)

#         # --------------------------------------------------------
#         # 3️⃣ SQL / Analytics Queries (Agent 3 — QueryAgent)
#         # --------------------------------------------------------
#         if any(k in text for k in [
#             "which category", "which merchant", "top store", "top merchant",
#             "most expensive subscription", "best subscription", "monthly spending",
#             "where do i spend", "highest spending", "charges me most",
#             "convenient subscription", "subscription value"
#         ]):
#             print("Routing → Agent 3 (QueryAgent)")
#             return self.agent3.answer(user_id, session_id, user_input)

#         # --------------------------------------------------------
#         # Unknown
#         # --------------------------------------------------------
#         return (
#             "I can help with:\n"
#             "• Process transactions\n"
#             "• Budget & savings recommendations\n"
#             "• Daily summaries\n"
#             "• Analytical questions (categories, merchants, subscriptions)"
#         )


# # -----------------------------------------------------------
# # Standalone CLI Interface (optional)
# # -----------------------------------------------------------
# if __name__ == "__main__":
#     import sys
#     import json
#     import psycopg2

#     # Example DB connection (adjust for your environment)
#     conn = psycopg2.connect(
#         dbname="mcp",
#         user="postgres",
#         password="postgres",
#         host="localhost",
#         port="5432"
#     )

#     def sample_transaction_checker():
#         return True  # always true for testing

#     orchestrator = RootOrchestratorAgent(sample_transaction_checker, conn)

#     if len(sys.argv) > 1:
#         user_request = " ".join(sys.argv[1:])
#         result = orchestrator.route(user_request)
#         print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
#     else:
#         print("Interactive mode:")
#         while True:
#             try:
#                 cmd = input("\nYour command: ")
#                 if cmd.lower() in ['exit', 'quit']:
#                     break
#                 result = orchestrator.route(cmd)
#                 print(json.dumps(result, indent=2) if isinstance(result, dict) else result)
#             except KeyboardInterrupt:
#                 break


"""
Root Orchestrator - Routes to Agent 1, Agent 2, or Query Agent
File: mcp_toolbox/agents/root_orchestrator.py
"""

import re
from mcp_toolbox.agents.agent_data_processor import DataProcessorLLMAgent
from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
from mcp_toolbox.tools.query_agent import QueryAgent


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