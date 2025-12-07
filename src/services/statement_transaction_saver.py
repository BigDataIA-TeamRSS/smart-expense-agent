"""
Utility for automatically saving transactions from parsed statements to the database.

This module handles:
- Converting parsed transactions to database format
- Creating/updating accounts for PDF uploads
- Saving transactions with deduplication
"""

import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from src.services.statement_parser import ParsedStatement


def generate_account_name(parsed: ParsedStatement) -> str:
    """
    Generate a descriptive account name based on bank, account type, and last 4 digits.
    
    Examples:
        "Chase Credit Card - 2551"
        "Bank of America Checking - 5820"
        "Wells Fargo Savings - 1234"
    """
    bank_name = parsed.account_info.bank_name or "Unknown Bank"
    account_type = parsed.account_info.account_type
    
    # Map account types to readable names
    type_map = {
        "credit_card": "Credit Card",
        "checking": "Checking",
        "savings": "Savings",
        "money_market": "Money Market",
    }
    
    # Get readable account type
    if hasattr(account_type, 'value'):
        acc_type_str = account_type.value
    else:
        acc_type_str = str(account_type)
    
    readable_type = type_map.get(acc_type_str, acc_type_str.replace("_", " ").title())
    
    # Get last 4 digits
    last4 = parsed.account_info.account_number_last4 or "****"
    
    return f"{bank_name} {readable_type} - {last4}"


def save_parsed_statement_transactions(
    parsed: ParsedStatement,
    db,
    user_id: str,
    filename: str,
    auto_create_account: bool = True
) -> Dict[str, Any]:
    """
    Save transactions from a parsed statement to the database.
    
    Args:
        parsed: ParsedStatement object from statement parser
        db: JSONDatabase instance
        user_id: User ID to associate transactions with
        filename: Original filename of the statement
        auto_create_account: Whether to automatically create an account if needed
    
    Returns:
        {
            "account_id": str,
            "account_created": bool,
            "transactions_saved": int,
            "transactions_duplicated": int,
            "total_transactions": int
        }
    """
    try:
        # Generate a stable account ID based on account info and filename
        # This ensures same statement creates same account
        account_key = f"{user_id}_{parsed.account_info.account_number_last4}_{parsed.account_info.bank_name}_{filename}"
        account_id = f"pdf_{hashlib.md5(account_key.encode()).hexdigest()[:16]}"
        
        account_created = False
        
        # Create or get account
        if auto_create_account:
            existing_accounts = db.get_user_accounts(user_id)
            existing_account = None
            
            # Check if account already exists
            for acc in existing_accounts:
                if acc.get("account_id") == account_id:
                    existing_account = acc
                    break
            
            if not existing_account:
                # Create new account
                account_data = {
                    "account_id": account_id,
                    "name": generate_account_name(parsed),
                    "institution_name": parsed.account_info.bank_name or "PDF Upload",
                    "type": parsed.account_info.account_type.value if hasattr(parsed.account_info.account_type, 'value') else str(parsed.account_info.account_type),
                    "subtype": "pdf_upload",
                    "mask": parsed.account_info.account_number_last4 or "****",
                    "source": "pdf_upload",
                    "current_balance": parsed.summary.ending_balance if hasattr(parsed.summary, 'ending_balance') else None,
                    "available_balance": parsed.summary.ending_balance if hasattr(parsed.summary, 'ending_balance') else None,
                    "statement_period": {
                        "start": str(parsed.account_info.statement_start_date) if parsed.account_info.statement_start_date else None,
                        "end": str(parsed.account_info.statement_end_date) if parsed.account_info.statement_end_date else None
                    } if parsed.account_info.statement_start_date or parsed.account_info.statement_end_date else None
                }
                
                db.save_bank_account(user_id, account_data)
                account_created = True
        
        # Convert parsed transactions to database format
        transactions = []
        for txn in parsed.transactions:
            # Convert to Plaid-compatible format
            plaid_txn = txn.to_plaid_format(account_id)
            
            # Add additional metadata
            plaid_txn["original_description"] = txn.original_description or txn.description
            plaid_txn["reference_number"] = txn.reference_number
            plaid_txn["location"] = txn.location
            plaid_txn["is_recurring"] = txn.is_recurring
            plaid_txn["check_number"] = txn.check_number
            
            transactions.append(plaid_txn)
        
        # Save transactions (deduplication happens in save_transactions)
        total_transactions = len(transactions)
        transactions_saved = db.save_transactions(user_id, account_id, transactions)
        transactions_duplicated = total_transactions - transactions_saved
        
        return {
            "account_id": account_id,
            "account_created": account_created,
            "transactions_saved": transactions_saved,
            "transactions_duplicated": transactions_duplicated,
            "total_transactions": total_transactions
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving parsed statement transactions: {str(e)}")
        raise


def save_parsed_statement_transactions_from_json(
    json_path: Union[str, Path],
    db,
    user_id: str,
    auto_create_account: bool = True
) -> Dict[str, Any]:
    """
    Save transactions from a parsed statement JSON file.
    
    Args:
        json_path: Path to the parsed statement JSON file
        db: JSONDatabase instance
        user_id: User ID to associate transactions with
        auto_create_account: Whether to automatically create an account if needed
    
    Returns:
        Same as save_parsed_statement_transactions
    """
    import json
    from src.services.statement_parser import ParsedStatement
    
    # Load the parsed statement
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Reconstruct ParsedStatement object
    parsed = ParsedStatement.model_validate(data)
    
    # Extract filename from path
    filename = Path(json_path).name
    
    return save_parsed_statement_transactions(
        parsed, db, user_id, filename, auto_create_account
    )

