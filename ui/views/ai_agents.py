"""
AI Agents View - With Query Support and Frequent Questions
File: views/ai_agents.py
"""

import streamlit as st
import json
from datetime import datetime


def show_ai_agents(db, current_user):
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
            generate_recommendations(user_id)
    
    with col2:
        st.subheader("📊 Daily Summary")
        if st.button("📈 Generate Report", use_container_width=True, type="primary"):
            generate_daily_summary(user_id)
    
    st.markdown("---")
    
    show_frequent_questions(user_id)
    
    st.markdown("---")
    
    st.subheader("💬 Chat with AI")
    show_agent_chat(user_id)


def generate_recommendations(user_id: str):
    with st.spinner("🤖 Analyzing..."):
        try:
            from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
            
            agent2 = FinancialAnalystLLMAgent()
            result = agent2.generate_recommendations(user_id)
            
            if result['status'] == 'success':
                st.success(f"✅ {result['total_recommendations']} recommendations!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Recommendations", result['total_recommendations'])
                with col2:
                    st.metric("Monthly Savings", f"${result.get('potential_monthly_savings', 0):.2f}")
                with col3:
                    st.metric("Annual Savings", f"${result.get('potential_annual_savings', 0):.2f}")
                
                st.markdown("### 🎯 Top Recommendations")
                
                recs = result.get('recommendations', [])
                sorted_recs = sorted(recs, key=lambda x: (x['priority'], -x['potential_savings']))
                
                for i, rec in enumerate(sorted_recs[:5], 1):
                    emoji = "🔴" if rec['priority'] == 1 else "🟡" if rec['priority'] == 2 else "🟢"
                    
                    with st.expander(f"{emoji} {rec['title']}", expanded=(i <= 2)):
                        st.markdown(f"**{rec['description']}**")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Monthly", f"${rec['potential_savings']:.2f}")
                        with col2:
                            st.metric("Annual", f"${rec['annual_savings']:.2f}")
                        with col3:
                            st.metric("Priority", f"{rec['priority']}")
        
        except Exception as e:
            st.error(f"❌ {str(e)}")


def generate_daily_summary(user_id: str):
    summary_date = st.date_input("Date:", value=datetime.now().date(), max_value=datetime.now().date())
    
    with st.spinner("🤖 Creating summary..."):
        try:
            from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
            
            agent2 = FinancialAnalystLLMAgent()
            result = agent2.generate_daily_summary(user_id, summary_date.isoformat())
            
            if result['status'] == 'success':
                st.success(f"✅ Summary for {result['summary_date']}")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Spending", f"${result['total_spent']:.2f}")
                with col2:
                    st.metric("Transactions", result['transaction_count'])
                with col3:
                    st.metric("Top Category", result['top_category'])
                with col4:
                    subs_list = result.get('subscriptions_charged', [])
                    subs_count = len(subs_list) if isinstance(subs_list, list) else 0
                    st.metric("Subscriptions", subs_count)
                
                st.markdown("### 📄 Report")
                st.text(result['summary_text'])
                
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
        
        except Exception as e:
            st.error(f"❌ {str(e)}")


def show_frequent_questions(user_id: str):
    """Display frequently asked questions as buttons"""
    
    try:
        from mcp_toolbox.tools.query_agent import QueryAgent
        
        agent = QueryAgent()
        frequent = agent.get_frequent_questions(user_id, limit=5)
        
        if frequent:
            st.subheader("🔥 Frequent Questions")
            
            cols = st.columns(min(len(frequent), 3))
            
            for i, fq in enumerate(frequent):
                col_idx = i % 3
                
                with cols[col_idx]:
                    intent_names = {
                        'subscription_most_expensive': '💰 Top subscription',
                        'subscription_total_cost': '💵 Subscription cost',
                        'merchant_top_spending': '🏪 Top store',
                        'category_breakdown': '📊 Categories',
                        'bills_upcoming': '📅 Bills due',
                        'spending_anomalies': '⚠️ Unusual'
                    }
                    
                    button_text = intent_names.get(fq['intent'], fq['intent'])
                    
                    if st.button(button_text, key=f"freq_{i}", use_container_width=True):
                        st.session_state['auto_question'] = fq['example_question']
                        st.rerun()
    
    except:
        pass


def show_agent_chat(user_id: str):
    st.markdown("Ask your AI about your finances:")
    
    default_value = ""
    if 'auto_question' in st.session_state:
        default_value = st.session_state['auto_question']
        del st.session_state['auto_question']
    
    user_message = st.text_input(
        "Your message:",
        value=default_value,
        placeholder="e.g., 'Which subscription costs the most?'",
        key="agent_chat_input"
    )
    
    if st.button("💬 Send", use_container_width=True) or default_value:
        if user_message:
            with st.spinner("🤖 Thinking..."):
                try:
                    from mcp_toolbox.agents.root_orchestrator import RootOrchestratorAgent
                    
                    orchestrator = RootOrchestratorAgent()
                    
                    message = f"{user_message} for user {user_id}" if user_id not in user_message else user_message
                    
                    result = orchestrator.route(message)
                    
                    st.markdown("### 🤖 AI Response:")
                    
                    if isinstance(result, dict):
                        if result.get('answer'):
                            st.success("✅ Here's what I found:")
                            st.markdown(result['answer'])
                            
                            if result.get('cached'):
                                st.caption("💡 Cached answer")
                            
                            if result.get('data'):
                                with st.expander("📊 Data"):
                                    st.json(result['data'])
                        
                        elif result.get('status') == 'success':
                            st.success("✅ Done!")
                            st.json(result)
                        
                        elif result.get('status') == 'help':
                            st.info(result.get('message'))
                        
                        else:
                            st.error(result.get('message', 'Error'))
                    else:
                        st.info(result)
                
                except Exception as e:
                    st.error(f"❌ {str(e)}")
        else:
            st.warning("Enter a message")
    
    with st.expander("💡 Examples"):
        st.markdown("""
        **Subscriptions:** "Which subscription costs most?"
        **Spending:** "What's my biggest expense?"
        **Bills:** "Which bills are due soon?"
        **Analysis:** "Show unusual spending"
        **Compare:** "Compare this month to last month"
        **Actions:** "Generate recommendations" | "Show daily summary"
        """)