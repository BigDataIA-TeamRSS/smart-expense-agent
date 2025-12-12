"""Account-related Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class AccountResponse(BaseModel):
    """Schema for account response"""
    id: str
    account_id: str
    name: str
    type: str
    subtype: Optional[str] = None
    mask: Optional[str] = None
    current_balance: Optional[float] = None
    available_balance: Optional[float] = None
    limit: Optional[float] = None
    currency: str = "USD"
    institution_name: Optional[str] = None
    institution_id: Optional[str] = None
    source: str = "plaid"
    created_at: Optional[str] = None
    last_synced: Optional[str] = None
    
    class Config:
        from_attributes = True
