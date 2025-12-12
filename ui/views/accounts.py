# pages/accounts.py
"""Accounts page for Smart Expense Analyzer POC"""
import streamlit as st
from typing import Dict
from datetime import datetime
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client
api = get_api_client()

def _fetch_accounts(user_id: str):
    """Fetch accounts from API"""
    print("[ACCOUNTS] Calling API: /api/accounts")
    accounts = api.get_accounts()
    print(f"[ACCOUNTS] Received {len(accounts)} accounts")
    return accounts

def show_accounts(current_user: Dict):
    """Show the accounts page with refresh functionality"""
    import time
    user_id = current_user.get('id')
    cache_key = f"accounts_data_{user_id}"
    page_start = time.time()
    print(f"[ACCOUNTS] Loading accounts for user: {user_id} at {page_start}")
    
    # Skip API calls if we're in a file upload operation
    if st.session_state.get('skip_api_calls', False):
        print("[ACCOUNTS] Skipping API call (file operation in progress)")
        if cache_key in st.session_state and st.session_state[cache_key]:
            accounts = st.session_state[cache_key]
        else:
            st.info("Loading...")
            return
    
    st.header("Your Bank Accounts")
    
    # Manual refresh button
    col1, col2 = st.columns([1, 10])
    with col1:
        refresh_key = f"refresh_{cache_key}"
        if st.button("🔄", help="Refresh accounts", key="refresh_accounts_top"):
            st.session_state[refresh_key] = True
    
    try:
        # Check if we need to fetch (no data or refresh requested)
        refresh_requested = st.session_state.get(f"refresh_{cache_key}", False)
        
        if cache_key not in st.session_state or st.session_state[cache_key] is None or refresh_requested:
            # Fetch from API
            api_start = time.time()
            accounts = _fetch_accounts(user_id)
            api_time = time.time() - api_start
            st.session_state[cache_key] = accounts
            st.session_state[f"refresh_{cache_key}"] = False
            print(f"[ACCOUNTS] Received {len(accounts)} accounts in {api_time:.2f}s")
        else:
            # Use cached data from session state
            accounts = st.session_state[cache_key]
            print(f"[ACCOUNTS] Using cached data from session state: {len(accounts)} accounts")
        
        if not accounts:
            st.info("No accounts connected yet.")
            st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
            return
        
        # Add a "Refresh All" button at the top
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔄 Refresh All Accounts", type="primary"):
                print("[ACCOUNTS] Refresh all accounts button clicked")
                st.session_state[f"refresh_{cache_key}"] = True  # Mark for refresh
                # Only refresh Plaid-connected accounts
                refresh_all_accounts(api, current_user)
        
        # Summary metrics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        total_balance = sum(acc.get('current_balance', 0) or 0 for acc in accounts)
        total_available = sum(acc.get('available_balance', 0) or 0 for acc in accounts)
        
        with col1:
            st.metric("Total Accounts", len(accounts))
        with col2:
            st.metric("Total Balance", f"${total_balance:,.2f}")
        with col3:
            st.metric("Total Available", f"${total_available:,.2f}")
        
        st.markdown("---")
        
        # Display each account
        for account in accounts:
            with st.expander(f"{account['institution_name']} - {account['name']}", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    balance = account.get('current_balance', 0)
                    st.metric(
                        "Current Balance",
                        f"${balance:,.2f}" if balance is not None else "N/A"
                    )
                
                with col2:
                    available = account.get('available_balance', 0)
                    st.metric(
                        "Available",
                        f"${available:,.2f}" if available is not None else "N/A"
                    )
                
                with col3:
                    st.metric("Type", account.get('type', 'Unknown').title())
                
                with col4:
                    st.metric("Account", f"****{account.get('mask', '????')}")
                
                # Additional details
                col1, col2 = st.columns(2)
                
                with col1:
                    if account.get('subtype'):
                        st.write(f"**Subtype:** {account['subtype'].title()}")
                    if account.get('official_name'):
                        st.write(f"**Official Name:** {account['official_name']}")
                
                with col2:
                    if account.get('currency'):
                        st.write(f"**Currency:** {account['currency']}")
                    if account.get('limit'):
                        st.write(f"**Credit Limit:** ${account['limit']:,.2f}")
                
                # Show last sync time
                if account.get('last_synced'):
                    try:
                        last_sync = datetime.fromisoformat(account['last_synced'])
                        time_ago = datetime.now() - last_sync
                        if time_ago.days > 0:
                            sync_text = f"{time_ago.days} days ago"
                        elif time_ago.seconds > 3600:
                            sync_text = f"{time_ago.seconds // 3600} hours ago"
                        else:
                            sync_text = f"{time_ago.seconds // 60} minutes ago"
                        st.caption(f"Last synced: {sync_text}")
                    except:
                        pass
                
                # Account actions
                col1, col2, col3 = st.columns(3)
                
                # Check if this is a Plaid account or PDF account
                account_source = account.get('source', 'plaid')
                is_plaid_account = account_source == 'plaid' and account.get('access_token')
                
                with col1:
                    # Lazy load transaction count - only fetch if user clicks
                    # This avoids making 16 API calls on page load
                    if st.button("📊 Get Count", key=f"count_{account['id']}"):
                        print(f"[ACCOUNTS] Getting transaction count for account: {account.get('account_id')}")
                        import time
                        start = time.time()
                        try:
                            txns = api.get_transactions(account_id=account.get("account_id"), limit=1000)
                            txn_count = len(txns)
                            elapsed = time.time() - start
                            print(f"[ACCOUNTS] Got {txn_count} transactions in {elapsed:.2f}s")
                            st.info(f"📊 {txn_count} transactions")
                        except Exception as e:
                            print(f"[ACCOUNTS] Error getting transaction count: {str(e)}")
                            st.error(f"Error: {str(e)}")
                    else:
                        st.info("📊 Click to get count")
                
                with col2:
                    # Only show refresh button for Plaid-connected accounts
                    if is_plaid_account:
                        if st.button("🔄 Refresh", key=f"refresh_{account['id']}"):
                            print(f"[ACCOUNTS] Refresh button clicked for account: {account.get('id')}")
                            st.session_state[f"refresh_{cache_key}"] = True  # Mark for refresh
                            refresh_single_account(api, current_user, account)
                    else:
                        # PDF-uploaded account - can't refresh via Plaid
                        st.caption("📄 PDF Account")
                        st.info("Uploaded via PDF")
                
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_{account['id']}"):
                        print(f"[ACCOUNTS] Delete button clicked for account: {account.get('id')}")
                        try:
                            api.delete_account(account["id"])
                            print(f"[ACCOUNTS] Account deleted successfully")
                            st.session_state[f"refresh_{cache_key}"] = True  # Mark for refresh
                            st.success("Account removed - refresh to see changes")
                        except Exception as e:
                            print(f"[ACCOUNTS] Error deleting account: {str(e)}")
                            st.error(f"Error deleting account: {str(e)}")
        
        page_time = time.time() - page_start
        print(f"[ACCOUNTS] Accounts page loaded successfully in {page_time:.2f}s")
        
    except Exception as e:
        print(f"[ACCOUNTS] Error loading accounts: {str(e)}")
        st.error(f"Error loading accounts: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def refresh_single_account(api, current_user: Dict, account: Dict):
    """Refresh a single account's data"""
    print(f"[ACCOUNTS] Refreshing single account: {account.get('id')}")
    
    # Check if account can be refreshed
    account_source = account.get('source', 'plaid')
    if account_source != 'plaid' or not account.get('access_token'):
        st.warning("⚠️ This account was uploaded via PDF and cannot be refreshed via Plaid. Only Plaid-connected accounts can be refreshed.")
        return
    
    with st.spinner(f"Refreshing {account['name']}..."):
        try:
            print(f"[ACCOUNTS] Calling API: /api/accounts/{account['id']}/refresh")
            result = api.refresh_account(account["id"])
            print(f"[ACCOUNTS] Refresh result: {result.get('new_transactions', 0)} new transactions")
            
            if result.get('new_transactions', 0) > 0:
                st.success(f"✅ Refreshed! Found {result['new_transactions']} new transactions")
            else:
                st.info("✅ Account refreshed. No new transactions.")
            
            # Don't rerun - just show success message
            # st.rerun()  # Removed to avoid slow reload
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ACCOUNTS] Error refreshing account: {error_msg}")
            
            # Provide helpful error message
            if "not connected via Plaid" in error_msg or "PDF-uploaded" in error_msg:
                st.warning("⚠️ This account cannot be refreshed. PDF-uploaded accounts are not connected to Plaid.")
            elif "400" in error_msg:
                st.error(f"❌ Bad Request: {error_msg}")
            else:
                st.error(f"❌ Error refreshing account: {error_msg}")


def refresh_all_accounts(api, current_user: Dict):
    """Refresh all accounts at once"""
    print(f"[ACCOUNTS] Refreshing all accounts for user: {current_user.get('id')}")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        print("[ACCOUNTS] Calling API: /api/accounts/refresh-all")
        result = api.refresh_all_accounts()
        print(f"[ACCOUNTS] Refresh all result: {result.get('total_new_transactions', 0)} total new transactions")
        
        progress_bar.progress(1.0)
        status_text.empty()
        
        if result.get('total_new_transactions', 0) > 0:
            st.success(f"✅ All accounts refreshed! Found {result['total_new_transactions']} new transactions total")
        else:
            st.info("✅ All accounts refreshed. No new transactions found.")
        
        # Don't rerun - just show success message
        # st.rerun()  # Removed to avoid slow reload
        
    except Exception as e:
        print(f"[ACCOUNTS] Error refreshing all accounts: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        st.error(f"Error refreshing accounts: {str(e)}")
