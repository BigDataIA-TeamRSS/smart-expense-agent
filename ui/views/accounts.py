# # # pages/accounts.py
# # """Accounts page for Smart Expense Analyzer POC"""

# # import streamlit as st
# # from typing import Dict

# # def show_accounts(db, current_user: Dict):
# #     """Show the accounts page"""
# #     st.header("Your Bank Accounts")
    
# #     accounts = db.get_user_accounts(current_user["id"])
    
# #     if not accounts:
# #         st.info("No accounts connected yet.")
# #         st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
# #         return
    
# #     # Summary metrics
# #     col1, col2, col3 = st.columns(3)
    
# #     total_balance = sum(acc.get('current_balance', 0) or 0 for acc in accounts)
# #     total_available = sum(acc.get('available_balance', 0) or 0 for acc in accounts)
    
# #     with col1:
# #         st.metric("Total Accounts", len(accounts))
# #     with col2:
# #         st.metric("Total Balance", f"${total_balance:,.2f}")
# #     with col3:
# #         st.metric("Total Available", f"${total_available:,.2f}")
    
# #     st.markdown("---")
    
# #     # Display each account
# #     for account in accounts:
# #         with st.expander(f"{account['institution_name']} - {account['name']}", expanded=True):
# #             col1, col2, col3, col4 = st.columns(4)
            
# #             with col1:
# #                 balance = account.get('current_balance', 0)
# #                 st.metric(
# #                     "Current Balance",
# #                     f"${balance:,.2f}" if balance is not None else "N/A"
# #                 )
            
# #             with col2:
# #                 available = account.get('available_balance', 0)
# #                 st.metric(
# #                     "Available",
# #                     f"${available:,.2f}" if available is not None else "N/A"
# #                 )
            
# #             with col3:
# #                 st.metric("Type", account.get('type', 'Unknown').title())
            
# #             with col4:
# #                 st.metric("Account", f"****{account.get('mask', '????')}")
            
# #             # Additional details
# #             col1, col2 = st.columns(2)
            
# #             with col1:
# #                 if account.get('subtype'):
# #                     st.write(f"**Subtype:** {account['subtype'].title()}")
# #                 if account.get('official_name'):
# #                     st.write(f"**Official Name:** {account['official_name']}")
            
# #             with col2:
# #                 if account.get('currency'):
# #                     st.write(f"**Currency:** {account['currency']}")
# #                 if account.get('limit'):
# #                     st.write(f"**Credit Limit:** ${account['limit']:,.2f}")
            
# #             # Account actions
# #             col1, col2, col3 = st.columns(3)
            
# #             with col1:
# #                 # Get transaction count
# #                 txns = db.get_transactions(current_user["id"], account["account_id"])
# #                 st.info(f"📊 {len(txns)} transactions")
            
# #             with col2:
# #                 if st.button("🔄 Refresh", key=f"refresh_{account['id']}"):
# #                     st.info("Refresh functionality coming soon!")
            
# #             with col3:
# #                 if st.button("🗑️ Remove", key=f"remove_{account['id']}"):
# #                     if db.delete_account(current_user["id"], account["id"]):
# #                         st.success("Account removed")
# #                         st.rerun()




# # pages/accounts.py
# """Accounts page for Smart Expense Analyzer POC"""

# import streamlit as st
# from typing import Dict
# from datetime import datetime

# def show_accounts(db, plaid_service, current_user: Dict):
#     """Show the accounts page with refresh functionality"""
#     st.header("Your Bank Accounts")
    
#     accounts = db.get_user_accounts(current_user["id"])
    
#     if not accounts:
#         st.info("No accounts connected yet.")
#         st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
#         return
    
#     # Add a "Refresh All" button at the top
#     col1, col2, col3 = st.columns([1, 1, 2])
#     with col1:
#         if st.button("🔄 Refresh All Accounts", type="primary"):
#             refresh_all_accounts(db, plaid_service, current_user, accounts)
    
#     # Summary metrics
#     st.markdown("---")
#     col1, col2, col3 = st.columns(3)
    
#     total_balance = sum(acc.get('current_balance', 0) or 0 for acc in accounts)
#     total_available = sum(acc.get('available_balance', 0) or 0 for acc in accounts)
    
#     with col1:
#         st.metric("Total Accounts", len(accounts))
#     with col2:
#         st.metric("Total Balance", f"${total_balance:,.2f}")
#     with col3:
#         st.metric("Total Available", f"${total_available:,.2f}")
    
#     st.markdown("---")
    
#     # Display each account
#     for account in accounts:
#         with st.expander(f"{account['institution_name']} - {account['name']}", expanded=True):
#             col1, col2, col3, col4 = st.columns(4)
            
#             with col1:
#                 balance = account.get('current_balance', 0)
#                 st.metric(
#                     "Current Balance",
#                     f"${balance:,.2f}" if balance is not None else "N/A"
#                 )
            
#             with col2:
#                 available = account.get('available_balance', 0)
#                 st.metric(
#                     "Available",
#                     f"${available:,.2f}" if available is not None else "N/A"
#                 )
            
#             with col3:
#                 st.metric("Type", account.get('type', 'Unknown').title())
            
#             with col4:
#                 st.metric("Account", f"****{account.get('mask', '????')}")
            
#             # Additional details
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 if account.get('subtype'):
#                     st.write(f"**Subtype:** {account['subtype'].title()}")
#                 if account.get('official_name'):
#                     st.write(f"**Official Name:** {account['official_name']}")
            
#             with col2:
#                 if account.get('currency'):
#                     st.write(f"**Currency:** {account['currency']}")
#                 if account.get('limit'):
#                     st.write(f"**Credit Limit:** ${account['limit']:,.2f}")
            
#             # Show last sync time
#             if account.get('last_synced'):
#                 try:
#                     last_sync = datetime.fromisoformat(account['last_synced'])
#                     time_ago = datetime.now() - last_sync
#                     if time_ago.days > 0:
#                         sync_text = f"{time_ago.days} days ago"
#                     elif time_ago.seconds > 3600:
#                         sync_text = f"{time_ago.seconds // 3600} hours ago"
#                     else:
#                         sync_text = f"{time_ago.seconds // 60} minutes ago"
#                     st.caption(f"Last synced: {sync_text}")
#                 except:
#                     pass
            
#             # Account actions
#             col1, col2, col3 = st.columns(3)
            
#             with col1:
#                 # Get transaction count
#                 txns = db.get_transactions(current_user["id"], account["account_id"])
#                 st.info(f"📊 {len(txns)} transactions")
            
#             with col2:
#                 if st.button("🔄 Refresh", key=f"refresh_{account['id']}"):
#                     refresh_single_account(db, plaid_service, current_user, account)
            
#             with col3:
#                 if st.button("🗑️ Remove", key=f"remove_{account['id']}"):
#                     if db.delete_account(current_user["id"], account["id"]):
#                         st.success("Account removed")
#                         st.rerun()

# def refresh_single_account(db, plaid_service, current_user: Dict, account: Dict):
#     """Refresh a single account's data"""
#     with st.spinner(f"Refreshing {account['name']}..."):
#         try:
#             # Get the access token for this account
#             access_token = account.get('access_token')
#             if not access_token:
#                 st.error("No access token found for this account")
#                 return
            
#             # Get updated account information
#             updated_accounts = plaid_service.get_accounts(access_token)
            
#             # Update this specific account
#             for updated in updated_accounts:
#                 if updated['account_id'] == account['account_id']:
#                     # Update account balance and details
#                     account.update({
#                         'current_balance': updated['current_balance'],
#                         'available_balance': updated['available_balance'],
#                         'limit': updated.get('limit'),
#                         'last_synced': datetime.now().isoformat()
#                     })
                    
#                     # Save updated account
#                     db.save_bank_account(current_user["id"], account)
#                     break
            
#             # Sync new transactions
#             sync_result = plaid_service.sync_transactions(access_token, account.get('cursor'))
            
#             if sync_result['transactions']:
#                 # Save new transactions
#                 new_count = db.save_transactions(
#                     current_user["id"],
#                     account["account_id"],
#                     sync_result['transactions']
#                 )
                
#                 # Update cursor for next sync
#                 if sync_result.get('cursor'):
#                     account['cursor'] = sync_result['cursor']
#                     db.save_bank_account(current_user["id"], account)
                
#                 st.success(f"✅ Refreshed! Found {new_count} new transactions")
#             else:
#                 st.info("✅ Account refreshed. No new transactions.")
            
#             st.rerun()
            
#         except Exception as e:
#             st.error(f"Error refreshing account: {str(e)}")

# def refresh_all_accounts(db, plaid_service, current_user: Dict, accounts: list):
#     """Refresh all accounts at once"""
#     progress_bar = st.progress(0)
#     status_text = st.empty()
    
#     total_new_transactions = 0
    
#     for i, account in enumerate(accounts):
#         # Update progress
#         progress = (i + 1) / len(accounts)
#         progress_bar.progress(progress)
#         status_text.text(f"Refreshing {account['name']}...")
        
#         try:
#             access_token = account.get('access_token')
#             if not access_token:
#                 continue
            
#             # Get updated account information
#             updated_accounts = plaid_service.get_accounts(access_token)
            
#             # Update account balances
#             for updated in updated_accounts:
#                 if updated['account_id'] == account['account_id']:
#                     account.update({
#                         'current_balance': updated['current_balance'],
#                         'available_balance': updated['available_balance'],
#                         'limit': updated.get('limit'),
#                         'last_synced': datetime.now().isoformat()
#                     })
#                     db.save_bank_account(current_user["id"], account)
#                     break
            
#             # Sync transactions
#             sync_result = plaid_service.sync_transactions(
#                 access_token, 
#                 account.get('cursor')
#             )
            
#             if sync_result['transactions']:
#                 new_count = db.save_transactions(
#                     current_user["id"],
#                     account["account_id"],
#                     sync_result['transactions']
#                 )
#                 total_new_transactions += new_count
                
#                 # Update cursor
#                 if sync_result.get('cursor'):
#                     account['cursor'] = sync_result['cursor']
#                     db.save_bank_account(current_user["id"], account)
            
#         except Exception as e:
#             st.warning(f"Error refreshing {account['name']}: {str(e)}")
    
#     # Clear progress indicators
#     progress_bar.empty()
#     status_text.empty()
    
#     if total_new_transactions > 0:
#         st.success(f"✅ All accounts refreshed! Found {total_new_transactions} new transactions total")
#     else:
#         st.info("✅ All accounts refreshed. No new transactions found.")
    
#     st.rerun()

# pages/accounts.py
"""Accounts page for Smart Expense Analyzer POC"""

import streamlit as st
from typing import Dict
from datetime import datetime

def show_accounts(db, plaid_service, current_user: Dict):
    """Show the accounts page with refresh functionality"""
    st.header("Your Bank Accounts")
    
    accounts = db.get_user_accounts(current_user["id"])
    
    if not accounts:
        st.info("No accounts connected yet.")
        st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
        return
    
    # Add a "Refresh All" button at the top
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh All Accounts", type="primary"):
            refresh_all_accounts(db, plaid_service, current_user, accounts)
    
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
            
            with col1:
                # Get transaction count
                txns = db.get_transactions(current_user["id"], account["account_id"])
                st.info(f"📊 {len(txns)} transactions")
            
            with col2:
                if st.button("🔄 Refresh", key=f"refresh_{account['id']}"):
                    refresh_single_account(db, plaid_service, current_user, account)
            
            with col3:
                if st.button("🗑️ Remove", key=f"remove_{account['id']}"):
                    if db.delete_account(current_user["id"], account["id"]):
                        st.success("Account removed")
                        st.rerun()

def refresh_single_account(db, plaid_service, current_user: Dict, account: Dict):
    """Refresh a single account's data"""
    with st.spinner(f"Refreshing {account['name']}..."):
        try:
            # Get the access token for this account
            access_token = account.get('access_token')
            if not access_token:
                st.error("No access token found for this account")
                return
            
            # Get updated account information
            updated_accounts = plaid_service.get_accounts(access_token)
            
            # Update this specific account
            for updated in updated_accounts:
                if updated['account_id'] == account['account_id']:
                    # Update account balance and details
                    account.update({
                        'current_balance': updated['current_balance'],
                        'available_balance': updated['available_balance'],
                        'limit': updated.get('limit'),
                        'last_synced': datetime.now().isoformat()
                    })
                    
                    # Save updated account
                    db.save_bank_account(current_user["id"], account)
                    break
            
            # Sync new transactions
            sync_result = plaid_service.sync_transactions(access_token, account.get('cursor'))
            
            if sync_result['transactions']:
                # Save new transactions
                new_count = db.save_transactions(
                    current_user["id"],
                    account["account_id"],
                    sync_result['transactions']
                )
                
                # Update cursor for next sync
                if sync_result.get('cursor'):
                    account['cursor'] = sync_result['cursor']
                    db.save_bank_account(current_user["id"], account)
                
                st.success(f"✅ Refreshed! Found {new_count} new transactions")
            else:
                st.info("✅ Account refreshed. No new transactions.")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error refreshing account: {str(e)}")

def refresh_all_accounts(db, plaid_service, current_user: Dict, accounts: list):
    """Refresh all accounts at once"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_new_transactions = 0
    
    for i, account in enumerate(accounts):
        # Update progress
        progress = (i + 1) / len(accounts)
        progress_bar.progress(progress)
        status_text.text(f"Refreshing {account['name']}...")
        
        try:
            access_token = account.get('access_token')
            if not access_token:
                continue
            
            # Get updated account information
            updated_accounts = plaid_service.get_accounts(access_token)
            
            # Update account balances
            for updated in updated_accounts:
                if updated['account_id'] == account['account_id']:
                    account.update({
                        'current_balance': updated['current_balance'],
                        'available_balance': updated['available_balance'],
                        'limit': updated.get('limit'),
                        'last_synced': datetime.now().isoformat()
                    })
                    db.save_bank_account(current_user["id"], account)
                    break
            
            # Sync transactions
            sync_result = plaid_service.sync_transactions(
                access_token, 
                account.get('cursor')
            )
            
            if sync_result['transactions']:
                new_count = db.save_transactions(
                    current_user["id"],
                    account["account_id"],
                    sync_result['transactions']
                )
                total_new_transactions += new_count
                
                # Update cursor
                if sync_result.get('cursor'):
                    account['cursor'] = sync_result['cursor']
                    db.save_bank_account(current_user["id"], account)
            
        except Exception as e:
            st.warning(f"Error refreshing {account['name']}: {str(e)}")
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    if total_new_transactions > 0:
        st.success(f"✅ All accounts refreshed! Found {total_new_transactions} new transactions total")
    else:
        st.info("✅ All accounts refreshed. No new transactions found.")
    
    st.rerun()