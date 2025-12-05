# """Transactions view for Smart Expense Analyzer"""

# import streamlit as st
# import pandas as pd
# from typing import Dict
# from datetime import datetime

# def show_transactions(db, current_user: Dict):
#     """Display user transactions"""
    
#     st.header("💸 Transactions")
    
#     user_id = current_user["user_id"]
#     transactions = db.get_user_transactions(user_id)
    
#     if not transactions:
#         st.info("No transactions found. Sync your bank account to see transactions!")
#         return
    
#     # Filters
#     col1, col2 = st.columns(2)
#     with col1:
#         search = st.text_input("🔍 Search transactions", "")
#     with col2:
#         sort_order = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (High to Low)", "Amount (Low to High)"])
    
#     # Filter transactions
#     filtered_txns = transactions
#     if search:
#         filtered_txns = [
#             t for t in filtered_txns 
#             if search.lower() in t.get('merchant_name', t.get('name', '')).lower()
#         ]
    
#     # Sort transactions
#     if sort_order == "Date (Newest)":
#         filtered_txns = sorted(filtered_txns, key=lambda x: x.get('date', ''), reverse=True)
#     elif sort_order == "Date (Oldest)":
#         filtered_txns = sorted(filtered_txns, key=lambda x: x.get('date', ''))
#     elif sort_order == "Amount (High to Low)":
#         filtered_txns = sorted(filtered_txns, key=lambda x: abs(x.get('amount', 0)), reverse=True)
#     else:
#         filtered_txns = sorted(filtered_txns, key=lambda x: abs(x.get('amount', 0)))
    
#     # Show count
#     st.write(f"Showing {len(filtered_txns)} transactions")
    
#     # Display transactions
#     for txn in filtered_txns:
#         merchant = txn.get('merchant_name', txn.get('name', 'Unknown'))
#         amount = abs(txn.get('amount', 0))
#         date = txn.get('date', 'N/A')
#         category = txn.get('category', ['Other'])[0] if isinstance(txn.get('category'), list) else txn.get('category', 'Other')
        
#         with st.container():
#             col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
#             with col1:
#                 st.write(f"**{merchant}**")
#             with col2:
#                 st.write(date)
#             with col3:
#                 st.write(f"${amount:.2f}")
#             with col4:
#                 st.write(category)
#             st.markdown("---")


"""Transactions page for Smart Expense Analyzer POC"""

import streamlit as st
from typing import Dict, List
from datetime import datetime

def show_transactions(db, current_user: Dict):
    """Show the transactions page"""
    st.header("Transaction History")
    
    accounts = db.get_user_accounts(current_user["id"])
    
    if not accounts:
        st.info("No accounts connected yet.")
        st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
        return
    
    # Account selector
    account_options = ["All Accounts"] + [
        f"{acc['institution_name']} - {acc['name']}" for acc in accounts
    ]
    
    selected_option = st.selectbox("Select Account", account_options)
    
    # Get transactions
    if selected_option == "All Accounts":
        transactions = db.get_all_user_transactions(current_user["id"])
    else:
        selected_index = account_options.index(selected_option) - 1
        selected_account = accounts[selected_index]
        transactions = db.get_transactions(current_user["id"], selected_account["account_id"])
    
    if not transactions:
        st.info("No transactions found for the selected account.")
        return
    
    # Sort transactions by date
    transactions = sorted(transactions, key=lambda x: x.get("date", ""), reverse=True)
    
    # Filters
    st.markdown("### 🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search transactions", "")
    
    with col2:
        min_amount = st.number_input("Min amount ($)", value=0.0, step=1.0)
    
    with col3:
        max_amount = st.number_input("Max amount ($)", value=10000.0, step=1.0)
    
    # Apply filters
    filtered_txns = transactions
    
    if search_term:
        filtered_txns = [
            t for t in filtered_txns
            if search_term.lower() in (t.get("name", "") + " " + str(t.get("merchant_name", ""))).lower()
        ]
    
    filtered_txns = [
        t for t in filtered_txns
        if min_amount <= abs(t.get("amount", 0)) <= max_amount
    ]
    
    # Summary
    st.markdown("---")
    st.markdown(f"### 📊 Summary - Showing {len(filtered_txns)} of {len(transactions)} transactions")
    
    col1, col2, col3 = st.columns(3)
    
    total_spent = sum(t.get("amount", 0) for t in filtered_txns if t.get("amount", 0) > 0)
    total_received = sum(abs(t.get("amount", 0)) for t in filtered_txns if t.get("amount", 0) < 0)
    
    with col1:
        st.metric("Total Spent", f"${total_spent:,.2f}")
    with col2:
        st.metric("Total Received", f"${total_received:,.2f}")
    with col3:
        st.metric("Net", f"${total_received - total_spent:,.2f}")
    
    st.markdown("---")
    
    # Transaction list
    st.markdown("### 📋 Transactions")
    
    # Display options
    show_categories = st.checkbox("Show categories", value=True)
    
    # Display transactions
    for i, txn in enumerate(filtered_txns[:100]):  # Limit to 100 for performance
        display_transaction(txn, show_categories)
        
        if i < len(filtered_txns) - 1:
            st.markdown("---")
    
    if len(filtered_txns) > 100:
        st.info(f"Showing first 100 transactions. Total: {len(filtered_txns)}")

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
