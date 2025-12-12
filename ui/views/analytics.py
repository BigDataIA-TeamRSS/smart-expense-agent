# """Analytics view for Smart Expense Analyzer"""

# import streamlit as st
# from typing import Dict
# from collections import defaultdict
# from datetime import datetime

# def show_analytics(db, current_user: Dict):
#     """Display spending analytics"""
    
#     st.header("📈 Analytics")
    
#     user_id = current_user["user_id"]
#     transactions = db.get_user_transactions(user_id)
    
#     if not transactions:
#         st.info("No transactions found. Connect your bank to see analytics!")
#         return
    
#     # Calculate spending by category
#     category_spending = defaultdict(float)
#     for txn in transactions:
#         amount = abs(txn.get('amount', 0))
#         category = txn.get('category', ['Other'])
#         if isinstance(category, list):
#             category = category[0] if category else 'Other'
#         category_spending[category] += amount
    
#     # Display summary
#     st.subheader("Spending by Category")
    
#     # Sort by amount
#     sorted_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
    
#     # Bar chart data
#     if sorted_categories:
#         categories = [cat for cat, _ in sorted_categories]
#         amounts = [amt for _, amt in sorted_categories]
        
#         # Create a simple bar chart
#         import pandas as pd
#         df = pd.DataFrame({
#             'Category': categories,
#             'Amount': amounts
#         })
        
#         st.bar_chart(df.set_index('Category'))
        
#         # Show table
#         st.markdown("---")
#         st.subheader("Breakdown")
        
#         total_spending = sum(amounts)
        
#         for category, amount in sorted_categories:
#             percentage = (amount / total_spending * 100) if total_spending > 0 else 0
#             col1, col2, col3 = st.columns([2, 1, 1])
#             with col1:
#                 st.write(f"**{category}**")
#             with col2:
#                 st.write(f"${amount:,.2f}")
#             with col3:
#                 st.write(f"{percentage:.1f}%")
    
#     # Summary metrics
#     st.markdown("---")
#     st.subheader("Summary")
    
#     total_spending = sum(abs(t.get('amount', 0)) for t in transactions)
#     avg_transaction = total_spending / len(transactions) if transactions else 0
    
#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Total Spending", f"${total_spending:,.2f}")
#     with col2:
#         st.metric("Total Transactions", len(transactions))
#     with col3:
#         st.metric("Average Transaction", f"${avg_transaction:.2f}")


"""Analytics page for Smart Expense Analyzer POC"""

import streamlit as st
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

def show_analytics(db, current_user: Dict):
    """Show the analytics page"""
    st.header("📈 Spending Analytics")
    
    accounts = db.get_user_accounts(current_user["id"])
    
    if not accounts:
        st.info("No accounts connected yet.")
        st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
        return
    
    # Get all transactions
    all_transactions = db.get_all_user_transactions(current_user["id"])
    
    if not all_transactions:
        st.info("No transactions found. Sync your accounts to see analytics.")
        return
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_period = st.selectbox(
            "📅 Analysis Period",
            ["Last 30 days", "Last 60 days", "Last 90 days", "This Year", "All Time"]
        )
    
    # Filter transactions based on period
    filtered_txns = filter_by_period(all_transactions, analysis_period)
    
    if not filtered_txns:
        st.warning("No transactions in the selected period")
        return
    
    with col2:
        st.metric("Transactions Analyzed", len(filtered_txns))
    
    # Calculate metrics
    total_spent = sum(t.get("amount", 0) for t in filtered_txns if t.get("amount", 0) > 0)
    total_income = sum(abs(t.get("amount", 0)) for t in filtered_txns if t.get("amount", 0) < 0)
    net_flow = total_income - total_spent
    
    # Display summary metrics
    st.markdown("---")
    st.subheader("💰 Financial Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Spent", f"${total_spent:,.2f}")
    
    with col2:
        st.metric("Total Income", f"${total_income:,.2f}")
    
    with col3:
        delta_color = "normal" if net_flow >= 0 else "inverse"
        st.metric("Net Cash Flow", f"${net_flow:,.2f}", delta_color=delta_color)
    
    with col4:
        days_in_period = len(set(t.get("date") for t in filtered_txns))
        avg_daily = total_spent / days_in_period if days_in_period > 0 else 0
        st.metric("Daily Average", f"${avg_daily:.2f}")
    
    # Category Analysis
    st.markdown("---")
    st.subheader("🏷️ Spending by Category")
    
    category_data = analyze_categories(filtered_txns, total_spent)
    if category_data:
        display_category_analysis(category_data)
    
    # Merchant Analysis
    st.markdown("---")
    st.subheader("🏪 Top Merchants")
    
    merchant_data = analyze_merchants(filtered_txns)
    if merchant_data:
        display_merchant_analysis(merchant_data)
    
    # Trend Analysis
    st.markdown("---")
    st.subheader("📊 Spending Trends")
    
    display_spending_trend(filtered_txns)
    
    # Insights
    st.markdown("---")
    st.subheader("💡 Smart Insights")
    
    generate_insights(filtered_txns, total_spent, total_income)

def filter_by_period(transactions: List[Dict], period: str) -> List[Dict]:
    """Filter transactions by selected period"""
    today = datetime.now()
    
    if period == "Last 30 days":
        cutoff = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif period == "Last 60 days":
        cutoff = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    elif period == "Last 90 days":
        cutoff = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    elif period == "This Year":
        cutoff = f"{today.year}-01-01"
    else:  # All Time
        cutoff = "1900-01-01"
    
    return [t for t in transactions if t.get("date", "") >= cutoff]

def analyze_categories(transactions: List[Dict], total_spent: float) -> List[Dict]:
    """Analyze spending by category"""
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    
    for txn in transactions:
        if txn.get("amount", 0) > 0:  # Only spending
            category = extract_category(txn)
            category_totals[category] += txn.get("amount", 0)
            category_counts[category] += 1
    
    if not category_totals:
        return []
    
    # Create category data
    category_data = []
    for category, amount in category_totals.items():
        category_data.append({
            "Category": category,
            "Amount": amount,
            "Count": category_counts[category],
            "Average": amount / category_counts[category],
            "Percentage": (amount / total_spent * 100) if total_spent > 0 else 0
        })
    
    return sorted(category_data, key=lambda x: x["Amount"], reverse=True)

def extract_category(txn: Dict) -> str:
    """Extract category from transaction"""
    category_raw = txn.get("category", ["Uncategorized"])
    
    if isinstance(category_raw, list) and category_raw:
        return category_raw[0] if category_raw else "Uncategorized"
    
    return str(category_raw) if category_raw else "Uncategorized"

def display_category_analysis(category_data: List[Dict]):
    """Display category analysis"""
    # Create DataFrame for display
    df = pd.DataFrame(category_data[:10])  # Top 10 categories
    
    # Format for display
    st.dataframe(
        df.style.format({
            "Amount": "${:.2f}",
            "Average": "${:.2f}",
            "Percentage": "{:.1f}%"
        }),
        hide_index=True
    )
    
    # Visual breakdown for top 5
    st.markdown("#### Top 5 Categories")
    for item in category_data[:5]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(min(item["Percentage"] / 100, 1.0))
            st.caption(f"{item['Category']} - {item['Count']} transactions")
        with col2:
            st.metric(label="Amount", value=f"${item['Amount']:.2f}", label_visibility="hidden")

def analyze_merchants(transactions: List[Dict]) -> List[Dict]:
    """Analyze spending by merchant"""
    merchant_totals = defaultdict(float)
    merchant_counts = defaultdict(int)
    
    for txn in transactions:
        if txn.get("amount", 0) > 0:  # Only spending
            merchant = txn.get("merchant_name") or txn.get("name", "Unknown")
            merchant_totals[merchant] += txn.get("amount", 0)
            merchant_counts[merchant] += 1
    
    if not merchant_totals:
        return []
    
    # Get top merchants
    top_merchants = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return [{
        "Merchant": m[0][:30],  # Truncate long names
        "Total": m[1],
        "Visits": merchant_counts[m[0]]
    } for m in top_merchants]

def display_merchant_analysis(merchant_data: List[Dict]):
    """Display merchant analysis"""
    for item in merchant_data[:5]:  # Show top 5
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.text(item["Merchant"])
        with col2:
            st.text(f"${item['Total']:.2f}")
        with col3:
            st.text(f"{item['Visits']} visits")

def display_spending_trend(transactions: List[Dict]):
    """Display spending trend chart"""
    # Group by date
    daily_spending = defaultdict(float)
    
    for txn in transactions:
        if txn.get("amount", 0) > 0:
            date = txn.get("date", "")
            daily_spending[date] += txn.get("amount", 0)
    
    if daily_spending:
        # Sort by date and get last 30 days
        sorted_days = sorted(daily_spending.items())[-30:]
        
        # Create DataFrame
        df = pd.DataFrame(sorted_days, columns=["Date", "Amount"])
        
        # Display chart
        st.bar_chart(df.set_index("Date"))
        
        # Stats
        col1, col2, col3 = st.columns(3)
        amounts = [d[1] for d in sorted_days]
        
        with col1:
            st.metric("Highest Day", f"${max(amounts):.2f}")
        with col2:
            st.metric("Lowest Day", f"${min(amounts):.2f}")
        with col3:
            st.metric("Average", f"${sum(amounts)/len(amounts):.2f}")

def generate_insights(transactions: List[Dict], total_spent: float, total_income: float):
    """Generate smart insights"""
    insights = []
    
    # Basic insights
    if transactions:
        spending_txns = [t for t in transactions if t.get("amount", 0) > 0]
        
        if spending_txns:
            avg_transaction = total_spent / len(spending_txns)
            insights.append(f"💳 Your average transaction is **${avg_transaction:.2f}**")
            
            # Find largest transaction
            largest = max(spending_txns, key=lambda x: x.get("amount", 0))
            insights.append(
                f"💸 Largest expense: **${largest['amount']:.2f}** at "
                f"{largest.get('merchant_name') or largest.get('name', 'Unknown')}"
            )
        
        # Income vs spending
        if total_income > 0:
            savings_rate = ((total_income - total_spent) / total_income) * 100
            if savings_rate > 0:
                insights.append(f"💰 You're saving **{savings_rate:.1f}%** of your income")
            else:
                insights.append(f"⚠️ You're spending **{abs(savings_rate):.1f}%** more than you earn")
    
    # Display insights
    for insight in insights:
        st.info(insight)