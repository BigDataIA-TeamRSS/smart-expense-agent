"""Dashboard view for Smart Expense Analyzer"""

import streamlit as st
from typing import Dict

def show_dashboard(db, current_user: Dict):
    """Display the main dashboard"""
    
    st.header("📊 Dashboard")
    
    user_id = current_user["id"]
    
    # Get user data
    transactions = db.get_all_user_transactions(user_id)
    accounts = db.get_user_accounts(user_id)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Accounts", len(accounts))
    
    with col2:
        st.metric("Total Transactions", len(transactions))
    
    with col3:
        total_balance = sum(
            acc.get("balances", {}).get("current", 0) 
            for acc in accounts
        )
        st.metric("Total Balance", f"${total_balance:,.2f}")
    
    # Recent activity
    if transactions:
        st.subheader("Recent Transactions")
        recent = sorted(transactions, key=lambda x: x.get("date", ""), reverse=True)[:10]
        
        for txn in recent:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{txn.get('name', 'Unknown')}**")
            with col2:
                st.write(txn.get('date', 'N/A'))
            with col3:
                amount = txn.get('amount', 0)
                st.write(f"${abs(amount):.2f}")
    else:
        st.info("No transactions yet. Connect your bank account to get started!")

