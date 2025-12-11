import os
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid import ApiClient, Configuration
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

configuration = Configuration(
    host='https://sandbox.plaid.com',
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

client = plaid_api.PlaidApi(ApiClient(configuration))

# For sandbox testing, you need an access_token
# Get this by completing the Link flow first
# For now, this shows the structure

print("To get transactions, you need:")
print("1. Create Link Token")
print("2. User completes Plaid Link OAuth (in browser)")
print("3. Exchange public_token for access_token")
print("4. Use access_token to fetch transactions")
print("\nLet's build the Link flow in Streamlit next!")