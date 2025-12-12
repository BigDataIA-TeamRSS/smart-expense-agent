"""
AI Agents View - Powered by Agent 3 Supervisor
File: views/ai_agents.py

Uses the Supervisor to orchestrate all AI agent interactions.
"""

import streamlit as st
import json
from datetime import datetime


def show_ai_agents(db, current_user):
    """Main AI Agents view"""
    st.header("🤖 AI Financial Assistants")
    st.markdown("Get personalized recommendations and insights powered by multi-agent AI")
    
    if not current_user:
        st.error("Please login to use AI features")
        return
    
    user_id = current_user.get('id')
    
    # Main action buttons in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💡 Recommendations")
        if st.button("🚀 Generate", type="primary", key="btn_recommendations"):
            generate_recommendations(user_id)
    
    with col2:
        st.subheader("📊 Daily Summary")
        if st.button("📈 Report", type="primary", key="btn_summary"):
            generate_daily_summary(user_id)
    
    with col3:
        st.subheader("⚡ Full Pipeline")
        if st.button("🔄 Run All", type="secondary", key="btn_pipeline"):
            run_full_pipeline(user_id)
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Chat with AI")
    show_agent_chat(user_id)
    
    # Show agent status in expander
    with st.expander("🔧 Agent Status"):
        show_agent_status()


def get_supervisor():
    """Get or create the Supervisor instance"""
    try:
        from agents.agent3_supervisor import get_supervisor
        return get_supervisor()
    except ImportError as e:
        st.error(f"Could not load Supervisor: {e}")
        return None


def generate_recommendations(user_id: str):
    """Generate recommendations using Supervisor"""
    with st.spinner("🤖 Analyzing your finances..."):
        supervisor = get_supervisor()
        
        if supervisor is None:
            st.error("Supervisor not available")
            return
        
        try:
            result = supervisor.handle_request(user_id, "generate recommendations")
            display_recommendations_result(result)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def generate_daily_summary(user_id: str):
    """Generate daily summary using Supervisor"""
    summary_date = st.date_input(
        "Select date:", 
        value=datetime.now().date(), 
        max_value=datetime.now().date(),
        key="summary_date_picker"
    )
    
    with st.spinner("🤖 Creating summary..."):
        supervisor = get_supervisor()
        
        if supervisor is None:
            st.error("Supervisor not available")
            return
        
        try:
            # Use Agent 2 directly for summary with date
            result = supervisor._run_agent2_summary(user_id, summary_date.isoformat())
            display_summary_result(result)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def run_full_pipeline(user_id: str):
    """Run the complete processing pipeline"""
    with st.spinner("🔄 Running full pipeline (this may take a moment)..."):
        supervisor = get_supervisor()
        
        if supervisor is None:
            st.error("Supervisor not available")
            return
        
        try:
            result = supervisor.run_full_pipeline(user_id)
            display_pipeline_result(result)
        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}")


def show_agent_chat(user_id: str):
    """Chat interface for interacting with the Supervisor"""
    
    # Check for auto-question from session state
    default_value = ""
    if 'auto_question' in st.session_state:
        default_value = st.session_state['auto_question']
        del st.session_state['auto_question']
    
    user_message = st.text_input(
        "Ask anything about your finances:",
        value=default_value,
        placeholder="e.g., 'Which subscription costs the most?' or 'Run full pipeline'",
        key="agent_chat_input"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        send_clicked = st.button("💬 Send", type="primary")
    
    with col2:
        if st.button("🗑️ Clear"):
            st.session_state['chat_history'] = []
            st.rerun()
    
    # Process message
    if (send_clicked or default_value) and user_message:
        with st.spinner("🤖 Thinking..."):
            supervisor = get_supervisor()
            
            if supervisor is None:
                st.error("Supervisor not available")
                return
            
            try:
                result = supervisor.handle_request(user_id, user_message)
                display_chat_response(result)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **Quick Actions:**
        - "Generate recommendations"
        - "Show daily summary"
        - "Run full pipeline"
        
        **Questions:**
        - "Which subscription costs the most?"
        - "What's my biggest expense category?"
        - "Show unusual spending"
        - "Compare this month to last month"
        - "Which bills are due soon?"
        """)


def show_agent_status():
    """Display the status of all agents"""
    supervisor = get_supervisor()
    
    if supervisor:
        status = supervisor.get_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status.get('agent1_available'):
                st.success("✅ Agent 1: Data Processor")
            else:
                st.error("❌ Agent 1: Unavailable")
        
        with col2:
            if status.get('agent2_available'):
                st.success("✅ Agent 2: Financial Analyst")
            else:
                st.error("❌ Agent 2: Unavailable")
        
        with col3:
            if status.get('query_agent_available'):
                st.success("✅ Query Agent")
            else:
                st.warning("⚠️ Query Agent: Not loaded")
        
        st.caption(f"Last checked: {status.get('timestamp', 'Unknown')}")
    else:
        st.error("Supervisor not available")


# =========================================================================
# RESULT DISPLAY FUNCTIONS
# =========================================================================

def display_recommendations_result(result: dict):
    """Display recommendations in a nice format"""
    if result.get('status') == 'error':
        st.error(f"❌ {result.get('message', 'Unknown error')}")
        return
    
    # Handle different result formats
    if result.get('agent') == 'financial_analyst' or 'total_recommendations' in result:
        total_recs = result.get('total_recommendations', 0)
        monthly_savings = result.get('potential_monthly_savings', 0)
        annual_savings = result.get('potential_annual_savings', 0)
        
        st.success(f"✅ Generated {total_recs} recommendations!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Recommendations", total_recs)
        with col2:
            st.metric("Monthly Savings", f"${monthly_savings:.2f}")
        with col3:
            st.metric("Annual Savings", f"${annual_savings:.2f}")
        
        # Display individual recommendations
        recs = result.get('recommendations', [])
        if recs:
            st.markdown("### 🎯 Top Recommendations")
            
            sorted_recs = sorted(recs, key=lambda x: (x.get('priority', 5), -x.get('potential_savings', 0)))
            
            for i, rec in enumerate(sorted_recs[:5], 1):
                priority = rec.get('priority', 3)
                emoji = "🔴" if priority == 1 else "🟡" if priority == 2 else "🟢"
                
                with st.expander(f"{emoji} {rec.get('title', 'Recommendation')}", expanded=(i <= 2)):
                    st.markdown(f"**{rec.get('description', '')}**")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Monthly", f"${rec.get('potential_savings', 0):.2f}")
                    with c2:
                        st.metric("Annual", f"${rec.get('annual_savings', 0):.2f}")
                    with c3:
                        st.metric("Priority", priority)
    else:
        # Generic success message
        st.success("✅ " + result.get('message', 'Recommendations generated'))
        if result.get('data'):
            st.json(result['data'])


def display_summary_result(result: dict):
    """Display daily summary in a nice format"""
    if result.get('status') == 'error':
        st.error(f"❌ {result.get('message', 'Unknown error')}")
        return
    
    if result.get('status') == 'success':
        st.success(f"✅ Summary for {result.get('summary_date', 'today')}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Spending", f"${result.get('total_spent', 0):.2f}")
        with col2:
            st.metric("Transactions", result.get('transaction_count', 0))
        with col3:
            st.metric("Top Category", result.get('top_category', 'N/A'))
        with col4:
            subs = result.get('subscriptions_charged', [])
            st.metric("Subscriptions", len(subs) if isinstance(subs, list) else 0)
        
        # Summary text
        if result.get('summary_text'):
            st.markdown("### 📄 Report")
            st.text(result['summary_text'])
        
        # Spending breakdown chart
        if result.get('spending_by_category'):
            st.markdown("### 💰 Breakdown")
            import pandas as pd
            df = pd.DataFrame([
                {'Category': cat, 'Amount': amt} 
                for cat, amt in result['spending_by_category'].items()
            ]).sort_values('Amount', ascending=False)
            st.bar_chart(df.set_index('Category'))
        
        # Budget alerts
        if result.get('budget_alerts'):
            st.markdown("### ⚠️ Alerts")
            for alert in result['budget_alerts']:
                st.warning(alert)


def display_pipeline_result(result: dict):
    """Display full pipeline results"""
    status = result.get('status', 'unknown')
    
    if status == 'success':
        st.success("✅ Full pipeline completed successfully!")
    elif status == 'partial':
        st.warning("⚠️ Pipeline completed with some errors")
    else:
        st.error("❌ Pipeline failed")
    
    # Show message
    if result.get('message'):
        st.markdown("### Summary")
        st.text(result['message'])
    
    # Show stages
    stages = result.get('stages', {})
    
    if stages.get('data_processing'):
        with st.expander("📥 Stage 1: Data Processing", expanded=False):
            dp = stages['data_processing']
            if dp.get('status') == 'success':
                st.success("✅ Transactions processed")
            else:
                st.error(f"❌ {dp.get('message', 'Failed')}")
    
    if stages.get('recommendations'):
        with st.expander("💡 Stage 2: Recommendations", expanded=True):
            display_recommendations_result(stages['recommendations'])
    
    # Show errors
    if result.get('errors'):
        st.markdown("### ❌ Errors")
        for error in result['errors']:
            st.error(error)


def display_chat_response(result: dict):
    """Display chat response from Supervisor"""
    st.markdown("### 🤖 AI Response")
    
    if result.get('status') == 'error':
        st.error(f"❌ {result.get('message', 'Unknown error')}")
        if result.get('suggestion'):
            st.info(f"💡 Suggestion: {result['suggestion']}")
        return
    
    if result.get('status') == 'help':
        st.info(result.get('message', 'How can I help?'))
        
        if result.get('capabilities'):
            st.markdown("**I can help with:**")
            for cap in result['capabilities']:
                st.markdown(f"• {cap}")
        
        if result.get('examples'):
            st.markdown("**Try saying:**")
            for ex in result['examples']:
                st.markdown(f"• _{ex}_")
        return
    
    # Success responses
    if result.get('answer'):
        st.success("✅ Here's what I found:")
        st.markdown(result['answer'])
        
        if result.get('cached'):
            st.caption("💡 Cached answer")
        
        if result.get('data'):
            with st.expander("📊 Raw Data"):
                st.json(result['data'])
    
    elif result.get('message'):
        st.success("✅ " + result['message'])
    
    elif result.get('status') == 'success':
        st.success("✅ Done!")
        
        # Check for specific result types
        if 'total_recommendations' in result:
            display_recommendations_result(result)
        elif 'total_spent' in result:
            display_summary_result(result)
        elif 'stages' in result:
            display_pipeline_result(result)
        else:
            st.json(result)
    
    else:
        # Fallback - show raw result
        st.json(result)
