# src/models/processed_transaction.py
from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base

class ProcessedTransaction(Base):
    __tablename__ = "processed_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Assuming transaction_id in this table matches Transaction.transaction_id
    transaction_id = Column(
        String,
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # AI fields
    category_ai = Column(String(255), nullable=True)
    merchant_standardized = Column(String(255), nullable=True)
    is_subscription = Column(Boolean, default=False, nullable=False)
    subscription_id = Column(String(255), nullable=True)
    subscription_confidence = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_score = Column(Float, default=0.0, nullable=False)
    anomaly_reason = Column(String(1000), nullable=True)
    is_bill = Column(Boolean, default=False, nullable=False)
    bill_cycle_day = Column(String(10), nullable=True)  # or Integer if you want
    tags = Column(String(1000), nullable=True)          # or JSON, depending on how you store it
    notes = Column(String(2000), nullable=True)

    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_version = Column(String(50), default="1.0", nullable=False)

    transaction = relationship(
        "Transaction",
        back_populates="processed",
        uselist=False,
    )
