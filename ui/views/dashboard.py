"""Dashboard view for Smart Expense Analyzer"""
import streamlit as st
from typing import Dict
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client

def _fetch_dashboard_data(user_id: str):
    """Fetch dashboard data from API"""
    api = get_api_client()
    print("[DASHBOARD] Calling API: /api/analytics/dashboard")
    data = api.get_dashboard()
    print(f"[DASHBOARD] Received dashboard data: {len(data.get('recent_transactions', []))} recent transactions")
    return data

def show_dashboard(current_user: Dict):
    """Display the main dashboard"""
    user_id = current_user.get('id')
    cache_key = f"dashboard_data_{user_id}"
    
    print(f"[DASHBOARD] Loading dashboard for user: {user_id}")
    
    # Skip API calls if we're in a file upload operation
    if st.session_state.get('skip_api_calls', False):
        print("[DASHBOARD] Skipping API call (file operation in progress)")
        if cache_key in st.session_state and st.session_state[cache_key]:
            dashboard_data = st.session_state[cache_key]
        else:
            st.info("Loading...")
            return
    
    st.header("📊 Dashboard")
    
    # Manual refresh button
    col1, col2 = st.columns([1, 10])
    with col1:
        refresh_key = f"refresh_{cache_key}"
        if st.button("🔄", help="Refresh dashboard data", key="refresh_dashboard"):
            st.session_state[refresh_key] = True
    
    try:
        # Check if we need to fetch (no data or refresh requested)
        refresh_requested = st.session_state.get(f"refresh_{cache_key}", False)
        
        if cache_key not in st.session_state or st.session_state[cache_key] is None or refresh_requested:
            # Fetch from API
            dashboard_data = _fetch_dashboard_data(user_id)
            st.session_state[cache_key] = dashboard_data
            st.session_state[f"refresh_{cache_key}"] = False
        else:
            # Use cached data from session state
            dashboard_data = st.session_state[cache_key]
            print("[DASHBOARD] Using cached data from session state")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Accounts", dashboard_data["total_accounts"])
        
        with col2:
            st.metric("Total Transactions", dashboard_data["total_transactions"])
        
        with col3:
            st.metric("Total Balance", f"${dashboard_data['total_balance']:,.2f}")
        
        # Recent activity
        recent_transactions = dashboard_data.get("recent_transactions", [])
        if recent_transactions:
            st.subheader("Recent Transactions")
            print(f"[DASHBOARD] Displaying {len(recent_transactions)} recent transactions")
            
            for txn in recent_transactions:
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
        
        print("[DASHBOARD] Dashboard loaded successfully")
        
    except Exception as e:
        print(f"[DASHBOARD] Error loading dashboard: {str(e)}")
        st.error(f"Error loading dashboard: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
