# # config.py
# """Configuration settings for Smart Expense Analyzer POC"""

# from pathlib import Path
# import os
# from dotenv import load_dotenv
# load_dotenv()

# class Config:
#     """Application configuration"""
    
#     # Plaid Settings (Sandbox credentials)
#     PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
#     PLAID_SECRET = os.getenv("PLAID_SECRET")
#     PLAID_ENV = "sandbox"
#     PLAID_PRODUCTS = ["auth", "transactions"]
#     PLAID_COUNTRY_CODES = ["US", "CA"]
    
#     # Data storage paths
#     DATA_DIR = Path("data")
#     USERS_FILE = DATA_DIR / "json_db" / "users.json"
#     ACCOUNTS_FILE = DATA_DIR / "json_db" / "accounts.json"
#     TRANSACTIONS_FILE = DATA_DIR / "json_db" / "transactions.json"
    
#     # App settings
#     APP_NAME = "Smart Expense Analyzer POC"
#     APP_VERSION = "1.0.0"
    
#     # UI Settings
#     PAGE_ICON = "💰"
#     LAYOUT = "wide"
    
#     # Session keys
#     SESSION_KEYS = {
#         "db": "db",
#         "plaid": "plaid",
#         "logged_in": "logged_in",
#         "current_user": "current_user",
#         "link_token": "link_token",
#         "hosted_link_url": "hosted_link_url"
#     }

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
    
    # Gemini API (for PDF parsing)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Database Configuration
    # Set USE_POSTGRESQL=true to use PostgreSQL, otherwise uses JSON files
    USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
    
    # PostgreSQL / Cloud SQL Configuration
    # For local development: postgresql://user:password@localhost:5432/dbname
    # For Cloud SQL: Leave connection_string empty and set use_cloud_sql=True
    DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING", "")
    USE_CLOUD_SQL = os.getenv("USE_CLOUD_SQL", "false").lower() == "true"
    CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME", "")  # project:region:instance
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "smart_expense_db")
    
    # Data storage paths (for JSON fallback or migration)
    DATA_DIR = Path("data")
    JSON_DB_DIR = DATA_DIR / "json_db"
    USERS_FILE = JSON_DB_DIR / "users.json"
    ACCOUNTS_FILE = JSON_DB_DIR / "accounts.json"
    TRANSACTIONS_FILE = JSON_DB_DIR / "transactions.json"
    UPLOAD_HISTORY_FILE = JSON_DB_DIR / "upload_history.json"
    
    # App settings
    APP_NAME = "Smart Expense Analyzer POC"
    APP_VERSION = "1.0.0"
    
    # UI Settings
    PAGE_ICON = "💰"
    LAYOUT = "wide"
    
    # Statement Parser Settings
    SUPPORTED_FILE_TYPES = ["pdf"]
    MAX_FILE_SIZE_MB = 10
    
    # Transaction Categories (for manual categorization)
    TRANSACTION_CATEGORIES = [
        "Uncategorized",
        "Groceries",
        "Dining & Restaurants",
        "Transportation",
        "Gas & Fuel",
        "Shopping",
        "Entertainment",
        "Subscriptions",
        "Utilities",
        "Rent & Mortgage",
        "Healthcare",
        "Personal Care",
        "Travel",
        "Education",
        "Income",
        "Transfer",
        "Fees & Charges",
        "Other"
    ]
    
    # Session keys
    SESSION_KEYS = {
        "db": "db",
        "plaid": "plaid",
        "logged_in": "logged_in",
        "current_user": "current_user",
        "link_token": "link_token",
        "hosted_link_url": "hosted_link_url",
        "parser": "statement_parser"  # NEW
    }