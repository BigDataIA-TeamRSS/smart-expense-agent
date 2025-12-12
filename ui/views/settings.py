"""User Settings - Profile and Preferences Management"""
import streamlit as st
from datetime import datetime

def show_settings(db, current_user):
    """Main settings page with profile and preferences"""
    
    st.header("Settings")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Profile", "Preferences", "Account"])
    
    # Profile Tab
    with tab1:
        show_profile_tab(db, current_user)
    
    # Preferences Tab
    with tab2:
        show_preferences_tab(db, current_user)
    
    # Account Tab
    with tab3:
        show_account_tab(db, current_user)

def show_profile_tab(db, current_user):
    """Profile information and personalization"""
    
    st.subheader("Financial Profile")
    
    # Check if profile is complete
    profile_completed = current_user.get('profile_completed', False)
    
    if not profile_completed:
        st.info("Complete your profile to unlock personalized insights and income-based budgets")
    else:
        st.success("Profile completed! You're getting personalized insights.")
    
    st.markdown("---")
    
    # Profile Form
    with st.form("profile_form"):
        
        st.markdown("#### Income Information")
        st.caption("Used for income-based budget recommendations")
        
        monthly_income = st.number_input(
            "Monthly Income (after taxes)",
            min_value=0.0,
            max_value=1000000.0,
            value=float(current_user.get('monthly_income') or 0),
            step=100.0,
            help="Your monthly take-home income"
        )
        
        if monthly_income > 0:
            st.success(f"With ${monthly_income:,.2f}/month income, we'll show spending as % of income")
        
        st.markdown("---")
        
        st.markdown("#### Household Information")
        st.caption("Helps adjust budget expectations based on your situation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            life_stage_options = [
                "Not specified",
                "Young Professional (18-34)",
                "Family with Kids (25-50)",
                "Mid-Career (35-55)",
                "Pre-Retirement (55-65)",
                "Retired (65+)"
            ]
            
            current_life_stage = current_user.get('life_stage') or "Not specified"
            
            # Find index
            try:
                life_stage_index = life_stage_options.index(current_life_stage)
            except ValueError:
                life_stage_index = 0
            
            life_stage = st.selectbox(
                "Life Stage",
                options=life_stage_options,
                index=life_stage_index,
                help="Your current life stage"
            )
        
        with col2:
            dependents = st.number_input(
                "Number of Dependents",
                min_value=0,
                max_value=20,
                value=int(current_user.get('dependents') or 0),
                help="Children, elderly parents, or others you support"
            )
        
        st.markdown("---")
        
        st.markdown("#### Location")
        st.caption("For regional cost-of-living context")
        
        location = st.text_input(
            "City, State",
            value=current_user.get('location') or "",
            placeholder="e.g., Boston, MA"
        )
        
        st.markdown("---")
        
        # What you'll unlock
        st.markdown("#### What You'll Unlock")
        
        unlocked_features = []
        
        if monthly_income > 0:
            unlocked_features.append("Income-based budget recommendations (50/30/20 rule)")
            unlocked_features.append("Spending as percentage of income")
            unlocked_features.append("Savings rate tracking")
        
        if life_stage != "Not specified":
            unlocked_features.append("Life-stage appropriate spending expectations")
        
        if dependents > 0:
            unlocked_features.append("Family-size adjusted grocery/healthcare budgets")
        
        if location:
            unlocked_features.append("Regional cost-of-living comparisons")
        
        if unlocked_features:
            for feature in unlocked_features:
                st.markdown(f"✅ {feature}")
        else:
            st.info("Fill in fields above to unlock personalized features")
        
        st.markdown("---")
        
        # Submit button
        submitted = st.form_submit_button("Save Profile", type="primary")
        
        if submitted:
            try:
                # Prepare profile data
                profile_data = {
                    'monthly_income': monthly_income if monthly_income > 0 else None,
                    'life_stage': life_stage if life_stage != "Not specified" else None,
                    'dependents': dependents if dependents > 0 else None,
                    'location': location if location else None,
                    'profile_completed': any([
                        monthly_income > 0,
                        life_stage != "Not specified",
                        dependents > 0,
                        location
                    ]),
                    'profile_completed_at': datetime.utcnow().isoformat() if any([
                        monthly_income > 0,
                        life_stage != "Not specified",
                        dependents > 0,
                        location
                    ]) else None
                }
                
                # Update database
                updated_user = db.update_user_profile(
                    user_id=current_user['id'],
                    **profile_data
                )
                
                # Update session
                st.session_state.current_user.update(profile_data)
                
                st.success("Profile updated successfully!")
                st.balloons()
                
                # Refresh page to show changes
                st.rerun()
                
            except Exception as e:
                st.error(f"Error updating profile: {str(e)}")

def show_preferences_tab(db, current_user):
    """Alert and notification preferences"""
    
    st.subheader("Alert Preferences")
    
    with st.form("preferences_form"):
        
        st.markdown("#### Budget Alert Sensitivity")
        st.caption("When should we alert you about spending increases?")
        
        alert_threshold = st.slider(
            "Alert when spending exceeds your baseline by:",
            min_value=1.1,
            max_value=2.0,
            value=float(current_user.get('budget_alert_threshold') or 1.3),
            step=0.1,
            format="%.1fx",
            help="Lower = more alerts, Higher = fewer alerts"
        )
        
        # Show examples
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Strict", "1.1x", "More alerts")
            st.caption("Alert at 10% over baseline")
        
        with col2:
            st.metric("Normal", "1.3x", "Balanced")
            st.caption("Alert at 30% over baseline")
        
        with col3:
            st.metric("Relaxed", "1.5x", "Fewer alerts")
            st.caption("Alert at 50% over baseline")
        
        st.markdown("---")
        
        st.markdown("#### Example")
        st.info(f"""
        If your typical dining spending is $200/month:
        
        With limit for yourself **{alert_threshold}x**:
        - You'll get an alert when dining exceeds **${200 * alert_threshold:.2f}**
        - Current setting: **{(alert_threshold - 1) * 100:.0f}% above your baseline**
        """)
        
        st.markdown("---")
        
        # Submit
        submitted = st.form_submit_button("Save Preferences", type="primary")
        
        if submitted:
            try:
                db.update_user_preferences(
                    user_id=current_user['id'],
                    budget_alert_threshold=alert_threshold
                )
                
                st.session_state.current_user['budget_alert_threshold'] = alert_threshold
                
                st.success("Preferences updated!")
                
            except Exception as e:
                st.error(f"Error updating preferences: {str(e)}")

def show_account_tab(db, current_user):
    """Account management and security"""
    
    st.subheader("Account Information")
    
    # Display current info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Username**")
        st.code(current_user.get('username', 'N/A'))
    
    with col2:
        st.markdown("**Email**")
        st.code(current_user.get('email', 'N/A'))
    
    st.markdown("**Account Created**")
    created_at = current_user.get('created_at', 'Unknown')
    st.code(created_at)
    
    st.markdown("---")
    
    # Change Password Section
    st.subheader("Security")
    
    with st.form("change_password_form"):
        st.markdown("#### Change Password")
        
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new = st.text_input("Confirm New Password", type="password")
        
        change_pw = st.form_submit_button("Change Password", type="primary")
        
        if change_pw:
            if not all([current_password, new_password, confirm_new]):
                st.error("Please fill in all fields")
            elif new_password != confirm_new:
                st.error("New passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                # Verify current password
                user_check = db.authenticate_user(current_user['username'], current_password)
                if user_check:
                    try:
                        db.change_password(current_user['id'], new_password)
                        st.success("Password changed successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Current password is incorrect")
    
    st.markdown("---")
    
    # Danger Zone
    with st.expander("Danger Zone"):
        st.warning("These actions cannot be undone")
        
        # Clear data
        st.markdown("**Clear All Transaction Data**")
        st.caption("Removes all transactions and accounts but keeps your account")
        
        if st.button("Clear All Data"):
            st.session_state.confirm_clear = True
        
        if st.session_state.get('confirm_clear'):
            st.error("Are you absolutely sure?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Cancel"):
                    st.session_state.confirm_clear = False
                    st.rerun()
            
            with col2:
                if st.button("Yes, Delete All Data", type="primary"):
                    try:
                        db.clear_user_data(current_user['id'])
                        st.session_state.confirm_clear = False
                        st.success("All data cleared!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")