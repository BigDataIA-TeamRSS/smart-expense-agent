import logging
import uuid
import asyncio
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner 
from google.genai.types import Content, Part
from google.adk.sessions import Session # Import Session type for clarity

# Assuming these tools are defined correctly elsewhere
from agent_tools.fetch_transactions import fetch_transactions
from agent_tools.categorization import categorize_transaction
from agent_tools.subscription_detector import detect_subscriptions
from agent_tools.fraud_detector import detect_fraud
from agent_tools.store_processed import store_processed_data

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
APP_NAME = "agent1_financial_processor_app"

# Define the agent
agent1_data_processor = LlmAgent(
    name="agent1_data_processor",
    model="gemini-flash-lite-latest",
    description="Agent 1: Data Processor for financial transactions, ",
    tools=[
        FunctionTool(fetch_transactions),
        FunctionTool(categorize_transaction),
        FunctionTool(detect_fraud),
        FunctionTool(detect_subscriptions),
        FunctionTool(store_processed_data),
    ]
)

# --- CORRECTED RUNNER SETUP ---
# InMemoryRunner is used, which internally creates the InMemorySessionService.
agent_runner = InMemoryRunner(
    agent=agent1_data_processor,
    app_name=APP_NAME
)


class DataProcessorLLMAgent:
    """Wrapper class for Agent 1: Data Processor"""
    
    def __init__(self):
        self.agent = agent1_data_processor
        self.runner = agent_runner
        
    def process_transactions(self, user_id: str, limit: int = 50):
        """Process transactions for a user"""
        return process_user_transactions_agent1(user_id, limit)


def process_user_transactions_agent1(user_id: str, limit: int = 50):
    """
    Run Agent 1 synchronously using ADK v1.20.0, guaranteeing session creation.
    """
    logger.info(f"🚀 Starting Agent 1 for user {user_id}")

    prompt_text = f"""Process all unprocessed transactions for user: {user_id}

Workflow:
1. Fetch new transactions (limit: {limit})
2. For each transaction:
    a. Categorize it
    b. Check for fraud
3. Detect subscription patterns
4. Mark all as processed
5. Provide summary
Give answers and output in proper format which is readable.
Execute now."""
    
    user_message = Content(
        parts=[Part(text=prompt_text)],
        role="user"
    )

    try:
        # --- FIX: Explicitly create the session object using asyncio.run() ---
        unique_session_id = str(uuid.uuid4())
        logger.info(f"🔄 Creating session with ID: {unique_session_id}")

        # Define an async function to execute the session creation
        async def create_session_async() -> Session:
            return await agent_runner.session_service.create_session(
                app_name=APP_NAME, 
                user_id=user_id,
                session_id=unique_session_id
            )

        # Run the async function synchronously to get the created session object
        session_object = asyncio.run(create_session_async())

        # 4. Now, run the agent using the ID of the session we just created
        # The key change: Accessing the ID via .id instead of .session_id
        events = agent_runner.run(
            user_id=user_id, 
            session_id=session_object.id, # <-- CORRECTED ATTRIBUTE ACCESS
            new_message=user_message
        )

        # Iterate through the events (the generator) to capture the final output
        output_text = ""
        for event in events:
            # The final response is usually in the last generated Content event
            if event.content and event.content.parts and len(event.content.parts) > 0:
                part = event.content.parts[0]
                if hasattr(part, 'text') and part.text:
                    output_text = part.text.strip()
        
        # Fallback if the agent finished but didn't produce a clear text output
        if not output_text:
            output_text = "Agent completed the run process but did not produce a final text response. Check logs for authentication or tool execution errors."
            
        logger.info(f"✅ Agent 1 completed")
        return output_text

    except Exception as e:
        logger.error(f"❌ Agent 1 failed: {e}", exc_info=True)
        return str(e)