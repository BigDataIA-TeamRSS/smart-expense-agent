"""Account management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.app.dependencies import get_current_user, get_db, get_plaid_service
from src.app.schemas.account import AccountResponse
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
async def get_accounts(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get all user accounts"""
    accounts = db.get_user_accounts(current_user["id"])
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get specific account"""
    accounts = db.get_user_accounts(current_user["id"])
    account = next((a for a in accounts if a.get("id") == account_id), None)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/{account_id}/refresh")
async def refresh_account(
    account_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
    plaid_service = Depends(get_plaid_service)
):
    """Refresh a single account's data"""
    accounts = db.get_user_accounts(current_user["id"])
    account = next((a for a in accounts if a.get("id") == account_id), None)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    access_token = account.get('access_token')
    if not access_token:
        # Check if this is a PDF-uploaded account
        account_source = account.get('source', 'plaid')
        if account_source == 'pdf_upload':
            raise HTTPException(
                status_code=400, 
                detail="PDF-uploaded accounts cannot be refreshed via Plaid. Only Plaid-connected accounts can be refreshed."
            )
        raise HTTPException(
            status_code=400, 
            detail="Account not connected via Plaid. Missing access_token."
        )
    
    try:
        # Get updated account information
        updated_accounts = plaid_service.get_accounts(access_token)
        
        # Update account balance
        for updated in updated_accounts:
            if updated['account_id'] == account['account_id']:
                account.update({
                    'current_balance': updated['current_balance'],
                    'available_balance': updated['available_balance'],
                    'limit': updated.get('limit'),
                    'last_synced': datetime.now().isoformat()
                })
                db.save_bank_account(current_user["id"], account)
                break
        
        # Sync new transactions
        sync_result = plaid_service.sync_transactions(access_token, account.get('cursor'))
        
        new_count = 0
        if sync_result['transactions']:
            new_count = db.save_transactions(
                current_user["id"],
                account["account_id"],
                sync_result['transactions']
            )
            
            # Update cursor
            if sync_result.get('cursor'):
                account['cursor'] = sync_result['cursor']
                db.save_bank_account(current_user["id"], account)
        
        return {
            "message": "Account refreshed successfully",
            "new_transactions": new_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing account: {str(e)}")


@router.post("/refresh-all")
async def refresh_all_accounts(
    current_user = Depends(get_current_user),
    db = Depends(get_db),
    plaid_service = Depends(get_plaid_service)
):
    """Refresh all accounts"""
    accounts = db.get_user_accounts(current_user["id"])
    total_new_transactions = 0
    
    for account in accounts:
        try:
            access_token = account.get('access_token')
            if not access_token:
                continue
            
            # Get updated account information
            updated_accounts = plaid_service.get_accounts(access_token)
            
            # Update account balances
            for updated in updated_accounts:
                if updated['account_id'] == account['account_id']:
                    account.update({
                        'current_balance': updated['current_balance'],
                        'available_balance': updated['available_balance'],
                        'limit': updated.get('limit'),
                        'last_synced': datetime.now().isoformat()
                    })
                    db.save_bank_account(current_user["id"], account)
                    break
            
            # Sync transactions
            sync_result = plaid_service.sync_transactions(
                access_token,
                account.get('cursor')
            )
            
            if sync_result['transactions']:
                new_count = db.save_transactions(
                    current_user["id"],
                    account["account_id"],
                    sync_result['transactions']
                )
                total_new_transactions += new_count
                
                # Update cursor
                if sync_result.get('cursor'):
                    account['cursor'] = sync_result['cursor']
                    db.save_bank_account(current_user["id"], account)
        except Exception as e:
            # Continue with other accounts if one fails
            continue
    
    return {
        "message": "All accounts refreshed",
        "total_new_transactions": total_new_transactions
    }


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete an account"""
    success = db.delete_account(current_user["id"], account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}
