"""Main Streamlit application for Smart Expense Analyzer POC"""
import sys
from pathlib import Path

# Add the project root to Python path so we can import from src/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import views (after path is set up)
from views.ai_agents import show_ai_agents

import streamlit as st
from src.config import Config
# Removed direct database and plaid imports - now using API client
# from src.core.database import get_database
# from src.integrations.plaid_service import PlaidService

# Import page modules
from views import dashboard, connect_bank, accounts, transactions, analytics
from views.statement_upload import show_statement_upload  # NEW
from views.settings import show_settings 
from src.core.auth import handle_authentication
from ui.api_client import get_api_client

def initialize_session_state():
    """Initialize all session state variables"""
    print("[MAIN] Initializing session state...")
    
    # Initialize API client (replaces db and plaid)
    if 'api_client' not in st.session_state:
        print("[MAIN] Creating API client...")
        st.session_state.api_client = get_api_client()
        print(f"[MAIN] API client created, base URL: {st.session_state.api_client.base_url}")
    
    # Debug: Check if token exists
    if 'api_token' in st.session_state:
        token = st.session_state.api_token
        print(f"[MAIN] Token found in session: {token[:30]}..." if len(token) > 30 else f"[MAIN] Token found: {token}")
    else:
        print("[MAIN] No token in session state yet")
    
    # Keep db for backward compatibility during migration (will be removed)
    # if 'db' not in st.session_state:
    #     st.session_state.db = get_database()
    
    # if 'plaid' not in st.session_state:
    #     st.session_state.plaid = PlaidService()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    # Flag to skip API calls during file operations
    if 'skip_api_calls' not in st.session_state:
        st.session_state.skip_api_calls = False
    
    print("[MAIN] Session state initialized")

def main():
    """Main application entry point"""
    import time
    main_start = time.time()
    
    # Page configuration
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT
    )
    
    # Initialize session state
    init_start = time.time()
    initialize_session_state()
    init_time = time.time() - init_start
    print(f"[MAIN] Initialization took {init_time:.3f}s")
    
    # App title
    st.title(f"{Config.PAGE_ICON} {Config.APP_NAME}")
    st.markdown("### Smart Financial Analysis with Plaid & PDF Uploads")
    
    # Handle authentication in sidebar
    if not handle_authentication():
        # User is not logged in, show login/register page
        st.info("Please login or register to continue")
        show_data_storage_info()
        return
    
    # User is logged in, show main application
    tabs = st.tabs([
        "📊 Dashboard", 
        "🏦 Connect Bank", 
        "📄 Upload Statements",  # NEW TAB
        "💳 Accounts", 
        "💸 Transactions", 
        "📈 Analytics",
        "🤖 AI Agents",
        "⚙️ Settings"  # NEW
    ])
    
    # Note: Streamlit tabs execute all code on page load, not when clicked
    # This is normal Streamlit behavior - all tab content runs immediately
    # The UI (tabs) remain in Streamlit, but they make API calls to get data
    # We've optimized by removing unnecessary API calls (e.g., transaction counts)
    
    tabs_start = time.time()
    with tabs[0]:
        print("[MAIN] Loading Dashboard tab...")
        dashboard.show_dashboard(st.session_state.current_user)
    
    with tabs[1]:
        print("[MAIN] Loading Connect Bank tab...")
        connect_bank.show_connect_bank(st.session_state.current_user)
    
    with tabs[2]:  # NEW
        print("[MAIN] Loading Upload Statements tab...")
        show_statement_upload(st.session_state.current_user)
    
    with tabs[3]:
        print("[MAIN] Loading Accounts tab...")
        accounts.show_accounts(st.session_state.current_user)
    
    with tabs[4]:
        print("[MAIN] Loading Transactions tab...")
        transactions.show_transactions(st.session_state.current_user)
    
    with tabs[5]:
        print("[MAIN] Loading Analytics tab...")
        analytics.show_analytics(st.session_state.current_user)

    with tabs[6]:
        print("[MAIN] Loading AI Agents tab...")
        show_ai_agents(st.session_state.current_user)  

    # Add settings tab handler
    with tabs[7]:  # 7th tab (index 6)
        print("[MAIN] Loading Settings tab...")
        show_settings(st.session_state.current_user)
    
    tabs_time = time.time() - tabs_start
    total_time = time.time() - main_start
    print(f"[MAIN] All tabs loaded in {tabs_time:.3f}s (total page load: {total_time:.3f}s)")
    
    # Footer
    show_data_storage_info()

def show_data_storage_info():
    """Show information about data storage"""
    st.markdown("---")
    st.markdown("### 📁 Data Storage Info")
    st.markdown(f"Data is stored in JSON files at: `{Config.DATA_DIR}`")
    
    if st.session_state.logged_in and st.checkbox("Show Database Stats"):
        print("[MAIN] Fetching database stats...")
        try:
            # Note: Database stats endpoint not yet implemented in API
            # For now, show message that this feature needs API endpoint
            st.info("Database stats feature requires API endpoint implementation")
            # TODO: Add /api/admin/stats endpoint when needed
        except Exception as e:
            print(f"[MAIN] Error getting stats: {str(e)}")
            st.error(f"Error loading stats: {str(e)}")

if __name__ == "__main__":
    main()