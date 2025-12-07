"""Account model"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base


class Account(Base):
    """Bank account model"""
    
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, nullable=False, index=True)  # Plaid account_id or PDF account identifier
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # depository, credit_card, etc.
    subtype = Column(String(50))  # checking, savings, etc.
    mask = Column(String(10))  # Last 4 digits
    current_balance = Column(Float)
    available_balance = Column(Float)
    limit = Column(Float, nullable=True)  # Credit limit for credit cards
    currency = Column(String(10), default="USD")
    
    # Plaid-specific fields
    access_token = Column(String, nullable=True)  # Encrypted in production
    item_id = Column(String, nullable=True)
    institution_name = Column(String(255), nullable=True)
    institution_id = Column(String(100), nullable=True)
    official_name = Column(String(255), nullable=True)
    verification_status = Column(String(50), nullable=True)
    cursor = Column(String, nullable=True)  # For Plaid sync
    
    # PDF upload fields
    source = Column(String(50), default="plaid")  # "plaid" or "pdf_upload"
    statement_period = Column(JSON, nullable=True)  # {"start": "2024-12-16", "end": "2025-01-15"}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_synced = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert account to dictionary"""
        return {
            "id": self.id,
            "account_id": self.account_id,
            "name": self.name,
            "type": self.type,
            "subtype": self.subtype,
            "mask": self.mask,
            "current_balance": self.current_balance,
            "available_balance": self.available_balance,
            "limit": self.limit,
            "currency": self.currency,
            "institution_name": self.institution_name,
            "institution_id": self.institution_id,
            "official_name": self.official_name,
            "verification_status": self.verification_status,
            "source": self.source,
            "statement_period": self.statement_period,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "cursor": self.cursor,
        }
