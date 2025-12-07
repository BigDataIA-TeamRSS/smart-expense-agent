# auth.py
"""Authentication module for Smart Expense Analyzer POC"""

import streamlit as st

def handle_authentication() -> bool:
    """
    Handle user authentication in the sidebar
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    with st.sidebar:
        if not st.session_state.logged_in:
            st.header("Authentication")
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                handle_login()
            
            with tab2:
                handle_register()
            
            return False
        else:
            # User is logged in
            st.success(f"Welcome, {st.session_state.current_user['username']}!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚪 Logout", use_container_width=True):
                    logout()
            with col2:
                if st.button("👤 Profile", use_container_width=True):
                    show_profile()
            
            return True

def handle_login():
    """Handle user login"""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", use_container_width=True):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                user = st.session_state.db.authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

def handle_register():
    """Handle user registration"""
    with st.form("register_form"):
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("Register", use_container_width=True):
            # Validation
            if not all([new_username, new_email, new_password, confirm_password]):
                st.error("Please fill all fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif "@" not in new_email:
                st.error("Please enter a valid email")
            else:
                try:
                    user = st.session_state.db.create_user(
                        new_username, new_password, new_email
                    )
                    st.success("✅ Registration successful! Please login.")
                except ValueError as e:
                    st.error(str(e))

def logout():
    """Logout the current user"""
    st.session_state.logged_in = False
    st.session_state.current_user = None
    # Clear any stored tokens
    for key in ['link_token', 'hosted_link_url']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def show_profile():
    """Show user profile in a modal/expander"""
    with st.expander("User Profile", expanded=True):
        user = st.session_state.current_user
        st.write(f"**Username:** {user.get('username')}")
        st.write(f"**Email:** {user.get('email')}")
        st.write(f"**User ID:** {user.get('id')}")
        st.write(f"**Member Since:** {user.get('created_at', 'N/A')[:10]}")