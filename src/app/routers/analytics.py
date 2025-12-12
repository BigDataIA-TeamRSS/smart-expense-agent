"""Analytics endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict
from src.app.dependencies import get_current_user, get_db
from src.app.schemas.common import DashboardResponse

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get dashboard summary data"""
    user_id = current_user["id"]
    
    # Get data
    accounts = db.get_user_accounts(user_id)
    transactions = db.get_all_user_transactions(user_id)
    
    # Calculate metrics
    total_accounts = len(accounts)
    total_transactions = len(transactions)
    total_balance = sum(acc.get("current_balance", 0) or 0 for acc in accounts)
    
    # Get recent transactions
    recent = sorted(transactions, key=lambda x: x.get("date", ""), reverse=True)[:10]
    
    return DashboardResponse(
        total_accounts=total_accounts,
        total_transactions=total_transactions,
        total_balance=total_balance,
        recent_transactions=recent
    )


@router.get("/spending-by-category")
async def get_spending_by_category(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get spending breakdown by category"""
    transactions = db.get_transactions(current_user["id"])
    
    # Filter by date if provided
    if start_date:
        transactions = [t for t in transactions if t.get("date", "") >= start_date]
    if end_date:
        transactions = [t for t in transactions if t.get("date", "") <= end_date]
    
    # Calculate spending by category
    # Plaid format: positive = money out (expenses), negative = money in (income)
    category_spending = {}
    for txn in transactions:
        amount = txn.get("amount", 0)
        if amount > 0:  # Only expenses (positive amounts)
            category = txn.get("category", ["Uncategorized"])
            if isinstance(category, list):
                category = category[0] if category else "Uncategorized"
            category_spending[category] = category_spending.get(category, 0) + amount
    
    return category_spending


@router.get("/monthly-trends")
async def get_monthly_trends(
    months: int = Query(6, ge=1, le=24),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get monthly spending trends"""
    transactions = db.get_transactions(current_user["id"])
    
    # Group by month
    monthly_data = {}
    for txn in transactions:
        date_str = txn.get("date", "")
        if date_str:
            month_key = date_str[:7]  # YYYY-MM
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0, "expenses": 0}
            
            amount = txn.get("amount", 0)
            # Plaid format: positive = expenses, negative = income
            if amount > 0:
                monthly_data[month_key]["expenses"] += amount
            else:
                monthly_data[month_key]["income"] += abs(amount)
    
    return monthly_data
