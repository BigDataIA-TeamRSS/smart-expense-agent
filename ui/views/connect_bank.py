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
        if st.button("🔗 Generate Bank Connection Link", type="primary"):
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
            
            if st.button("✅ Check Connection Status", type="primary"):
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