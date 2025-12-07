"""PostgreSQL database operations for Smart Expense Analyzer"""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.config import Config
from src.models import init_db, get_session, User, Account, Transaction


class PostgreSQLDatabase:
    """PostgreSQL database implementation using SQLAlchemy"""
    
    def __init__(self):
        """Initialize database connection"""
        from src.models import CLOUD_SQL_AVAILABLE
        
        # Initialize database connection if not already done
        if Config.USE_CLOUD_SQL:
            if not CLOUD_SQL_AVAILABLE:
                raise ImportError(
                    "cloud-sql-python-connector is not installed. Install it with:\n"
                    "  pip install 'cloud-sql-python-connector[pg8000]'\n\n"
                    "Or use local PostgreSQL by setting:\n"
                    "  USE_CLOUD_SQL=false\n"
                    "  DB_CONNECTION_STRING=postgresql://user:pass@localhost:5432/dbname"
                )
            init_db(use_cloud_sql=True)
        elif Config.DB_CONNECTION_STRING:
            init_db(connection_string=Config.DB_CONNECTION_STRING)
        else:
            raise ValueError(
                "Database configuration missing. Set either:\n"
                "  - USE_CLOUD_SQL=true with CLOUD_SQL_CONNECTION_NAME (for Cloud SQL), or\n"
                "  - DB_CONNECTION_STRING=postgresql://user:pass@localhost:5432/dbname (for local PostgreSQL)\n"
                "See LOCAL_SETUP.md for local development instructions."
            )
    
    def _get_session(self) -> Session:
        """Get database session"""
        return get_session()
    
    # ========== User Operations ==========
    
    def create_user(self, username: str, password: str, email: str) -> Dict:
        """Create a new user account"""
        session = self._get_session()
        try:
            # Check if username already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                raise ValueError("Username already exists")
            
            user_id = str(uuid.uuid4())
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=hashed_password,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return user.to_dict()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        session = self._get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                return None
            
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            if user.password_hash == hashed_password:
                return user.to_dict()
            
            return None
        finally:
            session.close()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        session = self._get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            return user.to_dict() if user else None
        finally:
            session.close()
    
    # ========== Bank Account Operations ==========
    
    def save_bank_account(self, user_id: str, account_data: Dict) -> Dict:
        """Save a new bank account for a user"""
        session = self._get_session()
        try:
            # Check if account already exists by account_id
            existing = session.query(Account).filter(
                and_(
                    Account.user_id == user_id,
                    Account.account_id == account_data.get("account_id")
                )
            ).first()
            
            if existing:
                # Update existing account
                for key, value in account_data.items():
                    if hasattr(existing, key) and key not in ["id", "user_id"]:
                        setattr(existing, key, value)
                existing.last_synced = datetime.utcnow() if account_data.get("last_synced") else existing.last_synced
                session.commit()
                session.refresh(existing)
                return existing.to_dict()
            
            # Create new account
            account = Account(
                user_id=user_id,
                account_id=account_data.get("account_id"),
                name=account_data.get("name"),
                type=account_data.get("type"),
                subtype=account_data.get("subtype"),
                mask=account_data.get("mask"),
                current_balance=account_data.get("current_balance"),
                available_balance=account_data.get("available_balance"),
                limit=account_data.get("limit"),
                currency=account_data.get("currency", "USD"),
                access_token=account_data.get("access_token"),
                item_id=account_data.get("item_id"),
                institution_name=account_data.get("institution_name"),
                institution_id=account_data.get("institution_id"),
                official_name=account_data.get("official_name"),
                verification_status=account_data.get("verification_status"),
                cursor=account_data.get("cursor"),
                source=account_data.get("source", "plaid"),
                statement_period=account_data.get("statement_period"),
                created_at=datetime.utcnow(),
                last_synced=datetime.utcnow() if account_data.get("last_synced") else None,
            )
            
            session.add(account)
            session.commit()
            session.refresh(account)
            
            return account.to_dict()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_user_accounts(self, user_id: str) -> List[Dict]:
        """Get all bank accounts for a user"""
        session = self._get_session()
        try:
            accounts = session.query(Account).filter(Account.user_id == user_id).all()
            return [acc.to_dict() for acc in accounts]
        finally:
            session.close()
    
    def delete_account(self, user_id: str, account_id: str) -> bool:
        """Delete a bank account by internal ID (not account_id)"""
        session = self._get_session()
        try:
            account = session.query(Account).filter(
                and_(
                    Account.id == account_id,
                    Account.user_id == user_id
                )
            ).first()
            
            if account:
                session.delete(account)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== Transaction Operations ==========
    
    def save_transactions(self, user_id: str, account_id: str, transactions: List[Dict]) -> int:
        """Save transactions for a specific account with deduplication"""
        from src.services.transaction_deduplicator import get_deduplicator
        
        session = self._get_session()
        try:
            # Get account by account_id (Plaid account_id, not internal ID)
            account = session.query(Account).filter(
                and_(
                    Account.account_id == account_id,
                    Account.user_id == user_id
                )
            ).first()
            
            if not account:
                raise ValueError(f"Account {account_id} not found for user {user_id}")
            
            # Get all existing transactions for this user for deduplication
            existing_user_transactions = self.get_all_user_transactions(user_id)
            
            # Use deduplicator to find unique transactions
            deduplicator = get_deduplicator()
            result = deduplicator.deduplicate_transactions(transactions, existing_user_transactions)
            
            unique_new = result["unique_new"]
            
            # Insert unique transactions
            for txn_data in unique_new:
                # Check if transaction already exists by transaction_id
                existing_txn = session.query(Transaction).filter(
                    Transaction.transaction_id == txn_data.get("transaction_id")
                ).first()
                
                if existing_txn:
                    continue  # Skip duplicates
                
                transaction = Transaction(
                    transaction_id=txn_data.get("transaction_id"),
                    account_id=account.id,  # Use internal account ID
                    user_id=user_id,
                    amount=txn_data.get("amount"),
                    date=datetime.strptime(txn_data.get("date"), "%Y-%m-%d").date() if isinstance(txn_data.get("date"), str) else txn_data.get("date"),
                    authorized_date=datetime.strptime(txn_data.get("authorized_date"), "%Y-%m-%d").date() if isinstance(txn_data.get("authorized_date"), str) else txn_data.get("authorized_date"),
                    name=txn_data.get("name"),
                    merchant_name=txn_data.get("merchant_name"),
                    merchant_entity_id=txn_data.get("merchant_entity_id"),
                    logo_url=txn_data.get("logo_url"),
                    website=txn_data.get("website"),
                    category=txn_data.get("category"),
                    category_id=txn_data.get("category_id"),
                    personal_finance_category=txn_data.get("personal_finance_category"),
                    personal_finance_category_icon_url=txn_data.get("personal_finance_category_icon_url"),
                    location=txn_data.get("location"),
                    payment_channel=txn_data.get("payment_channel"),
                    pending=txn_data.get("pending", False),
                    transaction_type=txn_data.get("transaction_type"),
                    account_owner=txn_data.get("account_owner"),
                    transaction_code=txn_data.get("transaction_code"),
                    source=txn_data.get("source", "plaid"),
                    original_description=txn_data.get("original_description"),
                    reference_number=txn_data.get("reference_number"),
                    location_text=txn_data.get("location"),
                    is_recurring=txn_data.get("is_recurring", False),
                    check_number=txn_data.get("check_number"),
                    saved_at=datetime.utcnow(),
                )
                
                session.add(transaction)
            
            session.commit()
            return len(unique_new)
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_transactions(self, user_id: str, account_id: str = None) -> List[Dict]:
        """Get transactions for a user or specific account"""
        session = self._get_session()
        try:
            query = session.query(Transaction).filter(Transaction.user_id == user_id)
            
            if account_id:
                # account_id here is the Plaid account_id, need to find internal account ID
                account = session.query(Account).filter(
                    and_(
                        Account.account_id == account_id,
                        Account.user_id == user_id
                    )
                ).first()
                
                if account:
                    query = query.filter(Transaction.account_id == account.id)
                else:
                    return []  # Account not found
            
            transactions = query.order_by(Transaction.date.desc()).all()
            return [txn.to_dict() for txn in transactions]
        finally:
            session.close()
    
    def get_all_user_transactions(self, user_id: str) -> List[Dict]:
        """Get all transactions across all accounts for a user"""
        return self.get_transactions(user_id, account_id=None)
    
    def delete_transactions(self, user_id: str, account_id: str) -> bool:
        """Delete all transactions for an account"""
        session = self._get_session()
        try:
            # Find account by Plaid account_id
            account = session.query(Account).filter(
                and_(
                    Account.account_id == account_id,
                    Account.user_id == user_id
                )
            ).first()
            
            if account:
                deleted = session.query(Transaction).filter(
                    Transaction.account_id == account.id
                ).delete()
                session.commit()
                return deleted > 0
            return False
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ========== Utility Operations ==========
    
    def clear_all_data(self):
        """Clear all data (for testing purposes)"""
        session = self._get_session()
        try:
            session.query(Transaction).delete()
            session.query(Account).delete()
            session.query(User).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        session = self._get_session()
        try:
            total_users = session.query(User).count()
            total_accounts = session.query(Account).count()
            total_transactions = session.query(Transaction).count()
            
            return {
                "total_users": total_users,
                "total_accounts": total_accounts,
                "total_transactions": total_transactions,
                "database_type": "PostgreSQL (Cloud SQL)" if Config.USE_CLOUD_SQL else "PostgreSQL (Local)"
            }
        finally:
            session.close()
