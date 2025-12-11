#uvicorn app.main:app --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from plaid_handler import exchange_public_token, get_transactions
from datetime import datetime, timedelta

app = FastAPI(title="Smart Expense Analyzer")

class PlaidExchangeRequest(BaseModel):
    public_token: str

@app.post("/api/plaid/exchange")
async def exchange_token(request: PlaidExchangeRequest):
    """Exchange public token for access token"""
    try:
        access_token, item_id = exchange_public_token(request.public_token)
        
        # Store access_token in database (you'll do this later)
        # For now, just return success
        
        return {
            "status": "success",
            "item_id": item_id,
            "message": "Bank connected successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/plaid/transactions")
async def fetch_transactions(access_token: str):
    """Fetch transactions from Plaid"""
    try:
        # Get last 30 days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        transactions = get_transactions(access_token, start_date, end_date)
        
        return {
            "count": len(transactions),
            "transactions": transactions
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))