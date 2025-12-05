# database.py
"""JSON-based database operations for Smart Expense Analyzer POC"""

import json
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.config import Config

# class Config:
#     """Configuration settings (put this in database.py if you don't have config.py)"""
#     DATA_DIR = Path("data")
#     USERS_FILE = DATA_DIR / "users.json"
#     ACCOUNTS_FILE = DATA_DIR / "accounts.json"
#     TRANSACTIONS_FILE = DATA_DIR / "transactions.json"

class JSONDatabase:
    """Simple JSON file-based database for POC"""
    
    def __init__(self):
        """Initialize database and create data directory if needed"""
        Config.DATA_DIR.mkdir(exist_ok=True)
        self._init_file(Config.USERS_FILE, {})
        self._init_file(Config.ACCOUNTS_FILE, {})
        self._init_file(Config.TRANSACTIONS_FILE, {})
    
    def _init_file(self, filepath: Path, default_data: Any):
        """Initialize JSON file if it doesn't exist"""
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(default_data, f, indent=2)
    
    def _read_file(self, filepath: Path) -> Any:
        """Read and return JSON file contents"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} if filepath != Config.TRANSACTIONS_FILE else []
    
    def _write_file(self, filepath: Path, data: Any):
        """Write data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # ========== User Operations ==========
    
    def create_user(self, username: str, password: str, email: str) -> Dict:
        """Create a new user account"""
        users = self._read_file(Config.USERS_FILE)
        
        if username in users:
            raise ValueError("Username already exists")
        
        user_id = str(uuid.uuid4())
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = {
            "id": user_id,
            "username": username,
            "password": hashed_password,
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        
        users[username] = user
        self._write_file(Config.USERS_FILE, users)
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        users = self._read_file(Config.USERS_FILE)
        
        if username not in users:
            return None
        
        user = users[username]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if user["password"] == hashed_password:
            # Don't return password in response
            safe_user = {k: v for k, v in user.items() if k != "password"}
            return safe_user
        
        return None
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        users = self._read_file(Config.USERS_FILE)
        if username in users:
            user = users[username].copy()
            user.pop("password", None)  # Remove password from response
            return user
        return None
    
    # ========== Bank Account Operations ==========
    
    def save_bank_account(self, user_id: str, account_data: Dict) -> Dict:
        """Save a new bank account for a user"""
        accounts = self._read_file(Config.ACCOUNTS_FILE)
        
        if user_id not in accounts:
            accounts[user_id] = []
        
        # Check if account already exists
        existing_account_ids = [acc.get("account_id") for acc in accounts[user_id]]
        if account_data.get("account_id") in existing_account_ids:
            # Update existing account
            for i, acc in enumerate(accounts[user_id]):
                if acc.get("account_id") == account_data.get("account_id"):
                    accounts[user_id][i].update(account_data)
                    self._write_file(Config.ACCOUNTS_FILE, accounts)
                    return accounts[user_id][i]
        
        # Add new account
        account_data["id"] = str(uuid.uuid4())
        account_data["created_at"] = datetime.now().isoformat()
        accounts[user_id].append(account_data)
        
        self._write_file(Config.ACCOUNTS_FILE, accounts)
        return account_data
    
    def get_user_accounts(self, user_id: str) -> List[Dict]:
        """Get all bank accounts for a user"""
        accounts = self._read_file(Config.ACCOUNTS_FILE)
        return accounts.get(user_id, [])
    
    def delete_account(self, user_id: str, account_id: str) -> bool:
        """Delete a bank account"""
        accounts = self._read_file(Config.ACCOUNTS_FILE)
        
        if user_id in accounts:
            accounts[user_id] = [
                acc for acc in accounts[user_id] 
                if acc.get("id") != account_id
            ]
            self._write_file(Config.ACCOUNTS_FILE, accounts)
            return True
        return False
    
    # ========== Transaction Operations ==========
    
    def save_transactions(self, user_id: str, account_id: str, transactions: List[Dict]):
        """Save transactions for a specific account"""
        all_transactions = self._read_file(Config.TRANSACTIONS_FILE)
        
        key = f"{user_id}_{account_id}"
        if key not in all_transactions:
            all_transactions[key] = []
        
        # Add new transactions (avoid duplicates based on transaction_id)
        existing_ids = {t.get("transaction_id") for t in all_transactions[key]}
        
        new_transactions = []
        for txn in transactions:
            if txn.get("transaction_id") not in existing_ids:
                txn["saved_at"] = datetime.now().isoformat()
                new_transactions.append(txn)
                all_transactions[key].append(txn)
        
        if new_transactions:
            self._write_file(Config.TRANSACTIONS_FILE, all_transactions)
        
        return len(new_transactions)
    
    def get_transactions(self, user_id: str, account_id: str = None) -> List[Dict]:
        """Get transactions for a user or specific account"""
        all_transactions = self._read_file(Config.TRANSACTIONS_FILE)
        
        if account_id:
            # Get transactions for specific account
            key = f"{user_id}_{account_id}"
            return all_transactions.get(key, [])
        else:
            # Get all transactions for user across all accounts
            user_transactions = []
            for key in all_transactions:
                if key.startswith(f"{user_id}_"):
                    user_transactions.extend(all_transactions[key])
            return user_transactions
    
    def get_all_user_transactions(self, user_id: str) -> List[Dict]:
        """Get all transactions across all accounts for a user"""
        return self.get_transactions(user_id, account_id=None)
    
    def delete_transactions(self, user_id: str, account_id: str) -> bool:
        """Delete all transactions for an account"""
        all_transactions = self._read_file(Config.TRANSACTIONS_FILE)
        key = f"{user_id}_{account_id}"
        
        if key in all_transactions:
            del all_transactions[key]
            self._write_file(Config.TRANSACTIONS_FILE, all_transactions)
            return True
        return False
    
    # ========== Utility Operations ==========
    
    def clear_all_data(self):
        """Clear all data (for testing purposes)"""
        self._write_file(Config.USERS_FILE, {})
        self._write_file(Config.ACCOUNTS_FILE, {})
        self._write_file(Config.TRANSACTIONS_FILE, {})
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database"""
        users = self._read_file(Config.USERS_FILE)
        accounts = self._read_file(Config.ACCOUNTS_FILE)
        transactions = self._read_file(Config.TRANSACTIONS_FILE)
        
        total_accounts = sum(len(accs) for accs in accounts.values())
        total_transactions = sum(len(txns) for txns in transactions.values())
        
        return {
            "total_users": len(users),
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "data_files": {
                "users": str(Config.USERS_FILE),
                "accounts": str(Config.ACCOUNTS_FILE),
                "transactions": str(Config.TRANSACTIONS_FILE)
            }
        }