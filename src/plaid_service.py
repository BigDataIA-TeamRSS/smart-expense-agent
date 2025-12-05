# # plaid_service.py
# """Plaid API integration service for Smart Expense Analyzer POC"""

# import streamlit as st
# from typing import Dict, List, Optional
# from datetime import datetime

# from plaid.api_client import ApiClient
# from plaid.configuration import Configuration, Environment
# from plaid.api import plaid_api
# from plaid.model.link_token_create_request import LinkTokenCreateRequest
# from plaid.model.country_code import CountryCode
# from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
# from plaid.model.products import Products
# from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
# from plaid.model.link_token_get_request import LinkTokenGetRequest
# from plaid.model.transactions_sync_request import TransactionsSyncRequest
# from plaid.model.accounts_get_request import AccountsGetRequest

# from src.config import Config

# from dotenv import load_dotenv
# load_dotenv()

# class PlaidService:
#     """Service for handling all Plaid API operations"""
    
#     def __init__(self):
#         """Initialize Plaid client with configuration"""
#         configuration = Configuration(
#             host=Environment.Sandbox,
#             api_key={
#                 "clientId": Config.PLAID_CLIENT_ID,
#                 "secret": Config.PLAID_SECRET,
#             }
#         )
        
#         api_client = ApiClient(configuration)
#         self.client = plaid_api.PlaidApi(api_client)
    
#     def create_link_token(self, user_id: str, user_email: str) -> Optional[Dict]:
#         """
#         Create a Plaid Link token for bank connection
        
#         Args:
#             user_id: Unique user identifier
#             user_email: User's email address
            
#         Returns:
#             Dict with link_token and hosted_link_url, or None if error
#         """
#         try:
#             # Create Products and CountryCode objects
#             products = [Products(p) for p in Config.PLAID_PRODUCTS]
#             country_codes = [CountryCode(c) for c in Config.PLAID_COUNTRY_CODES]
            
#             # Build the request
#             link_token_request = LinkTokenCreateRequest(
#                 products=products,
#                 client_name=Config.APP_NAME[:30],  # Max 30 chars
#                 country_codes=country_codes,
#                 language="en",
#                 user=LinkTokenCreateRequestUser(
#                     client_user_id=user_id,
#                     email_address=user_email,
#                 ),
#             )
            
#             # Enable Hosted Link
#             link_token_request['hosted_link'] = {}
            
#             # Create the link token
#             response = self.client.link_token_create(link_token_request)
#             data = response.to_dict()
            
#             return {
#                 "link_token": data["link_token"],
#                 "hosted_link_url": data.get("hosted_link_url"),
#                 "expiration": data.get("expiration")
#             }
            
#         except Exception as e:
#             st.error(f"Error creating link token: {str(e)}")
#             return None
    
#     def get_link_token_status(self, link_token: str) -> Dict:
#         """
#         Check the status of a link token
        
#         Args:
#             link_token: The link token to check
            
#         Returns:
#             Dict with status and related information
#         """
#         try:
#             request = LinkTokenGetRequest(link_token=link_token)
#             response = self.client.link_token_get(request)
#             data = response.to_dict()
            
#             # Check if link session is complete
#             link_sessions = data.get("link_sessions", [])
#             if link_sessions:
#                 latest_session = link_sessions[-1]
#                 results = latest_session.get("results", {})
#                 item_add_results = results.get("item_add_results", [])
                
#                 if item_add_results:
#                     return {
#                         "status": "success",
#                         "public_token": item_add_results[0].get("public_token"),
#                         "accounts": item_add_results[0].get("accounts", []),
#                         "institution": item_add_results[0].get("institution", {})
#                     }
            
#             return {
#                 "status": "pending",
#                 "created_at": data.get("created_at"),
#                 "expiration": data.get("expiration")
#             }
            
#         except Exception as e:
#             return {"status": "error", "message": str(e)}
    
#     def exchange_public_token(self, public_token: str) -> Optional[Dict]:
#         """
#         Exchange a public token for an access token
        
#         Args:
#             public_token: The public token from Plaid Link
            
#         Returns:
#             Dict with access_token and item_id, or None if error
#         """
#         try:
#             request = ItemPublicTokenExchangeRequest(public_token=public_token)
#             response = self.client.item_public_token_exchange(request)
#             data = response.to_dict()
            
#             return {
#                 "access_token": data["access_token"],
#                 "item_id": data["item_id"]
#             }
            
#         except Exception as e:
#             st.error(f"Error exchanging token: {str(e)}")
#             return None
    
#     def get_accounts(self, access_token: str) -> List[Dict]:
#         """
#         Get all accounts associated with an access token
        
#         Args:
#             access_token: Plaid access token
            
#         Returns:
#             List of account dictionaries
#         """
#         try:
#             request = AccountsGetRequest(access_token=access_token)
#             response = self.client.accounts_get(request)
#             data = response.to_dict()
            
#             accounts = []
#             for account in data.get("accounts", []):
#                 accounts.append({
#                     "account_id": account["account_id"],
#                     "name": account["name"],
#                     "type": account["type"],
#                     "subtype": account.get("subtype"),
#                     "mask": account.get("mask"),
#                     "current_balance": account["balances"].get("current"),
#                     "available_balance": account["balances"].get("available"),
#                     "limit": account["balances"].get("limit"),
#                     "currency": account["balances"].get("iso_currency_code", "USD"),
#                     "official_name": account.get("official_name"),
#                     "verification_status": account.get("verification_status")
#                 })
            
#             return accounts
            
#         except Exception as e:
#             st.error(f"Error fetching accounts: {str(e)}")
#             return []
    
#     def sync_transactions(self, access_token: str, cursor: Optional[str] = None) -> Dict:
#         """
#         Sync transactions from Plaid
        
#         Args:
#             access_token: Plaid access token
#             cursor: Optional cursor for pagination
            
#         Returns:
#             Dict with transactions and pagination info
#         """
#         try:
#             all_transactions = []
#             has_more = True
#             next_cursor = cursor
            
#             while has_more:
#                 if next_cursor:
#                     request = TransactionsSyncRequest(
#                         access_token=access_token,
#                         cursor=next_cursor
#                     )
#                 else:
#                     request = TransactionsSyncRequest(access_token=access_token)
                
#                 response = self.client.transactions_sync(request)
#                 data = response.to_dict()
                
#                 # Add new transactions
#                 all_transactions.extend(data.get("added", []))
                
#                 # Check for more pages
#                 has_more = data.get("has_more", False)
#                 next_cursor = data.get("next_cursor")
                
#                 # Limit to prevent infinite loops
#                 if len(all_transactions) > 1000:
#                     break
            
#             # Process transactions
#             processed = []
#             for txn in all_transactions:
#                 processed.append({
#                     "transaction_id": txn.get("transaction_id"),
#                     "account_id": txn.get("account_id"),
#                     "amount": txn.get("amount"),
#                     "date": str(txn.get("date")),
#                     "authorized_date": str(txn.get("authorized_date")) if txn.get("authorized_date") else None,
#                     "name": txn.get("name"),
#                     "merchant_name": txn.get("merchant_name"),
#                     "merchant_entity_id": txn.get("merchant_entity_id"),
#                     "logo_url": txn.get("logo_url"),
#                     "website": txn.get("website"),
#                     "category": txn.get("category"),
#                     "category_id": txn.get("category_id"),
#                     "personal_finance_category": txn.get("personal_finance_category"),
#                     "location": txn.get("location"),
#                     "payment_channel": txn.get("payment_channel"),
#                     "pending": txn.get("pending", False),
#                     "transaction_type": txn.get("transaction_type"),
#                     "account_owner": txn.get("account_owner"),
#                     "transaction_code": txn.get("transaction_code")
#                 })
            
#             return {
#                 "transactions": processed,
#                 "cursor": next_cursor,
#                 "has_more": False,  # We fetched all in the loop
#                 "total_transactions": len(processed)
#             }
            
#         except Exception as e:
#             st.error(f"Error syncing transactions: {str(e)}")
#             return {
#                 "transactions": [],
#                 "cursor": None,
#                 "has_more": False,
#                 "total_transactions": 0,
#                 "error": str(e)
#             }
    
#     def get_item_info(self, access_token: str) -> Optional[Dict]:
#         """
#         Get information about the Item (bank connection)
        
#         Args:
#             access_token: Plaid access token
            
#         Returns:
#             Dict with item information or None if error
#         """
#         try:
#             from plaid.model.item_get_request import ItemGetRequest
            
#             request = ItemGetRequest(access_token=access_token)
#             response = self.client.item_get(request)
#             data = response.to_dict()
            
#             item = data.get("item", {})
#             return {
#                 "item_id": item.get("item_id"),
#                 "institution_id": item.get("institution_id"),
#                 "webhook": item.get("webhook"),
#                 "error": item.get("error"),
#                 "available_products": item.get("available_products"),
#                 "billed_products": item.get("billed_products"),
#                 "consent_expiration_time": item.get("consent_expiration_time"),
#                 "update_type": item.get("update_type")
#             }
            
#         except Exception as e:
#             st.error(f"Error getting item info: {str(e)}")
#             return None



# plaid_service.py
"""Plaid API integration service for Smart Expense Analyzer POC"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

from plaid.api_client import ApiClient
from plaid.configuration import Configuration, Environment
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_get_request import LinkTokenGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_get_request import AccountsGetRequest

from src.config import Config

class PlaidService:
    """Service for handling all Plaid API operations"""
    
    def __init__(self):
        """Initialize Plaid client with configuration"""
        configuration = Configuration(
            host=Environment.Sandbox,
            api_key={
                "clientId": Config.PLAID_CLIENT_ID,
                "secret": Config.PLAID_SECRET,
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def create_link_token(self, user_id: str, user_email: str) -> Optional[Dict]:
        """
        Create a Plaid Link token for bank connection
        
        Args:
            user_id: Unique user identifier
            user_email: User's email address
            
        Returns:
            Dict with link_token and hosted_link_url, or None if error
        """
        try:
            # Create Products and CountryCode objects
            products = [Products(p) for p in Config.PLAID_PRODUCTS]
            country_codes = [CountryCode(c) for c in Config.PLAID_COUNTRY_CODES]
            
            # Build the request
            link_token_request = LinkTokenCreateRequest(
                products=products,
                client_name=Config.APP_NAME[:30],  # Max 30 chars
                country_codes=country_codes,
                language="en",
                user=LinkTokenCreateRequestUser(
                    client_user_id=user_id,
                    email_address=user_email,
                ),
            )
            
            # Enable Hosted Link
            link_token_request['hosted_link'] = {}
            
            # Create the link token
            response = self.client.link_token_create(link_token_request)
            data = response.to_dict()
            
            return {
                "link_token": data["link_token"],
                "hosted_link_url": data.get("hosted_link_url"),
                "expiration": data.get("expiration")
            }
            
        except Exception as e:
            st.error(f"Error creating link token: {str(e)}")
            return None
    
    def get_link_token_status(self, link_token: str) -> Dict:
        """
        Check the status of a link token
        
        Args:
            link_token: The link token to check
            
        Returns:
            Dict with status and related information
        """
        try:
            request = LinkTokenGetRequest(link_token=link_token)
            response = self.client.link_token_get(request)
            data = response.to_dict()
            
            # Check if link session is complete
            link_sessions = data.get("link_sessions", [])
            if link_sessions:
                latest_session = link_sessions[-1]
                results = latest_session.get("results", {})
                item_add_results = results.get("item_add_results", [])
                
                if item_add_results:
                    return {
                        "status": "success",
                        "public_token": item_add_results[0].get("public_token"),
                        "accounts": item_add_results[0].get("accounts", []),
                        "institution": item_add_results[0].get("institution", {})
                    }
            
            return {
                "status": "pending",
                "created_at": data.get("created_at"),
                "expiration": data.get("expiration")
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def exchange_public_token(self, public_token: str) -> Optional[Dict]:
        """
        Exchange a public token for an access token
        
        Args:
            public_token: The public token from Plaid Link
            
        Returns:
            Dict with access_token and item_id, or None if error
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            data = response.to_dict()
            
            return {
                "access_token": data["access_token"],
                "item_id": data["item_id"]
            }
            
        except Exception as e:
            st.error(f"Error exchanging token: {str(e)}")
            return None
    
    def get_accounts(self, access_token: str) -> List[Dict]:
        """
        Get all accounts associated with an access token
        
        Args:
            access_token: Plaid access token
            
        Returns:
            List of account dictionaries
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            data = response.to_dict()
            
            accounts = []
            for account in data.get("accounts", []):
                accounts.append({
                    "account_id": account["account_id"],
                    "name": account["name"],
                    "type": account["type"],
                    "subtype": account.get("subtype"),
                    "mask": account.get("mask"),
                    "current_balance": account["balances"].get("current"),
                    "available_balance": account["balances"].get("available"),
                    "limit": account["balances"].get("limit"),
                    "currency": account["balances"].get("iso_currency_code", "USD"),
                    "official_name": account.get("official_name"),
                    "verification_status": account.get("verification_status")
                })
            
            return accounts
            
        except Exception as e:
            st.error(f"Error fetching accounts: {str(e)}")
            return []
    
    def sync_transactions(self, access_token: str, cursor: Optional[str] = None) -> Dict:
        """
        Sync transactions from Plaid
        
        Args:
            access_token: Plaid access token
            cursor: Optional cursor for pagination
            
        Returns:
            Dict with transactions and pagination info
        """
        try:
            all_transactions = []
            has_more = True
            next_cursor = cursor
            
            while has_more:
                if next_cursor:
                    request = TransactionsSyncRequest(
                        access_token=access_token,
                        cursor=next_cursor
                    )
                else:
                    request = TransactionsSyncRequest(access_token=access_token)
                
                response = self.client.transactions_sync(request)
                data = response.to_dict()
                
                # Add new transactions
                all_transactions.extend(data.get("added", []))
                
                # Check for more pages
                has_more = data.get("has_more", False)
                next_cursor = data.get("next_cursor")
                
                # Limit to prevent infinite loops
                if len(all_transactions) > 1000:
                    break
            
            # Process transactions
            processed = []
            for txn in all_transactions:
                processed.append({
                    "transaction_id": txn.get("transaction_id"),
                    "account_id": txn.get("account_id"),
                    "amount": txn.get("amount"),
                    "date": str(txn.get("date")),
                    "authorized_date": str(txn.get("authorized_date")) if txn.get("authorized_date") else None,
                    "name": txn.get("name"),
                    "merchant_name": txn.get("merchant_name"),
                    "merchant_entity_id": txn.get("merchant_entity_id"),
                    "logo_url": txn.get("logo_url"),
                    "website": txn.get("website"),
                    "category": txn.get("category"),
                    "category_id": txn.get("category_id"),
                    "personal_finance_category": txn.get("personal_finance_category"),
                    "location": txn.get("location"),
                    "payment_channel": txn.get("payment_channel"),
                    "pending": txn.get("pending", False),
                    "transaction_type": txn.get("transaction_type"),
                    "account_owner": txn.get("account_owner"),
                    "transaction_code": txn.get("transaction_code")
                })
            
            return {
                "transactions": processed,
                "cursor": next_cursor,
                "has_more": False,  # We fetched all in the loop
                "total_transactions": len(processed)
            }
            
        except Exception as e:
            st.error(f"Error syncing transactions: {str(e)}")
            return {
                "transactions": [],
                "cursor": None,
                "has_more": False,
                "total_transactions": 0,
                "error": str(e)
            }
    
    def get_item_info(self, access_token: str) -> Optional[Dict]:
        """
        Get information about the Item (bank connection)
        
        Args:
            access_token: Plaid access token
            
        Returns:
            Dict with item information or None if error
        """
        try:
            from plaid.model.item_get_request import ItemGetRequest
            
            request = ItemGetRequest(access_token=access_token)
            response = self.client.item_get(request)
            data = response.to_dict()
            
            item = data.get("item", {})
            return {
                "item_id": item.get("item_id"),
                "institution_id": item.get("institution_id"),
                "webhook": item.get("webhook"),
                "error": item.get("error"),
                "available_products": item.get("available_products"),
                "billed_products": item.get("billed_products"),
                "consent_expiration_time": item.get("consent_expiration_time"),
                "update_type": item.get("update_type")
            }
            
        except Exception as e:
            st.error(f"Error getting item info: {str(e)}")
            return None