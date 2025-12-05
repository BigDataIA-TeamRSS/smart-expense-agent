# config.py
"""Configuration settings for Smart Expense Analyzer POC"""

from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    """Application configuration"""
    
    # Plaid Settings (Sandbox credentials)
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET = os.getenv("PLAID_SECRET")
    PLAID_ENV = "sandbox"
    PLAID_PRODUCTS = ["auth", "transactions"]
    PLAID_COUNTRY_CODES = ["US", "CA"]
    
    # Data storage paths
    DATA_DIR = Path("data")
    USERS_FILE = DATA_DIR / "users.json"
    ACCOUNTS_FILE = DATA_DIR / "accounts.json"
    TRANSACTIONS_FILE = DATA_DIR / "transactions.json"
    
    # App settings
    APP_NAME = "Smart Expense Analyzer POC"
    APP_VERSION = "1.0.0"
    
    # UI Settings
    PAGE_ICON = "💰"
    LAYOUT = "wide"
    
    # Session keys
    SESSION_KEYS = {
        "db": "db",
        "plaid": "plaid",
        "logged_in": "logged_in",
        "current_user": "current_user",
        "link_token": "link_token",
        "hosted_link_url": "hosted_link_url"
    }