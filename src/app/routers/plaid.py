"""Plaid integration endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.app.dependencies import get_current_user, get_db, get_plaid_service
from datetime import datetime

router = APIRouter()


class ExchangeTokenRequest(BaseModel):
    """Request schema for token exchange"""
    public_token: str


@router.post("/link-token")
async def create_link_token(
    current_user = Depends(get_current_user),
    plaid_service = Depends(get_plaid_service)
):
    """Create Plaid Link token for bank connection"""
    result = plaid_service.create_link_token(
        current_user["id"],
        current_user["email"]
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create link token")
    return result


@router.get("/link-status")
async def get_link_token_status(
    link_token: str,
    plaid_service = Depends(get_plaid_service)
):
    """Check the status of a link token"""
    status_result = plaid_service.get_link_token_status(link_token)
    return status_result


@router.post("/exchange-token")
async def exchange_public_token(
    request: ExchangeTokenRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
    plaid_service = Depends(get_plaid_service)
):
    """Exchange public token for access token and save accounts"""
    result = plaid_service.exchange_public_token(request.public_token)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to exchange token")
    
    access_token = result["access_token"]
    item_id = result["item_id"]
    
    # Get accounts from Plaid
    accounts = plaid_service.get_accounts(access_token)
    
    if not accounts:
        raise HTTPException(status_code=400, detail="No accounts found")
    
    # Save accounts to database
    saved_accounts = []
    for account_data in accounts:
        account_data["access_token"] = access_token
        account_data["item_id"] = item_id
        account_data["institution_id"] = result.get("institution_id")
        saved_account = db.save_bank_account(current_user["id"], account_data)
        saved_accounts.append(saved_account)
    
    # Sync transactions for all accounts
    total_saved = 0
    for account in accounts:
        sync_result = plaid_service.sync_transactions(access_token)
        if sync_result["transactions"]:
            # Group transactions by account
            account_transactions = [
                txn for txn in sync_result["transactions"]
                if txn["account_id"] == account["account_id"]
            ]
            if account_transactions:
                saved_count = db.save_transactions(
                    current_user["id"],
                    account["account_id"],
                    account_transactions
                )
                total_saved += saved_count
    
    return {
        "message": "Bank connected successfully",
        "accounts": saved_accounts,
        "transactions_saved": total_saved
    }


@router.post("/sync/{account_id}")
async def sync_transactions(
    account_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
    plaid_service = Depends(get_plaid_service)
):
    """Sync transactions for a specific account"""
    accounts = db.get_user_accounts(current_user["id"])
    account = next((a for a in accounts if a.get("id") == account_id), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if not account.get("access_token"):
        raise HTTPException(status_code=400, detail="Account not connected via Plaid")
    
    # Sync transactions
    sync_result = plaid_service.sync_transactions(
        account["access_token"],
        cursor=account.get("cursor")
    )
    
    # Save transactions
    saved_count = 0
    if sync_result["transactions"]:
        saved_count = db.save_transactions(
            current_user["id"],
            account["account_id"],
            sync_result["transactions"]
        )
        
        # Update cursor
        if sync_result.get("cursor"):
            account["cursor"] = sync_result["cursor"]
            account["last_synced"] = datetime.now().isoformat()
            db.save_bank_account(current_user["id"], account)
    
    return {
        "message": "Transactions synced successfully",
        "transactions_saved": saved_count,
        "total_fetched": sync_result.get("total_transactions", len(sync_result["transactions"]))
    }
