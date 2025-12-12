"""Transaction endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import date
from src.app.dependencies import get_current_user, get_db
from src.app.schemas.transaction import TransactionResponse, TransactionSummary

router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    account_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    limit: int = Query(100, ge=1, le=10000),  # Increased limit for analytics
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user transactions with optional filtering"""
    print(f"[TRANSACTIONS] Getting transactions for user: {current_user['id']}, account_id: {account_id}")
    transactions = db.get_transactions(
        current_user["id"],
        account_id=account_id
    )
    print(f"[TRANSACTIONS] Retrieved {len(transactions)} transactions from database")
    
    # Normalize location field (convert strings to dicts)
    normalized_count = 0
    for txn in transactions:
        if txn.get("location") is not None:
            if isinstance(txn["location"], str):
                print(f"[TRANSACTIONS] Normalizing location from string '{txn['location']}' to dict")
                txn["location"] = {"region": txn["location"], "city": None, "address": None}
                normalized_count += 1
            elif not isinstance(txn["location"], dict):
                # If it's neither string nor dict, set to None
                print(f"[TRANSACTIONS] Invalid location type: {type(txn['location'])}, setting to None")
                txn["location"] = None
    
    if normalized_count > 0:
        print(f"[TRANSACTIONS] Normalized {normalized_count} location fields")
    
    # Apply date filtering
    if start_date:
        transactions = [t for t in transactions if t.get("date", "") >= start_date]
    if end_date:
        transactions = [t for t in transactions if t.get("date", "") <= end_date]
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        transactions = [
            t for t in transactions
            if search_lower in (t.get("name", "") + " " + str(t.get("merchant_name", ""))).lower()
        ]
    
    # Apply amount filtering
    if min_amount is not None:
        transactions = [t for t in transactions if abs(t.get("amount", 0)) >= min_amount]
    if max_amount is not None:
        transactions = [t for t in transactions if abs(t.get("amount", 0)) <= max_amount]
    
    # Sort by date (newest first)
    transactions = sorted(transactions, key=lambda x: x.get("date", ""), reverse=True)
    
    # Apply pagination
    return transactions[offset:offset+limit]


@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    account_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get transaction summary statistics"""
    transactions = db.get_transactions(current_user["id"], account_id=account_id)
    
    # Apply date filtering
    if start_date:
        transactions = [t for t in transactions if t.get("date", "") >= start_date]
    if end_date:
        transactions = [t for t in transactions if t.get("date", "") <= end_date]
    
    # Calculate summary stats
    total_expenses = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)
    total_income = abs(sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) < 0))
    
    return TransactionSummary(
        total_transactions=len(transactions),
        total_income=total_income,
        total_expenses=total_expenses,
        net_amount=total_income - total_expenses
    )
