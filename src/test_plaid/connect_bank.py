import os
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid import ApiClient, Configuration
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

# Step 1: Create Link Token
print("Creating link token...")
request = LinkTokenCreateRequest(
    products=[Products("transactions")],
    client_name="Smart Expense Analyzer",
    country_codes=[CountryCode('US')],
    language='en',
    user=LinkTokenCreateRequestUser(client_user_id='user_123')
)

response = client.link_token_create(request)
link_token = response['link_token']

print(f"✓ Link token: {link_token}")
print("\nNow you need to complete OAuth flow in browser...")
print("For testing, we'll use a public_token from sandbox")

# For sandbox testing, Plaid provides test tokens
# In real app, user would authenticate via Plaid Link UI
print("\nIn sandbox, you can use test public_token from Plaid docs")