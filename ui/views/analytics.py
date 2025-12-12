"""Analytics page for Smart Expense Analyzer POC"""
import streamlit as st
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client

def _fetch_category_spending(user_id: str):
    """Fetch category spending from API"""
    api = get_api_client()
    print("[ANALYTICS] Calling API: /api/analytics/spending-by-category")
    data = api.get_spending_by_category()
    print(f"[ANALYTICS] Received category spending data: {len(data)} categories")
    return data

def _fetch_monthly_trends(user_id: str, months: int = 12):
    """Fetch monthly trends from API"""
    api = get_api_client()
    print("[ANALYTICS] Calling API: /api/analytics/monthly-trends")
    data = api.get_monthly_trends(months=months)
    print(f"[ANALYTICS] Received monthly trends: {len(data)} months")
    return data

def _fetch_all_transactions(user_id: str, limit: int = 10000):
    """Fetch all transactions for analysis from API"""
    api = get_api_client()
    print("[ANALYTICS] Calling API: /api/transactions")
    transactions = api.get_transactions(limit=limit)
    print(f"[ANALYTICS] Received {len(transactions)} transactions")
    return transactions

def show_analytics(current_user: Dict):
    """Show the analytics page"""
    user_id = current_user.get('id')
    cache_key = f"analytics_data_{user_id}"
    
    print(f"[ANALYTICS] Loading analytics for user: {user_id}")
    
    # Skip API calls if we're in a file upload operation
    if st.session_state.get('skip_api_calls', False):
        print("[ANALYTICS] Skipping API call (file operation in progress)")
        if cache_key in st.session_state and st.session_state[cache_key]:
            data = st.session_state[cache_key]
            category_spending = data.get('category_spending')
            monthly_trends = data.get('monthly_trends')
            all_transactions = data.get('all_transactions')
        else:
            st.info("Loading...")
            return
    
    st.header("📈 Spending Analytics")
    
    # Manual refresh button
    col1, col2 = st.columns([1, 10])
    with col1:
        refresh_key = f"refresh_{cache_key}"
        if st.button("🔄", help="Refresh analytics", key="refresh_analytics"):
            st.session_state[refresh_key] = True
    
    try:
        # Check if we need to fetch (no data or refresh requested)
        refresh_requested = st.session_state.get(f"refresh_{cache_key}", False)
        
        if cache_key not in st.session_state or st.session_state[cache_key] is None or refresh_requested:
            # Fetch from API
            category_spending = _fetch_category_spending(user_id)
            monthly_trends = _fetch_monthly_trends(user_id, months=12)
            all_transactions = _fetch_all_transactions(user_id, limit=10000)
            
            # Store in session state
            st.session_state[cache_key] = {
                'category_spending': category_spending,
                'monthly_trends': monthly_trends,
                'all_transactions': all_transactions
            }
            st.session_state[f"refresh_{cache_key}"] = False
        else:
            # Use cached data from session state
            data = st.session_state[cache_key]
            category_spending = data.get('category_spending')
            monthly_trends = data.get('monthly_trends')
            all_transactions = data.get('all_transactions')
            print("[ANALYTICS] Using cached data from session state")
        
        if not all_transactions:
            st.info("No transactions found. Sync your accounts to see analytics.")
            st.markdown("👉 Go to the **Connect Bank** tab to add your first account.")
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
        
        # Category Analysis - Use API data if available, otherwise calculate locally
        st.markdown("---")
        st.subheader("🏷️ Spending by Category")
        
        if category_spending:
            print("[ANALYTICS] Using API category data")
            display_category_analysis_from_api(category_spending, total_spent)
        else:
            print("[ANALYTICS] Calculating category data locally")
            category_data = analyze_categories(filtered_txns, total_spent)
            if category_data:
                display_category_analysis(category_data)
        
        # Merchant Analysis
        st.markdown("---")
        st.subheader("🏪 Top Merchants")
        
        merchant_data = analyze_merchants(filtered_txns)
        if merchant_data:
            display_merchant_analysis(merchant_data)
        
        # Trend Analysis - Use API monthly trends
        st.markdown("---")
        st.subheader("📊 Spending Trends")
        
        if monthly_trends:
            print("[ANALYTICS] Using API monthly trends")
            display_monthly_trends(monthly_trends)
        else:
            print("[ANALYTICS] Calculating trends locally")
            display_spending_trend(filtered_txns)
        
        # Insights
        st.markdown("---")
        st.subheader("💡 Smart Insights")
        
        generate_insights(filtered_txns, total_spent, total_income)
        
        print("[ANALYTICS] Analytics page loaded successfully")
        
    except Exception as e:
        print(f"[ANALYTICS] Error loading analytics: {str(e)}")
        st.error(f"Error loading analytics: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_category_analysis_from_api(category_spending: Dict, total_spent: float):
    """Display category analysis from API data"""
    # Convert dict to list for display
    category_data = [
        {"Category": cat, "Amount": amount, "Count": 0, "Average": amount}  # Add Count and Average for compatibility
        for cat, amount in sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Calculate percentages
    for item in category_data:
        item["Percentage"] = (item["Amount"] / total_spent * 100) if total_spent > 0 else 0
    
    display_category_analysis(category_data[:10])  # Top 10


def display_monthly_trends(monthly_trends: Dict):
    """Display monthly trends from API"""
    # Convert to DataFrame
    months = sorted(monthly_trends.keys())
    data = {
        "Month": months,
        "Income": [monthly_trends[m].get("income", 0) for m in months],
        "Expenses": [monthly_trends[m].get("expenses", 0) for m in months]
    }
    
    df = pd.DataFrame(data)
    df["Net"] = df["Income"] - df["Expenses"]
    
    # Display chart
    st.line_chart(df.set_index("Month")[["Income", "Expenses", "Net"]])
    
    # Stats
    if len(months) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_expenses = df["Expenses"].mean()
            st.metric("Avg Monthly Expenses", f"${avg_expenses:.2f}")
        with col2:
            avg_income = df["Income"].mean()
            st.metric("Avg Monthly Income", f"${avg_income:.2f}")
        with col3:
            avg_net = df["Net"].mean()
            st.metric("Avg Monthly Net", f"${avg_net:.2f}")


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
        use_container_width=True,
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
            st.metric("", f"${item['Amount']:.2f}")


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
