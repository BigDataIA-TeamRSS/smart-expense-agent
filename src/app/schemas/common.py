"""Common Pydantic schemas"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class DashboardResponse(BaseModel):
    """Schema for dashboard data"""
    total_accounts: int
    total_transactions: int
    total_balance: float
    recent_transactions: List[Dict]


class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str
    success: bool = True
