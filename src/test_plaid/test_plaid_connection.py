import os
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid import ApiClient, Configuration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Plaid client
configuration = Configuration(
    host='https://sandbox.plaid.com',  # Sandbox environment
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

print("Testing Plaid connection...")

# Test: Create Link Token
try:
    request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Smart Expense Analyzer",
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(
            client_user_id='test_user_123'
        )
    )
    
    response = client.link_token_create(request)
    link_token = response['link_token']
    
    print("✓ Plaid connection successful!")
    print(f"✓ Link token created: {link_token[:20]}...")
    print("\nYou're ready to connect to banks!")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")