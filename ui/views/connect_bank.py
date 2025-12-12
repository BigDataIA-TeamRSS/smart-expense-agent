# pages/connect_bank.py
"""Bank connection page for Smart Expense Analyzer POC"""
import streamlit as st
from typing import Dict
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client

def show_connect_bank(current_user: Dict):
    """Show the bank connection page"""
    print(f"[CONNECT_BANK] Loading connect bank page for user: {current_user.get('id')}")
    
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
            print("[CONNECT_BANK] Generate link button clicked")
            with st.spinner("Creating secure link..."):
                try:
                    api = get_api_client()
                    print("[CONNECT_BANK] Calling API: /api/plaid/link-token")
                    result = api.create_link_token()
                    print(f"[CONNECT_BANK] Link token created: {result.get('link_token')[:20]}...")
                    
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
                except Exception as e:
                    print(f"[CONNECT_BANK] Error creating link token: {str(e)}")
                    st.error(f"Failed to generate link: {str(e)}")
        
        # Check status section
        if 'link_token' in st.session_state:
            st.markdown("---")
            
            if st.button("✅ Check Connection Status", type="primary", use_container_width=True):
                print("[CONNECT_BANK] Check status button clicked")
                with st.spinner("Checking connection status..."):
                    try:
                        api = get_api_client()
                        print(f"[CONNECT_BANK] Calling API: /api/plaid/link-status with token: {st.session_state.link_token[:20]}...")
                        status = api.get_link_status(st.session_state.link_token)
                        print(f"[CONNECT_BANK] Link status: {status.get('status')}")
                        
                        if status["status"] == "success":
                            print("[CONNECT_BANK] Connection successful, handling...")
                            handle_successful_connection(api, current_user, status)
                        elif status["status"] == "pending":
                            st.warning("⏳ Connection pending. Please complete the process in Plaid Link.")
                            st.info("If you've completed it, wait a moment and try checking again.")
                        else:
                            st.error(f"❌ Error: {status.get('message', 'Unknown error')}")
                    except Exception as e:
                        print(f"[CONNECT_BANK] Error checking status: {str(e)}")
                        st.error(f"Error checking connection status: {str(e)}")
    
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

def handle_successful_connection(api, current_user: Dict, status: Dict):
    """Handle a successful bank connection"""
    print(f"[CONNECT_BANK] Handling successful connection, public_token: {status.get('public_token')[:20]}...")
    st.success("🎉 Bank connection successful!")
    
    # Exchange public token for access token via API
    with st.spinner("Securing your connection..."):
        try:
            print("[CONNECT_BANK] Calling API: /api/plaid/exchange-token")
            exchange_result = api.exchange_public_token(status["public_token"])
            print(f"[CONNECT_BANK] Exchange successful, accounts: {len(exchange_result.get('accounts', []))}")
            print(f"[CONNECT_BANK] Transactions saved: {exchange_result.get('transactions_saved', 0)}")
            
            saved_accounts = exchange_result.get("accounts", [])
            
            st.success(f"✅ Connected {len(saved_accounts)} accounts successfully!")
            
            # Display connected accounts
            st.markdown("### Connected Accounts:")
            for account in saved_accounts:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**{account.get('name', 'Unknown')}**")
                with col2:
                    st.metric("Type", account.get('type', 'Unknown').title())
                with col3:
                    if account.get('mask'):
                        st.metric("Account", f"****{account['mask']}")
            
            # Show transaction sync results
            transactions_saved = exchange_result.get("transactions_saved", 0)
            if transactions_saved > 0:
                st.success(f"✅ Synced {transactions_saved} new transactions!")
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
            
            print("[CONNECT_BANK] Connection handling complete")
            
        except Exception as e:
            print(f"[CONNECT_BANK] Error handling connection: {str(e)}")
            st.error(f"Failed to complete connection: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
