"""
Tool 1: Fetch New Transactions
Retrieves unprocessed transactions from the database
"""

import logging
from typing import Dict, Any
from agent_tools.toolbox_wrapper import get_toolbox


logger = logging.getLogger(__name__)


def fetch_transactions(user_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Fetches new unprocessed transactions for a user from the PostgreSQL database.
    This is the FIRST tool that should be called in the processing pipeline.
    
    This tool calls the MCP toolbox tool 'fetch-unprocessed-transactions' which:
    - Queries transactions table
    - Joins with processed_transactions to find unprocessed ones
    - Returns transaction details including merchant, amount, date, category
    
    Args:
        user_id: The user's ID to fetch transactions for (required).
        limit: Maximum number of transactions to fetch (default: 50).
               Note: This parameter is not used by the current SQL query,
               but included for future enhancement.
    
    Returns:
        A dictionary containing:
        {
            "status": "success" or "error",
            "transaction_count": Number of transactions found,
            "transactions": List of transaction objects with fields:
                - transaction_id: Unique identifier
                - user_id: User identifier
                - amount: Transaction amount (negative for debits)
                - date: Transaction date (ISO format string)
                - name: Transaction name
                - merchant_name: Merchant name
                - category: Original category from bank
                - personal_finance_category: Finance category
                - payment_channel: How payment was made
                - transaction_type: Type of transaction
            "message": Status message
        }
    
    Example:
        result = fetch_new_transactions("user_123", limit=50)
        # Returns: {"status": "success", "transaction_count": 10, "transactions": [...]}
    """
    
    try:
        logger.info(f"📥 Fetching new transactions for user: {user_id}")
        
        # Validate inputs
        if not user_id:
            return {
                "status": "error",
                "transaction_count": 0,
                "transactions": [],
                "message": "user_id is required"
            }
        
        # Get toolbox
        toolbox = get_toolbox()
        
        # Call the MCP tool: fetch-unprocessed-transactions
        result = toolbox.call_tool(
            "fetch-unprocessed-transactions",
            user_id=user_id
        )
        
        if not result['success']:
            return {
                "status": "error",
                "transaction_count": 0,
                "transactions": [],
                "message": f"Database error: {result.get('error', 'Unknown error')}"
            }
        
        transactions = result['data'] if isinstance(result['data'], list) else []
        
        logger.info(f"✅ Found {len(transactions)} unprocessed transactions")
        
        return {
            "status": "success",
            "transaction_count": len(transactions),
            "transactions": transactions,
            "message": f"Successfully fetched {len(transactions)} unprocessed transactions"
        }
    
    except Exception as e:
        logger.error(f"❌ Error fetching transactions: {e}", exc_info=True)
        return {
            "status": "error",
            "transaction_count": 0,
            "transactions": [],
            "message": f"Unexpected error: {str(e)}"
        }