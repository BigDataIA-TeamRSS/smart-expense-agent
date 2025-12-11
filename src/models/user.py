# """User model"""

# from sqlalchemy import Column, String, DateTime
# from sqlalchemy.orm import relationship
# from datetime import datetime
# import uuid

# from src.models import Base


# class User(Base):
#     """User model for authentication and user data"""
    
#     __tablename__ = "users"
    
#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     username = Column(String(50), unique=True, nullable=False, index=True)
#     email = Column(String(255), nullable=False, index=True)
#     password_hash = Column(String(255), nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
#     # Relationships
#     accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    
#     def to_dict(self, exclude_password=True):
#         """Convert user to dictionary"""
#         data = {
#             "id": self.id,
#             "username": self.username,
#             "email": self.email,
#             "created_at": self.created_at.isoformat() if self.created_at else None,
#         }
#         if not exclude_password:
#             data["password"] = self.password_hash
#         return data
"""User model with optional profile fields for personalization"""

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.models import Base


class User(Base):
    """User model for authentication and user data"""
    
    __tablename__ = "users"
    
    # ========== REQUIRED FIELDS ==========
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ========== NEW: OPTIONAL PROFILE FIELDS ==========
    # Financial Profile (for income-based budgeting)
    monthly_income = Column(Numeric(12, 2), nullable=True)
    
    # Demographic Profile (for life-stage adjustments)
    life_stage = Column(String(50), nullable=True)
    dependents = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)
    
    # ========== USER PREFERENCES ==========
    budget_alert_threshold = Column(Numeric(3, 2), default=1.30, nullable=True)
    
    # ========== PROFILE TRACKING ==========
    profile_completed = Column(Boolean, default=False)
    profile_completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # ========== RELATIONSHIPS ==========
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self, exclude_password=True):
        """Convert user to dictionary"""
        data = {
            # Required fields
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            
            # OPTIONAL Profile fields (may be None)
            "monthly_income": float(self.monthly_income) if self.monthly_income else None,
            "life_stage": self.life_stage,
            "dependents": self.dependents,
            "location": self.location,
            
            # Preferences
            "budget_alert_threshold": float(self.budget_alert_threshold) if self.budget_alert_threshold else 1.30,
            
            # Profile completion status
            "profile_completed": self.profile_completed or False,
            "profile_completed_at": self.profile_completed_at.isoformat() if self.profile_completed_at else None
        }
        
        if not exclude_password:
            data["password"] = self.password_hash
        
        return data
    
    def has_complete_profile(self):
        """Check if user has completed their profile"""
        return any([
            self.monthly_income is not None,
            self.life_stage is not None,
            self.dependents is not None,
            self.location is not None
        ])
    
    def get_personalization_level(self):
        """Get what level of personalization is available for this user"""
        return {
            'basic': True,  # Everyone gets historical baseline
            'income_based': self.monthly_income is not None,
            'life_stage_aware': self.life_stage is not None,
            'location_aware': self.location is not None,
            'full_personalization': self.has_complete_profile()
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, profile_completed={self.profile_completed})>"