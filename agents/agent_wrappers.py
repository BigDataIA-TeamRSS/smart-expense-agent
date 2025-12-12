import logging
from agent1_data_processor import agent1_executor

logger = logging.getLogger(__name__)

async def process_user_transactions_agent1(user_id: str, limit: int = 50):
    """
    Convenient wrapper to invoke Agent 1
    """
    logger.info(f"🚀 Starting Agent 1 for user {user_id}")

    prompt = f"""Process all unprocessed transactions for user: {user_id}

Workflow:
1. Fetch new transactions (limit: {limit})
2. For each transaction:
   a. Categorize it
   b. Check for fraud
3. Detect subscription patterns
4. Mark all as processed
5. Provide summary

Execute now.
"""

    # ✅ Use the AgentExecutor to run the agent
    response = await agent1_executor.agenerate_content(prompt=prompt)

    # Extract text content
    output_text = response.content if hasattr(response, 'content') else str(response)

    logger.info(f"✅ Agent 1 completed")
    return output_text