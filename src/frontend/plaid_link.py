import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Smart Expense Analyzer", layout="wide")

st.title("💰 Smart Expense Analyzer")
st.markdown("AI-Powered Budget Optimization")

# Load transactions from JSON
try:
    with open('data/plaid_transactions.json', 'r') as f:
        transactions = json.load(f)
    
    st.success(f"✅ Loaded {len(transactions)} transactions from Plaid")
    
    # Convert to DataFrame
    data = []
    for t in transactions:
        data.append({
            'Date': t['date'],
            'Merchant': t['name'],
            'Amount': t['amount'],
            'Category': t['category'][0] if t.get('category') else 'Uncategorized'
        })
    
    df = pd.DataFrame(data)
    
    # Summary metrics
    st.header("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", len(df))
    with col2:
        st.metric("Total Spending", f"${df['Amount'].sum():,.2f}")
    with col3:
        st.metric("Average Transaction", f"${df['Amount'].mean():.2f}")
    with col4:
        st.metric("Categories", df['Category'].nunique())
    
    # Category breakdown
    st.header("📈 Spending by Category")
    category_totals = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    st.bar_chart(category_totals)
    
    # Recent transactions
    st.header("📝 Recent Transactions")
    st.dataframe(
        df.sort_values('Date', ascending=False).head(50),
        use_container_width=True,
        height=400
    )
    
    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download All Transactions (CSV)",
        data=csv,
        file_name="transactions.csv",
        mime="text/csv"
    )
    
except FileNotFoundError:
    st.error("❌ No transaction data found!")
    st.info("Run the Plaid connection flow first to fetch transactions.")
    
    if st.button("🔗 Go to Plaid Connection"):
        st.switch_page("plaid_link.py")