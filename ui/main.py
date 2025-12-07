# # main.py
# """Main Streamlit application for Smart Expense Analyzer POC"""
# import sys
# from pathlib import Path

# # Add the project root to Python path so we can import from src/
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

# import streamlit as st
# from src.config import Config
# from src.database import JSONDatabase
# from src.plaid_service import PlaidService

# # Import page modules
# from views import dashboard, connect_bank, accounts, transactions, analytics
# from src.auth import handle_authentication

# def initialize_session_state():
#     """Initialize all session state variables"""
#     if 'db' not in st.session_state:
#         st.session_state.db = JSONDatabase()
    
#     if 'plaid' not in st.session_state:
#         st.session_state.plaid = PlaidService()
    
#     if 'logged_in' not in st.session_state:
#         st.session_state.logged_in = False
    
#     if 'current_user' not in st.session_state:
#         st.session_state.current_user = None

# def main():
#     """Main application entry point"""
#     # Page configuration
#     st.set_page_config(
#         page_title=Config.APP_NAME,
#         page_icon=Config.PAGE_ICON,
#         layout=Config.LAYOUT
#     )
    
#     # Initialize session state
#     initialize_session_state()
    
#     # App title
#     st.title(f"{Config.PAGE_ICON} {Config.APP_NAME}")
#     st.markdown("### Simple Plaid Integration with JSON Storage")
    
#     # Handle authentication in sidebar
#     if not handle_authentication():
#         # User is not logged in, show login/register page
#         st.info("Please login or register to continue")
#         show_data_storage_info()
#         return
    
#     # User is logged in, show main application
#     tabs = st.tabs([
#         "📊 Dashboard", 
#         "🏦 Connect Bank", 
#         "💳 Accounts", 
#         "💸 Transactions", 
#         "📈 Analytics"
#     ])
    
#     with tabs[0]:
#         dashboard.show_dashboard(st.session_state.db, st.session_state.current_user)
    
#     with tabs[1]:
#         connect_bank.show_connect_bank(
#             st.session_state.db, 
#             st.session_state.plaid, 
#             st.session_state.current_user
#         )
    
#     with tabs[2]:
#         accounts.show_accounts(st.session_state.db, st.session_state.plaid, st.session_state.current_user)
    
#     with tabs[3]:
#         transactions.show_transactions(st.session_state.db, st.session_state.current_user)
    
#     with tabs[4]:
#         analytics.show_analytics(st.session_state.db, st.session_state.current_user)
    
#     # Footer
#     show_data_storage_info()

# def show_data_storage_info():
#     """Show information about data storage"""
#     st.markdown("---")
#     st.markdown("### 📁 Data Storage Info")
#     st.markdown(f"Data is stored in JSON files at: `{Config.DATA_DIR}`")
    
#     if st.session_state.logged_in and st.checkbox("Show Database Stats"):
#         stats = st.session_state.db.get_database_stats()
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("Total Users", stats["total_users"])
#         with col2:
#             st.metric("Total Accounts", stats["total_accounts"])
#         with col3:
#             st.metric("Total Transactions", stats["total_transactions"])

# if __name__ == "__main__":
#     main()


"""Main Streamlit application for Smart Expense Analyzer POC"""
import sys
from pathlib import Path

# Add the project root to Python path so we can import from src/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.config import Config
from src.database import JSONDatabase
from src.plaid_service import PlaidService

# Import page modules
from views import dashboard, connect_bank, accounts, transactions, analytics
from views.statement_upload import show_statement_upload  # NEW
from src.auth import handle_authentication

def initialize_session_state():
    """Initialize all session state variables"""
    if 'db' not in st.session_state:
        st.session_state.db = JSONDatabase()
    
    if 'plaid' not in st.session_state:
        st.session_state.plaid = PlaidService()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(
        page_title=Config.APP_NAME,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT
    )
    
    # Initialize session state
    initialize_session_state()
    
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
        "📈 Analytics"
    ])
    
    with tabs[0]:
        dashboard.show_dashboard(st.session_state.db, st.session_state.current_user)
    
    with tabs[1]:
        connect_bank.show_connect_bank(
            st.session_state.db, 
            st.session_state.plaid, 
            st.session_state.current_user
        )
    
    with tabs[2]:  # NEW
        show_statement_upload(st.session_state.db, st.session_state.current_user)
    
    with tabs[3]:
        accounts.show_accounts(st.session_state.db, st.session_state.plaid, st.session_state.current_user)
    
    with tabs[4]:
        transactions.show_transactions(st.session_state.db, st.session_state.current_user)
    
    with tabs[5]:
        analytics.show_analytics(st.session_state.db, st.session_state.current_user)
    
    # Footer
    show_data_storage_info()

def show_data_storage_info():
    """Show information about data storage"""
    st.markdown("---")
    st.markdown("### 📁 Data Storage Info")
    st.markdown(f"Data is stored in JSON files at: `{Config.DATA_DIR}`")
    
    if st.session_state.logged_in and st.checkbox("Show Database Stats"):
        stats = st.session_state.db.get_database_stats()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", stats["total_users"])
        with col2:
            st.metric("Total Accounts", stats["total_accounts"])
        with col3:
            st.metric("Plaid Transactions", stats.get("plaid_transactions", 0))
        with col4:
            st.metric("PDF Transactions", stats.get("pdf_transactions", 0))

if __name__ == "__main__":
    main()