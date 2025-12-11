import os
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid import ApiClient, Configuration
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

# You need access_token from previous step
# For testing, manually paste it here after connecting
ACCESS_TOKEN = "access-sandbox-xxxxx-xxxxxx"  # Replace with your token

print("Fetching transactions from Plaid Sandbox...")

try:
    # Use transactions/sync endpoint (newer, better)
    request = TransactionsSyncRequest(
        access_token=ACCESS_TOKEN
    )
    
    response = client.transactions_sync(request)
    
    added = response['added']
    print(f"\n✓ Fetched {len(added)} transactions\n")
    
    # Display first 10
    for i, txn in enumerate(added[:10], 1):
        print(f"{i}. {txn['date']} | {txn['name']:30} | ${txn['amount']:>8.2f}")
    
    # Save to JSON file
    with open('data/plaid_sample_transactions.json', 'w') as f:
        json.dump(added, f, indent=2, default=str)
    
    print(f"\n✓ Saved to data/plaid_sample_transactions.json")
    
except Exception as e:
    print(f"Error: {e}")