import os
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid import ApiClient, Configuration
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

configuration = Configuration(
    host='https://sandbox.plaid.com',
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

client = plaid_api.PlaidApi(ApiClient(configuration))

def exchange_public_token(public_token: str):
    """Exchange public_token for access_token"""
    request = ItemPublicTokenExchangeRequest(public_token=public_token)
    response = client.item_public_token_exchange(request)
    
    access_token = response['access_token']
    item_id = response['item_id']
    
    return access_token, item_id

def get_transactions(access_token: str, start_date: str, end_date: str):
    """Fetch transactions using access_token"""
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date()
    )
    
    response = client.transactions_get(request)
    transactions = response['transactions']
    
    return transactions