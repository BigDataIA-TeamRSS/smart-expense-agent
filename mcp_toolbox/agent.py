# run using 'adk run mcp_toolbox'
# or 'adk web'
# """
# Agent for ADK Web - Data Processor
# This file is required for 'adk web' to work
# """

# from google.adk.agents import Agent
# from google.adk.apps import App
# from toolbox_core import ToolboxSyncClient
# from google.genai import types
# from dotenv import load_dotenv

# load_dotenv()

# # Connect to toolbox server (must be running on port 5000)
# print("Connecting to MCP Toolbox at http://127.0.0.1:5000...")

# try:
#     client = ToolboxSyncClient("http://127.0.0.1:5000")
#     tools = client.load_toolset("default")
#     print(f"✅ Loaded tools from toolbox")
# except Exception as e:
#     print(f"❌ Failed to connect to toolbox: {e}")
#     print("Make sure toolbox is running: .\\toolbox.exe --tools-file tools.yaml")
#     tools = []

# # Create the root agent (required by ADK web)
# root_agent = Agent(
#     name='data_processor',
#     model='gemini-2.5-flash',
#     instruction="""
# You are Agent 1: Data Processor for Smart Expense Analyzer.

# Your mission: Process raw transaction data and enhance it with AI insights.

# RESPONSIBILITIES:
# 1. Fetch unprocessed transactions from database
# 2. Categorize transactions into: Groceries, Dining, Transportation, Entertainment, Shopping, Bills, Healthcare, Income, Transfers, Other
# 3. Standardize merchant names (clean codes like AMZN → Amazon, UBER 072515 SF → Uber)
# 4. Detect recurring subscriptions (same merchant + amount every 28-32 days)
# 5. Flag anomalies (transactions that are unusually large)
# 6. Calculate monthly spending patterns by category
# 7. Save all processed data to database

# STANDARD CATEGORIES:
# - Groceries
# - Dining
# - Transportation
# - Entertainment
# - Shopping
# - Bills
# - Healthcare
# - Income
# - Transfers
# - Other

# AVAILABLE TOOLS:
# Use the database tools to:
# - fetch-unprocessed-transactions: Get transactions needing processing
# - get-user-transactions: Get transactions in a date range
# - insert-processed-transaction: Save categorized transaction
# - upsert-subscription: Save detected subscriptions
# - get-user-subscriptions: Check existing subscriptions
# - insert-spending-pattern: Save spending analytics
# - get-category-history: Get historical spending
# - get-recent-transactions: Get recent transactions for a user

# PROCESSING WORKFLOW:
# When user asks to "process transactions" or "analyze data":
# 1. Use fetch-unprocessed-transactions to get unprocessed data
# 2. For each transaction:
#    - Categorize it into a standard category
#    - Standardize the merchant name
#    - Determine if it's a subscription
#    - Check if it's anomalous (very high amount)
# 3. Use insert-processed-transaction to save each one
# 4. Analyze patterns to detect subscriptions
# 5. Use upsert-subscription for recurring charges
# 6. Calculate spending by category
# 7. Use insert-spending-pattern to save analytics

# RULES:
# - Always ask for user_id if not provided
# - Be thorough in categorization
# - Save everything to avoid reprocessing
# - Report progress and results clearly
# """,
#     tools=tools,
#     generate_content_config=types.GenerateContentConfig(
#         temperature=0.1,
#     )
# )

# # Required by ADK web
# app = App(root_agent=root_agent, name="mcp_toolbox")

# mcp_toolbox/agent.py

# import sys
# from pathlib import Path
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

# from google.adk.agents import Agent
# from google.adk.apps import App
# from mcp_toolbox.tools.data_processor import DataProcessorAgent
# from dotenv import load_dotenv
# from mcp_toolbox.financial_analyst import FinancialAnalystAgent


# load_dotenv()

# # Create wrapper that uses data_processor logic
# processor = DataProcessorAgent()

# root_agent = Agent(
#     name='data_processor',
#     model='gemini-2.5-flash',
#     instruction="You are a data processing agent. When asked to process transactions, use the DataProcessorAgent.",
#     tools=processor.tools,  # Use tools from data_processor
# )

# analyst = FinancialAnalystAgent()

# root_agent = Agent(
#     name="financial_analyst",
#     model="gemini-2.5-flash",
#     tools=analyst.tools,
#     instruction="You are Agent 2: Financial Analyst. Use tools to evaluate budget health and find savings opportunities."
# )

# app = App(root_agent=root_agent, name="mcp_toolbox")

from mcp_toolbox.agents.root_orchestrator import create_root_agent
from google.adk.apps import App

root_agent = create_root_agent()

app = App(root_agent=root_agent, name="mcp_toolbox")
