"""
AI Agents View - With Query Support and Frequent Questions
File: views/ai_agents.py
"""
import streamlit as st
import json
from datetime import datetime
import sys
from pathlib import Path
import requests

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client


def show_ai_agents(current_user):
    print(f"[AI_AGENTS] Loading AI agents page for user: {current_user.get('id')}")
    
    st.header("🤖 AI Financial Assistants")
    st.markdown("Get personalized recommendations and insights")
    
    if not current_user:
        st.error("Please login")
        return
    
    user_id = current_user.get('id')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 Recommendations")
        if st.button("🚀 Generate Recommendations", use_container_width=True, type="primary"):
            print("[AI_AGENTS] Generate recommendations button clicked")
            generate_recommendations(user_id)
    
    with col2:
        st.subheader("📊 Daily Summary")
        if st.button("📈 Generate Report", use_container_width=True, type="primary"):
            print("[AI_AGENTS] Generate daily summary button clicked")
            generate_daily_summary(user_id)
    
    st.markdown("---")
    
    show_frequent_questions(user_id)
    
    st.markdown("---")
    
    st.subheader("💬 Chat with AI")
    show_agent_chat(user_id)


def generate_recommendations(user_id: str):
    print(f"[AI_AGENTS] Generating recommendations for user: {user_id}")
    with st.spinner("🤖 Analyzing..."):
        try:
            api = get_api_client()
            print("[AI_AGENTS] Calling API: /api/ai/recommendations")
            result = api.get_recommendations()
            print(f"[AI_AGENTS] Recommendations received: {result.get('total_recommendations', 0)} recommendations")
            
            if result.get('status') == 'success' or result.get('recommendations'):
                total_recs = result.get('total_recommendations', len(result.get('recommendations', [])))
                st.success(f"✅ {total_recs} recommendations!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Recommendations", total_recs)
                with col2:
                    st.metric("Monthly Savings", f"${result.get('potential_monthly_savings', 0):.2f}")
                with col3:
                    st.metric("Annual Savings", f"${result.get('potential_annual_savings', 0):.2f}")
                
                st.markdown("### 🎯 Top Recommendations")
                
                recs = result.get('recommendations', [])
                if recs:
                    sorted_recs = sorted(recs, key=lambda x: (x.get('priority', 3), -x.get('potential_savings', 0)))
                    
                    for i, rec in enumerate(sorted_recs[:5], 1):
                        priority = rec.get('priority', 3)
                        emoji = "🔴" if priority == 1 else "🟡" if priority == 2 else "🟢"
                        
                        with st.expander(f"{emoji} {rec.get('title', 'Recommendation')}", expanded=(i <= 2)):
                            st.markdown(f"**{rec.get('description', '')}**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Monthly", f"${rec.get('potential_savings', 0):.2f}")
                            with col2:
                                st.metric("Annual", f"${rec.get('annual_savings', rec.get('potential_savings', 0) * 12):.2f}")
                            with col3:
                                st.metric("Priority", f"{priority}")
                else:
                    st.info("No recommendations available at this time.")
            else:
                st.warning("Unable to generate recommendations. Please try again later.")
        
        except Exception as e:
            print(f"[AI_AGENTS] Error generating recommendations: {str(e)}")
            st.error(f"❌ {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def generate_daily_summary(user_id: str):
    print(f"[AI_AGENTS] Generating daily summary for user: {user_id}")
    summary_date = st.date_input("Date:", value=datetime.now().date(), max_value=datetime.now().date())
    
    with st.spinner("🤖 Creating summary..."):
        try:
            api = get_api_client()
            print("[AI_AGENTS] Calling API: /api/ai/daily-summary")
            result = api.get_daily_summary()
            print(f"[AI_AGENTS] Daily summary received: status={result.get('status')}")
            
            if result.get('status') == 'success':
                st.success(f"✅ Summary for {result.get('summary_date', summary_date.isoformat())}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Spending", f"${result.get('total_spent', 0):.2f}")
                with col2:
                    st.metric("Transactions", result.get('transaction_count', 0))
                with col3:
                    st.metric("Top Category", result.get('top_category', 'N/A'))
                with col4:
                    subs_list = result.get('subscriptions_charged', [])
                    subs_count = len(subs_list) if isinstance(subs_list, list) else 0
                    st.metric("Subscriptions", subs_count)
                
                st.markdown("### 📄 Report")
                st.text(result.get('summary_text', 'No summary available'))
                
                if result.get('spending_by_category'):
                    st.markdown("### 💰 Breakdown")
                    import pandas as pd
                    df = pd.DataFrame([
                        {'Category': cat, 'Amount': amt} 
                        for cat, amt in result['spending_by_category'].items()
                    ]).sort_values('Amount', ascending=False)
                    st.bar_chart(df.set_index('Category'))
                
                if result.get('budget_alerts'):
                    st.markdown("### ⚠️ Alerts")
                    for alert in result['budget_alerts']:
                        st.warning(alert)
            else:
                st.warning("Unable to generate summary. Please try again later.")
        
        except Exception as e:
            print(f"[AI_AGENTS] Error generating daily summary: {str(e)}")
            st.error(f"❌ {str(e)}")
            import traceback
            st.code(traceback.format_exc())


def show_frequent_questions(user_id: str):
    """Display frequently asked questions as buttons - hardcoded, no API calls"""
    print(f"[AI_AGENTS] Loading frequent questions for user: {user_id}")
    
    # Hardcoded frequent questions - no API needed
    frequent_questions = [
        {
            'intent': 'subscription_most_expensive',
            'example_question': 'Which subscription costs the most?',
            'label': '💰 Top subscription'
        },
        {
            'intent': 'subscription_total_cost',
            'example_question': 'What is my total monthly subscription cost?',
            'label': '💵 Subscription cost'
        },
        {
            'intent': 'merchant_top_spending',
            'example_question': 'Where do I spend the most money?',
            'label': '🏪 Top store'
        },
        {
            'intent': 'category_breakdown',
            'example_question': 'Show me my spending by category',
            'label': '📊 Categories'
        },
        {
            'intent': 'spending_anomalies',
            'example_question': 'Are there any unusual spending patterns?',
            'label': '⚠️ Unusual'
        }
    ]
    
    if frequent_questions:
        st.subheader("🔥 Frequent Questions")
        
        cols = st.columns(min(len(frequent_questions), 3))
        
        for i, fq in enumerate(frequent_questions):
            col_idx = i % 3
            
            with cols[col_idx]:
                # Use form for each button to prevent full page rerun
                with st.form(f"freq_form_{i}", clear_on_submit=False):
                    if st.form_submit_button(
                        fq['label'], 
                        use_container_width=True
                    ):
                        # Set the question in session state - text input will pick it up
                        st.session_state['ai_chat_question'] = fq['example_question']
                        # Reset processed flag so the question shows up
                        if 'ai_chat_question_processed' in st.session_state:
                            del st.session_state['ai_chat_question_processed']
                        # Rerun to show the question in the input field
                        # st.rerun()


def show_agent_chat(user_id: str):
    print(f"[AI_AGENTS] Loading chat interface for user: {user_id}")
    
    # Initialize chat history in session state
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    # Initialize pending message flag
    if 'ai_chat_pending' not in st.session_state:
        st.session_state.ai_chat_pending = None
    
    st.markdown("Ask your AI about your finances:")
    
    # Get auto question from session state if set (from frequent questions)
    auto_question = st.session_state.get('ai_chat_question', "")
    
    # Process pending message if exists (from previous form submission)
    if st.session_state.ai_chat_pending:
        pending_msg = st.session_state.ai_chat_pending
        st.session_state.ai_chat_pending = None  # Clear pending flag
        
        # Add user message to history
        st.session_state.ai_chat_history.append({
            'role': 'user',
            'message': pending_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        # Call API
        try:
            api = get_api_client()
            print(f"[AI_AGENTS] Processing pending message: {pending_msg[:50]}...")
            
            with st.spinner("🤖 AI is thinking..."):
                result = api.chat_with_ai(pending_msg)
                print(f"[AI_AGENTS] API response: {result}")
                print(f"[AI_AGENTS] Chat response received: {len(str(result.get('response', '')))} chars")
            
            response_text = result.get('response', '') if isinstance(result, dict) else str(result)
            
            if response_text and response_text.strip():
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'message': response_text.strip(),
                    'timestamp': datetime.now().isoformat()
                })
                print(f"[AI_AGENTS] Added response to history: {response_text[:50]}...")
            else:
                error_msg = f"No response from AI. API returned: {result}"
                print(f"[AI_AGENTS] {error_msg}")
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
        except requests.exceptions.RequestException as e:
            print(f"[AI_AGENTS] Request error in chat: {str(e)}")
            error_msg = f"Network error: {str(e)}. Please check if the API is running."
            st.session_state.ai_chat_history.append({
                'role': 'assistant',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[AI_AGENTS] Error in chat: {str(e)}")
            import traceback
            print(f"[AI_AGENTS] Traceback: {traceback.format_exc()}")
            error_msg = f"Error: {str(e)}"
            st.session_state.ai_chat_history.append({
                'role': 'assistant',
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            })
    
    # Use form to prevent rerun on every keystroke
    with st.form("ai_chat_form", clear_on_submit=True):
        # Get the question value - use empty string if already processed
        question_value = auto_question if auto_question and 'ai_chat_question_processed' not in st.session_state else ""
        
        user_message = st.text_input(
            "Your message:",
            value=question_value,
            placeholder="e.g., 'Which subscription costs the most?'",
            key="agent_chat_input"
        )
        
        # Mark auto_question as processed so it doesn't keep showing
        if auto_question and 'ai_chat_question_processed' not in st.session_state:
            st.session_state['ai_chat_question_processed'] = True
        
        submitted = st.form_submit_button("💬 Send", use_container_width=True)
        
        if submitted and user_message and user_message.strip():
            # Store message as pending - will be processed on next rerun
            # This prevents the API call from happening during form submission
            # which would cause all tabs to rerun
            st.session_state.ai_chat_pending = user_message.strip()
            # Clear the auto question
            if 'ai_chat_question' in st.session_state:
                del st.session_state['ai_chat_question']
            if 'ai_chat_question_processed' in st.session_state:
                del st.session_state['ai_chat_question_processed']
            # Rerun to process the pending message
            # st.rerun()
    
    # Display chat history
    if st.session_state.ai_chat_history:
        st.markdown("---")
        st.markdown("### 💬 Conversation History")
        
        # Display messages in reverse order (newest first) or chronological
        for msg in reversed(st.session_state.ai_chat_history[-10:]):  # Show last 10 messages
            if msg['role'] == 'user':
                st.markdown(f"**You:** {msg['message']}")
            else:
                if msg['message'].startswith('Error:'):
                    st.error(f"**AI:** {msg['message']}")
                else:
                    st.success(f"**AI:** {msg['message']}")
            st.markdown("---")
        
        # Clear history button - use form to prevent unnecessary reruns
        with st.form("clear_history_form", clear_on_submit=False):
            if st.form_submit_button("🗑️ Clear History", use_container_width=True):
                st.session_state.ai_chat_history = []
                st.rerun()
    
    with st.expander("💡 Examples"):
        st.markdown("""
        **Subscriptions:** "Which subscription costs most?"
        **Spending:** "What's my biggest expense?"
        **Bills:** "Which bills are due soon?"
        **Analysis:** "Show unusual spending"
        **Compare:** "Compare this month to last month"
        **Actions:** "Generate recommendations" | "Show daily summary"
        """)
