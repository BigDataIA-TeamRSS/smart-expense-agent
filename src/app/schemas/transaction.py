"""Transaction-related Pydantic schemas"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Union
from datetime import date, datetime


class TransactionResponse(BaseModel):
    """Schema for transaction response"""
    transaction_id: str
    account_id: str
    amount: float
    date: str
    authorized_date: Optional[str] = None
    name: str
    merchant_name: Optional[str] = None
    category: Optional[List[str]] = None
    personal_finance_category: Optional[Dict] = None
    location: Optional[Dict] = None
    pending: bool = False
    source: str = "plaid"
    saved_at: Optional[str] = None
    
    @field_validator('location', mode='before')
    @classmethod
    def normalize_location(cls, v):
        """Normalize location to dict if it's a string"""
        if v is None:
            return None
        if isinstance(v, str):
            # Convert string like 'WA' to dict format
            print(f"[SCHEMA] Converting location string '{v}' to dict")
            return {"region": v, "city": None, "address": None}
        if isinstance(v, dict):
            return v
        # If it's neither string nor dict, return None
        print(f"[SCHEMA] Invalid location type: {type(v)}, returning None")
        return None
    
    class Config:
        from_attributes = True


class TransactionSummary(BaseModel):
    """Schema for transaction summary"""
    total_transactions: int
    total_income: float
    total_expenses: float
    net_amount: float
