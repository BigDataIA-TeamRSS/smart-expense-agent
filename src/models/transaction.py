"""Transaction model"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base


class Transaction(Base):
    """Transaction model"""
    
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, nullable=False, unique=True, index=True)  # Plaid transaction_id or PDF-generated ID
    account_id = Column(String, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core transaction data
    amount = Column(Float, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    authorized_date = Column(Date, nullable=True)
    name = Column(String(500), nullable=False)
    
    # Merchant information
    merchant_name = Column(String(255), nullable=True)
    merchant_entity_id = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Categorization
    category = Column(JSON, nullable=True)  # Array of category strings
    category_id = Column(String(100), nullable=True)
    personal_finance_category = Column(JSON, nullable=True)  # Plaid category structure
    personal_finance_category_icon_url = Column(String(500), nullable=True)
    
    # Location data
    location = Column(JSON, nullable=True)  # Address, city, region, postal_code, country, lat, lon, store_number
    
    # Transaction metadata
    payment_channel = Column(String(50), nullable=True)  # online, in store, other
    pending = Column(Boolean, default=False, nullable=False)
    transaction_type = Column(String(50), nullable=True)  # place, digital, special, unresolved
    account_owner = Column(String(255), nullable=True)
    transaction_code = Column(String(50), nullable=True)
    
    # PDF upload specific fields
    source = Column(String(50), default="plaid")  # "plaid" or "pdf_upload"
    original_description = Column(String(1000), nullable=True)
    reference_number = Column(String(255), nullable=True)
    location_text = Column(String(255), nullable=True)  # Simple location string from PDF
    is_recurring = Column(Boolean, default=False)
    check_number = Column(String(50), nullable=True)
    
    # Timestamps
    saved_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "authorized_date": self.authorized_date.isoformat() if self.authorized_date else None,
            "name": self.name,
            "merchant_name": self.merchant_name,
            "merchant_entity_id": self.merchant_entity_id,
            "logo_url": self.logo_url,
            "website": self.website,
            "category": self.category,
            "category_id": self.category_id,
            "personal_finance_category": self.personal_finance_category,
            "personal_finance_category_icon_url": self.personal_finance_category_icon_url,
            "location": self.location,
            "payment_channel": self.payment_channel,
            "pending": self.pending,
            "transaction_type": self.transaction_type,
            "account_owner": self.account_owner,
            "transaction_code": self.transaction_code,
            "source": self.source,
            "original_description": self.original_description,
            "reference_number": self.reference_number,
            "location_text": self.location_text,
            "is_recurring": self.is_recurring,
            "check_number": self.check_number,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }
