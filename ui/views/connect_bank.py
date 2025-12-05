# """Connect Bank view for Smart Expense Analyzer"""

# import streamlit as st
# import streamlit.components.v1 as components
# from typing import Dict
# import time

# def show_connect_bank(db, plaid, current_user: Dict):
#     """Display the connect bank interface"""
    
#     st.header("🏦 Connect Your Bank")
    
#     user_id = current_user["user_id"]
    
#     # Check if already connected
#     existing_token = db.get_plaid_token(user_id)
    
#     if existing_token:
#         st.success("✅ Bank account already connected!")
        
#         if st.button("🔄 Reconnect Bank"):
#             st.session_state.pop('link_token', None)
#             st.rerun()
        
#         # Show sync button
#         st.markdown("---")
#         if st.button("🔄 Sync Transactions"):
#             with st.spinner("Syncing transactions..."):
#                 try:
#                     result = plaid.sync_transactions(existing_token)
                    
#                     # Save transactions
#                     if result['added']:
#                         db.save_transactions(user_id, result['added'])
#                         st.success(f"✅ Synced {len(result['added'])} transactions!")
#                     else:
#                         st.info("No new transactions to sync")
                    
#                     # Get and save accounts
#                     accounts = plaid.get_accounts(existing_token)
#                     db.save_accounts(user_id, accounts)
                    
#                 except Exception as e:
#                     st.error(f"Error syncing: {str(e)}")
        
#         return
    
#     # Create link token if not exists
#     if 'link_token' not in st.session_state:
#         try:
#             result = plaid.create_link_token(user_id)
#             st.session_state.link_token = result['link_token']
#         except Exception as e:
#             st.error(f"Error creating link token: {str(e)}")
#             return
    
#     # Display Plaid Link
#     st.markdown("""
#     ### Connect your bank account securely with Plaid
    
#     Click the button below to:
#     1. Search for your bank
#     2. Log in securely (credentials are encrypted)
#     3. Select accounts to link
#     """)
    
#     # Display link token for manual testing
#     st.info("🔗 Link Token Generated!")
    
#     # Show instructions for sandbox testing
#     st.markdown("""
#     ### 📱 For Plaid Sandbox Testing:
    
#     **Option 1: Use Plaid's Link Demo (Recommended)**
#     1. Go to: https://plaid.com/docs/link/
#     2. Click "Try Link" 
#     3. Use credentials: `user_good` / `pass_good`
#     4. Copy the public_token from the response
#     5. Paste it below
    
#     **Option 2: Use Your Link Token Directly**
#     - Copy your link token below and use it with Plaid's testing tools
#     """)
    
#     # Show the link token
#     with st.expander("🔑 Your Link Token (for testing)"):
#         st.code(st.session_state.link_token)
#         st.caption("This token expires soon. Use it quickly!")
    
#     st.markdown("---")
    
#     # Manual token exchange section
#     st.markdown("### 🔗 Paste Your Public Token")
#     st.markdown("After completing Plaid Link flow, paste the `public_token` here:")
    
#     public_token = st.text_input(
#         "Public Token:", 
#         placeholder="public-sandbox-xxxxx...",
#         key="public_token_input"
#     )
    
#     col1, col2 = st.columns([1, 3])
#     with col1:
#         exchange_btn = st.button("🔄 Connect Bank", type="primary", use_container_width=True)
    
#     if exchange_btn:
#         if public_token:
#             try:
#                 with st.spinner("Connecting to your bank..."):
#                     # Exchange public token for access token
#                     result = plaid.exchange_public_token(public_token)
#                     access_token = result['access_token']
#                     item_id = result['item_id']
                    
#                     # Save to database
#                     db.save_plaid_token(user_id, access_token, item_id)
                    
#                     # Fetch accounts
#                     st.info("📊 Fetching accounts...")
#                     accounts = plaid.get_accounts(access_token)
#                     db.save_accounts(user_id, accounts)
                    
#                     # Sync transactions
#                     st.info("💸 Syncing transactions...")
#                     transactions_result = plaid.sync_transactions(access_token)
#                     if transactions_result['added']:
#                         db.save_transactions(user_id, transactions_result['added'])
#                         st.success(f"✅ Synced {len(transactions_result['added'])} transactions!")
                    
#                     st.success("🎉 Bank connected successfully!")
#                     st.balloons()
                    
#                     # Wait a moment then reload
#                     time.sleep(1)
#                     st.rerun()
                    
#             except Exception as e:
#                 st.error(f"❌ Connection failed: {str(e)}")
#                 st.caption("Make sure you're using a valid Plaid public token from sandbox")
#         else:
#             st.warning("⚠️ Please enter a public token first")
    
#     # Quick test option
#     st.markdown("---")
#     st.markdown("### 🧪 Quick Test Mode")
    
#     if st.button("📝 Use Sample Data (No Plaid Required)"):
#         st.info("This would load sample transaction data for testing")
#         st.caption("Feature coming soon!")


# pages/connect_bank.py
"""Bank connection page for Smart Expense Analyzer POC"""

import streamlit as st
from typing import Dict

def show_connect_bank(db, plaid_service, current_user: Dict):
    """Show the bank connection page"""
    st.header("Connect Your Bank Account")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("""
        **🔐 Secure Bank Connection Steps:**
        1. Click 'Generate Link' below
        2. Open the secure Plaid portal
        3. Use these sandbox test credentials:
           - Username: `user_good`
           - Password: `pass_good`
        4. Select your bank and accounts
        5. Return here and click 'Check Status'
        """)
        
        # Generate Link button
        if st.button("🔗 Generate Bank Connection Link", type="primary", use_container_width=True):
            with st.spinner("Creating secure link..."):
                result = plaid_service.create_link_token(
                    current_user["id"],
                    current_user["email"]
                )
                
                if result:
                    st.session_state.link_token = result["link_token"]
                    st.session_state.hosted_link_url = result["hosted_link_url"]
                    
                    st.success("✅ Link generated successfully!")
                    st.markdown("### 🏦 Connect Your Bank")
                    st.markdown(f"""
                    **Step 1:** Click the link below to open Plaid in a new tab:
                    
                    [{result['hosted_link_url']}]({result['hosted_link_url']})
                    """)
                    
                    # Also show as code for easy copying
                    st.code(result['hosted_link_url'])
                    
                    st.markdown("""
                    **Step 2:** Complete the bank connection in the new tab
                    
                    **Step 3:** Return here and click 'Check Connection Status'
                    """)
                else:
                    st.error("Failed to generate link. Please try again.")
        
        # Check status section
        if 'link_token' in st.session_state:
            st.markdown("---")
            
            if st.button("✅ Check Connection Status", type="primary", use_container_width=True):
                with st.spinner("Checking connection status..."):
                    status = plaid_service.get_link_token_status(st.session_state.link_token)
                    
                    if status["status"] == "success":
                        handle_successful_connection(
                            db, plaid_service, current_user, status
                        )
                    elif status["status"] == "pending":
                        st.warning("⏳ Connection pending. Please complete the process in Plaid Link.")
                        st.info("If you've completed it, wait a moment and try checking again.")
                    else:
                        st.error(f"❌ Error: {status.get('message', 'Unknown error')}")
    
    with col2:
        # Information panel
        st.markdown("### ℹ️ Quick Info")
        
        with st.expander("Supported Banks", expanded=False):
            st.markdown("""
            - Chase
            - Bank of America
            - Wells Fargo
            - Citi
            - Capital One
            - US Bank
            - PNC
            - TD Bank
            - And 12,000+ more...
            """)
        
        with st.expander("What We Access", expanded=False):
            st.markdown("""
            **Account Info:**
            - Account names & types
            - Current balances
            - Available funds
            
            **Transactions:**
            - Transaction history
            - Merchant names
            - Categories
            - Amounts & dates
            
            **We Never See:**
            - Your login credentials
            - Full account numbers
            - Personal information
            """)
        
        with st.expander("Security", expanded=False):
            st.markdown("""
            🔒 **Bank-Level Security**
            - 256-bit encryption
            - Read-only access
            - OAuth 2.0 authentication
            - No password storage
            
            ✅ **Plaid is trusted by:**
            - Venmo
            - Robinhood
            - Coinbase
            - And thousands more
            """)

def handle_successful_connection(db, plaid_service, current_user: Dict, status: Dict):
    """Handle a successful bank connection"""
    st.success("🎉 Bank connection successful!")
    
    # Exchange public token for access token
    with st.spinner("Securing your connection..."):
        exchange_result = plaid_service.exchange_public_token(status["public_token"])
        
        if not exchange_result:
            st.error("Failed to complete connection. Please try again.")
            return
    
    # Get account details
    with st.spinner("Fetching account information..."):
        accounts = plaid_service.get_accounts(exchange_result["access_token"])
        
        if not accounts:
            st.error("No accounts found. Please try again.")
            return
    
    # Save accounts to database
    saved_accounts = []
    for account in accounts:
        account["access_token"] = exchange_result["access_token"]
        account["item_id"] = exchange_result["item_id"]
        account["institution_name"] = status["institution"].get("name", "Unknown Bank")
        account["institution_id"] = status["institution"].get("institution_id", "")
        
        saved_account = db.save_bank_account(current_user["id"], account)
        saved_accounts.append(saved_account)
    
    st.success(f"✅ Connected {len(saved_accounts)} accounts successfully!")
    
    # Display connected accounts
    st.markdown("### Connected Accounts:")
    for account in accounts:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**{account['name']}**")
        with col2:
            st.metric("Type", account['type'].title())
        with col3:
            if account.get('mask'):
                st.metric("Account", f"****{account['mask']}")
    
    # Sync transactions
    with st.spinner("Syncing transactions... This may take a moment..."):
        sync_result = plaid_service.sync_transactions(exchange_result["access_token"])
        
        if sync_result["transactions"]:
            # Save transactions for each account
            transactions_by_account = {}
            for txn in sync_result["transactions"]:
                account_id = txn["account_id"]
                if account_id not in transactions_by_account:
                    transactions_by_account[account_id] = []
                transactions_by_account[account_id].append(txn)
            
            total_saved = 0
            for account_id, txns in transactions_by_account.items():
                saved_count = db.save_transactions(current_user["id"], account_id, txns)
                total_saved += saved_count
            
            st.success(f"✅ Synced {total_saved} new transactions!")
            
            # Show summary
            if total_saved > 0:
                st.balloons()
                st.markdown("### 🎊 Setup Complete!")
                st.markdown("""
                You can now:
                - View your account balances in **Accounts** tab
                - Browse transactions in **Transactions** tab
                - See spending analytics in **Analytics** tab
                - Check your dashboard for an overview
                """)
        else:
            st.info("No transactions found. This is normal for new accounts.")
    
    # Clear session state
    if 'link_token' in st.session_state:
        del st.session_state.link_token
    if 'hosted_link_url' in st.session_state:
        del st.session_state.hosted_link_url