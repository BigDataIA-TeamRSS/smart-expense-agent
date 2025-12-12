"""Transactions page for Smart Expense Analyzer POC"""
import streamlit as st
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client

def _fetch_accounts(user_id: str):
    """Fetch accounts from API"""
    api = get_api_client()
    print("[TRANSACTIONS] Calling API: /api/accounts")
    accounts = api.get_accounts()
    print(f"[TRANSACTIONS] Received {len(accounts)} accounts")
    return accounts

def _fetch_transactions(user_id: str, account_id: str = None, search: str = None, 
                       min_amount: float = None, max_amount: float = None, limit: int = 1000):
    """Fetch transactions from API"""
    api = get_api_client()
    print(f"[TRANSACTIONS] Calling API: /api/transactions with filters")
    transactions = api.get_transactions(
        account_id=account_id,
        search=search if search else None,
        min_amount=min_amount if min_amount and min_amount > 0 else None,
        max_amount=max_amount if max_amount and max_amount < 10000 else None,
        limit=limit
    )
    print(f"[TRANSACTIONS] Received {len(transactions)} transactions from API")
    return transactions

def _fetch_transaction_summary(user_id: str, account_id: str = None):
    """Fetch transaction summary from API"""
    api = get_api_client()
    print("[TRANSACTIONS] Calling API: /api/transactions/summary")
    try:
        summary = api.get_transaction_summary(account_id=account_id)
        print(f"[TRANSACTIONS] Summary: {summary}")
        return summary
    except Exception as e:
        print(f"[TRANSACTIONS] Error getting summary: {str(e)}")
        return None

def show_transactions(current_user: Dict):
    """Show the transactions page"""
    user_id = current_user.get('id')
    accounts_cache_key = f"transactions_accounts_{user_id}"
    
    print(f"[TRANSACTIONS] Loading transactions for user: {user_id}")
    
    # Skip API calls if we're in a file upload operation
    if st.session_state.get('skip_api_calls', False):
        print("[TRANSACTIONS] Skipping API call (file operation in progress)")
        if accounts_cache_key in st.session_state and st.session_state[accounts_cache_key]:
            accounts = st.session_state[accounts_cache_key]
        else:
            st.info("Loading...")
            return
    
    st.header("Transaction History")
    
    # Manual refresh button
    col1, col2 = st.columns([1, 10])
    with col1:
        refresh_key = f"refresh_transactions_{user_id}"
        if st.button("🔄", help="Refresh transactions", key="refresh_txns"):
            st.session_state[refresh_key] = True
    
    try:
        # Check if we need to fetch accounts (no data or refresh requested)
        refresh_requested = st.session_state.get(f"refresh_transactions_{user_id}", False)
        
        if accounts_cache_key not in st.session_state or st.session_state[accounts_cache_key] is None or refresh_requested:
            # Fetch from API
            accounts = _fetch_accounts(user_id)
            st.session_state[accounts_cache_key] = accounts
        else:
            # Use cached data from session state
            accounts = st.session_state[accounts_cache_key]
            print("[TRANSACTIONS] Using cached accounts from session state")
        
        if not accounts:
            st.info("No accounts connected yet.")
            st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
            return
        
        # Account selector
        account_options = ["All Accounts"] + [
            f"{acc['institution_name']} - {acc['name']}" for acc in accounts
        ]
        
        selected_option = st.selectbox("Select Account", account_options)
        
        # Determine account_id for API call
        selected_account_id = None
        if selected_option != "All Accounts":
            selected_index = account_options.index(selected_option) - 1
            selected_account = accounts[selected_index]
            selected_account_id = selected_account.get("account_id")
            print(f"[TRANSACTIONS] Selected account ID: {selected_account_id}")
        
        # Filters
        st.markdown("### 🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_term = st.text_input("Search transactions", "")
        
        with col2:
            min_amount = st.number_input("Min amount ($)", value=0.0, step=1.0)
        
        with col3:
            max_amount = st.number_input("Max amount ($)", value=10000.0, step=1.0)
        
        # Build cache key for transactions based on filters
        txns_cache_key = f"transactions_{user_id}_{selected_account_id}_{search_term}_{min_amount}_{max_amount}"
        
        # Get transactions (use cache if available, otherwise fetch)
        if txns_cache_key not in st.session_state or refresh_requested:
            transactions = _fetch_transactions(
                user_id,
                account_id=selected_account_id,
                search=search_term if search_term else None,
                min_amount=min_amount if min_amount > 0 else None,
                max_amount=max_amount if max_amount < 10000 else None,
                limit=1000
            )
            st.session_state[txns_cache_key] = transactions
        else:
            transactions = st.session_state[txns_cache_key]
            print("[TRANSACTIONS] Using cached transactions from session state")
        
        if not transactions:
            st.info("No transactions found for the selected account.")
            return
        
        # Get summary
        summary_cache_key = f"transaction_summary_{user_id}_{selected_account_id}"
        if summary_cache_key not in st.session_state or refresh_requested:
            summary = _fetch_transaction_summary(user_id, account_id=selected_account_id)
            st.session_state[summary_cache_key] = summary
        else:
            summary = st.session_state[summary_cache_key]
            print("[TRANSACTIONS] Using cached summary from session state")
        
        # Clear refresh flag
        if refresh_requested:
            st.session_state[f"refresh_transactions_{user_id}"] = False
        
        # Summary
        st.markdown("---")
        st.markdown(f"### 📊 Summary - Showing {len(transactions)} transactions")
        
        col1, col2, col3 = st.columns(3)
        
        if summary:
            total_spent = summary.get("total_expenses", 0)
            total_received = summary.get("total_income", 0)
            net = summary.get("net_amount", 0)
        else:
            # Calculate locally if API summary fails
            total_spent = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)
            total_received = sum(abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) < 0)
            net = total_received - total_spent
        
        with col1:
            st.metric("Total Spent", f"${total_spent:,.2f}")
        with col2:
            st.metric("Total Received", f"${total_received:,.2f}")
        with col3:
            st.metric("Net", f"${net:,.2f}")
        
        st.markdown("---")
        
        # Transaction list
        st.markdown("### 📋 Transactions")
        
        # Display options
        show_categories = st.checkbox("Show categories", value=True)
        
        # Display transactions
        print(f"[TRANSACTIONS] Displaying {min(len(transactions), 100)} transactions")
        for i, txn in enumerate(transactions[:100]):  # Limit to 100 for performance
            display_transaction(txn, show_categories)
            
            if i < len(transactions) - 1:
                st.markdown("---")
        
        if len(transactions) > 100:
            st.info(f"Showing first 100 transactions. Total: {len(transactions)}")
        
        print("[TRANSACTIONS] Transactions page loaded successfully")
        
    except Exception as e:
        print(f"[TRANSACTIONS] Error loading transactions: {str(e)}")
        st.error(f"Error loading transactions: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_transaction(txn: Dict, show_categories: bool = True):
    """Display a single transaction"""
    col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
    
    with col1:
        merchant = txn.get("merchant_name") or txn.get("name", "Unknown")
        st.markdown(f"**{merchant}**")
        
        if show_categories and txn.get("category"):
            category = txn["category"]
            if isinstance(category, list):
                category_str = " > ".join(category[:2])
            else:
                category_str = str(category)
            st.caption(f"📁 {category_str}")
    
    with col2:
        amount = txn.get("amount", 0)
        if amount > 0:
            st.markdown(f"<span style='color:#ff4b4b;font-weight:bold'>-${amount:.2f}</span>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#00cc88;font-weight:bold'>+${abs(amount):.2f}</span>", 
                       unsafe_allow_html=True)
    
    with col3:
        date_str = txn.get("date", "")
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                st.text(date_obj.strftime("%b %d, %Y"))
            except:
                st.text(date_str)
    
    with col4:
        if txn.get("pending"):
            st.warning("⏳ Pending")
        else:
            st.success("✓ Cleared")
