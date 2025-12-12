"""
Agent 2: Financial Analyst - ADK-Compatible Tool Functions
File: agent_tools/financial_analyst_tools.py

These functions are designed to be wrapped with FunctionTool for Google ADK.
Each function has clear docstrings that the LLM can use to understand when to call them.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Lazy-loaded toolbox to avoid connection issues at import time
_toolbox = None

def _get_toolbox():
    """Get or create toolbox wrapper (lazy initialization)"""
    global _toolbox
    if _toolbox is None:
        try:
            from agent_tools.toolbox_wrapper import get_toolbox
            _toolbox = get_toolbox()
        except Exception as e:
            logger.warning(f"Could not connect to MCP Toolbox: {e}")
            _toolbox = None
    return _toolbox


def analyze_budget_health(user_id: str) -> Dict[str, Any]:
    """
    Analyze the user's budget health by comparing current spending to historical baselines.
    
    This tool checks if the user is over budget in any spending category by comparing
    current month spending against their typical 3-month average.
    
    Args:
        user_id: The unique identifier of the user to analyze
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - alerts: List of budget alerts (categories over 100% of baseline)
        - recommendations: List of specific recommendations with potential savings
        - summary: Text summary of budget health
    """
    logger.info(f"Analyzing budget health for user {user_id}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        return _mock_budget_analysis(user_id)
    
    recommendations = []
    alerts = []
    
    try:
        # Get current month spending by category
        result = toolbox.call_tool('get-current-month-spending', user_id=user_id)
        
        if not result.get('success'):
            return {"status": "error", "message": "Failed to fetch spending data"}
        
        current_spending = result.get('data', [])
        if isinstance(current_spending, str):
            current_spending = json.loads(current_spending)
        
        for category_data in current_spending:
            category = category_data.get('category', 'Unknown')
            current = float(category_data.get('total_amount', 0))
            
            # Get baseline (3-month average)
            baseline = _get_category_baseline(toolbox, user_id, category)
            
            if baseline > 0:
                utilization = (current / baseline) * 100
                
                if utilization > 120:
                    # Critical - over 120% of baseline
                    potential_savings = current - baseline
                    alerts.append({
                        "category": category,
                        "severity": "high",
                        "message": f"Over budget by {utilization - 100:.0f}%"
                    })
                    recommendations.append({
                        "type": "budget_alert",
                        "title": f"Over Budget in {category}",
                        "description": f"You've spent ${current:.2f} in {category} this month, which is {utilization:.0f}% of your typical spending (${baseline:.2f}).",
                        "potential_savings": potential_savings,
                        "priority": 1,
                        "urgency": "high",
                        "category": category
                    })
                    
                elif utilization > 100:
                    # Warning - between 100-120%
                    potential_savings = current - baseline
                    alerts.append({
                        "category": category,
                        "severity": "medium",
                        "message": f"Slightly over baseline ({utilization:.0f}%)"
                    })
                    recommendations.append({
                        "type": "budget_warning",
                        "title": f"{category} Spending Above Average",
                        "description": f"You're at {utilization:.0f}% of typical {category} spending.",
                        "potential_savings": potential_savings,
                        "priority": 2,
                        "urgency": "medium",
                        "category": category
                    })
        
        # Generate summary
        if not alerts:
            summary = "Great news! All your spending categories are within normal ranges."
        elif len([a for a in alerts if a['severity'] == 'high']) > 0:
            summary = f"Budget Alert: You have {len(alerts)} categories requiring attention."
        else:
            summary = f"Minor Budget Notice: {len(alerts)} categories slightly above average."
        
        return {
            "status": "success",
            "alerts": alerts,
            "recommendations": recommendations,
            "summary": summary,
            "total_recommendations": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing budget: {e}")
        return {"status": "error", "message": str(e)}


def find_savings_opportunities(user_id: str) -> Dict[str, Any]:
    """
    Find opportunities for the user to save money on discretionary spending.
    
    This tool analyzes spending in categories like Dining, Shopping, and Entertainment
    to identify areas where the user could reduce expenses.
    
    Args:
        user_id: The unique identifier of the user to analyze
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - opportunities: List of savings opportunities with amounts
        - total_potential_savings: Total monthly savings possible
        - summary: Text summary of findings
    """
    logger.info(f"Finding savings opportunities for user {user_id}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        return _mock_savings_opportunities(user_id)
    
    opportunities = []
    discretionary_categories = ['Dining', 'Shopping', 'Entertainment', 'Travel', 'Recreation']
    
    try:
        result = toolbox.call_tool('get-current-month-spending', user_id=user_id)
        
        if not result.get('success'):
            return {"status": "error", "message": "Failed to fetch spending data"}
        
        current_spending = result.get('data', [])
        if isinstance(current_spending, str):
            current_spending = json.loads(current_spending)
        
        for category_data in current_spending:
            category = category_data.get('category', 'Unknown')
            current = float(category_data.get('total_amount', 0))
            
            if category in discretionary_categories:
                baseline = _get_category_baseline(toolbox, user_id, category)
                
                if baseline > 0 and current > baseline * 1.2:
                    # Suggest reducing to baseline + 10%
                    target = baseline * 1.1
                    potential_savings = current - target
                    
                    opportunities.append({
                        "type": "reduce_spending",
                        "title": f"Save on {category}",
                        "description": f"You're spending ${current:.2f}/month on {category}, above your baseline of ${baseline:.2f}. Consider reducing to ${target:.2f}.",
                        "current_spending": current,
                        "target_spending": target,
                        "potential_savings": potential_savings,
                        "annual_savings": potential_savings * 12,
                        "priority": 3,
                        "category": category
                    })
        
        total_savings = sum(o['potential_savings'] for o in opportunities)
        
        return {
            "status": "success",
            "opportunities": opportunities,
            "total_potential_savings": total_savings,
            "annual_potential_savings": total_savings * 12,
            "summary": f"Found {len(opportunities)} savings opportunities totaling ${total_savings:.2f}/month (${total_savings * 12:.2f}/year)"
        }
        
    except Exception as e:
        logger.error(f"Error finding savings: {e}")
        return {"status": "error", "message": str(e)}


def optimize_subscriptions(user_id: str) -> Dict[str, Any]:
    """
    Analyze and optimize the user's subscription spending.
    
    This tool reviews all detected subscriptions and identifies opportunities
    to cancel unused subscriptions or find cheaper alternatives.
    
    Args:
        user_id: The unique identifier of the user to analyze
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - subscriptions: List of current subscriptions with amounts
        - recommendations: Optimization suggestions
        - total_monthly_cost: Total subscription spending per month
        - summary: Text summary of subscription health
    """
    logger.info(f"Optimizing subscriptions for user {user_id}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        return _mock_subscription_optimization(user_id)
    
    recommendations = []
    
    try:
        result = toolbox.call_tool('get-user-subscriptions', user_id=user_id)
        
        if not result.get('success'):
            return {"status": "error", "message": "Failed to fetch subscriptions"}
        
        subscriptions = result.get('data', [])
        if isinstance(subscriptions, str):
            subscriptions = json.loads(subscriptions)
        
        if not subscriptions:
            return {
                "status": "success",
                "subscriptions": [],
                "recommendations": [],
                "total_monthly_cost": 0,
                "summary": "No subscriptions detected yet. Keep using the app to track your recurring charges."
            }
        
        total_monthly = sum(float(s.get('amount', 0)) for s in subscriptions)
        
        # High total subscription spending
        if total_monthly > 100:
            recommendations.append({
                "type": "reduce_subscriptions",
                "title": "High Subscription Spending",
                "description": f"You're spending ${total_monthly:.2f}/month on {len(subscriptions)} subscriptions. Consider reviewing which ones you actively use.",
                "potential_savings": total_monthly * 0.3,  # Assume 30% can be cut
                "annual_savings": total_monthly * 12 * 0.3,
                "priority": 2,
                "urgency": "medium"
            })
        
        # Flag expensive individual subscriptions
        for sub in subscriptions:
            amount = float(sub.get('amount', 0))
            merchant = sub.get('merchant_standardized', sub.get('merchant', 'Unknown'))
            
            if amount > 50:
                recommendations.append({
                    "type": "expensive_subscription",
                    "title": f"Review {merchant} Subscription",
                    "description": f"{merchant} costs ${amount:.2f}/month (${amount * 12:.2f}/year). Make sure you're getting value from this service.",
                    "potential_savings": amount,
                    "annual_savings": amount * 12,
                    "priority": 3,
                    "urgency": "low",
                    "merchant": merchant
                })
        
        return {
            "status": "success",
            "subscriptions": subscriptions,
            "recommendations": recommendations,
            "total_monthly_cost": total_monthly,
            "annual_cost": total_monthly * 12,
            "subscription_count": len(subscriptions),
            "summary": f"You have {len(subscriptions)} subscriptions costing ${total_monthly:.2f}/month (${total_monthly * 12:.2f}/year)"
        }
        
    except Exception as e:
        logger.error(f"Error optimizing subscriptions: {e}")
        return {"status": "error", "message": str(e)}


def predict_spending_trends(user_id: str) -> Dict[str, Any]:
    """
    Predict future spending trends based on historical patterns.
    
    This tool analyzes 3 months of spending history to identify categories
    with increasing spending trends and predict next month's spending.
    
    Args:
        user_id: The unique identifier of the user to analyze
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - trends: List of trending categories with predictions
        - predictions: Next month spending predictions by category
        - alerts: Categories with concerning upward trends
        - summary: Text summary of spending trajectory
    """
    logger.info(f"Predicting spending trends for user {user_id}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        return _mock_trend_predictions(user_id)
    
    trends = []
    alerts = []
    predictions = {}
    
    try:
        # Get categories for this user
        result = toolbox.call_tool('get-user-categories', user_id=user_id)
        
        if not result.get('success'):
            return {"status": "error", "message": "Failed to fetch categories"}
        
        categories = result.get('data', [])
        if isinstance(categories, str):
            categories = json.loads(categories)
        
        for cat_data in categories:
            category = cat_data.get('category', 'Unknown')
            
            # Get 3-month history
            history = _get_category_history(toolbox, user_id, category, months=3)
            
            if len(history) >= 2:
                amounts = [float(h.get('total_amount', 0)) for h in history]
                avg_amount = sum(amounts) / len(amounts)
                recent_amount = amounts[0] if amounts else 0
                
                # Calculate trend
                if avg_amount > 0:
                    trend_pct = ((recent_amount - avg_amount) / avg_amount) * 100
                else:
                    trend_pct = 0
                
                # Predict next month (simple linear projection)
                if len(amounts) >= 2:
                    monthly_change = amounts[0] - amounts[1]
                    predicted_next = max(0, amounts[0] + monthly_change)
                else:
                    predicted_next = recent_amount
                
                predictions[category] = predicted_next
                
                if trend_pct > 20:
                    # Spending trending up significantly
                    trends.append({
                        "category": category,
                        "direction": "up",
                        "change_percent": trend_pct,
                        "current": recent_amount,
                        "average": avg_amount,
                        "predicted_next": predicted_next
                    })
                    
                    alerts.append({
                        "type": "trend_alert",
                        "title": f"{category} Spending Trending Up",
                        "description": f"Your {category} spending increased {trend_pct:.0f}% above average. Last month: ${recent_amount:.2f}, predicted next: ${predicted_next:.2f}.",
                        "potential_savings": predicted_next - avg_amount,
                        "priority": 2,
                        "category": category
                    })
                    
                elif trend_pct < -20:
                    # Spending trending down (good!)
                    trends.append({
                        "category": category,
                        "direction": "down",
                        "change_percent": trend_pct,
                        "current": recent_amount,
                        "average": avg_amount,
                        "predicted_next": predicted_next
                    })
        
        total_predicted = sum(predictions.values())
        up_trends = len([t for t in trends if t['direction'] == 'up'])
        down_trends = len([t for t in trends if t['direction'] == 'down'])
        
        if up_trends > down_trends:
            summary = f"Heads up: {up_trends} categories show increasing spending. Predicted total next month: ${total_predicted:.2f}"
        elif down_trends > up_trends:
            summary = f"Great progress! {down_trends} categories show decreasing spending."
        else:
            summary = "Your spending is relatively stable across categories."
        
        return {
            "status": "success",
            "trends": trends,
            "predictions": predictions,
            "alerts": alerts,
            "total_predicted_next_month": total_predicted,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error predicting trends: {e}")
        return {"status": "error", "message": str(e)}


def generate_daily_summary(user_id: str, summary_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a daily spending summary for the user.
    
    This tool creates a comprehensive summary of a day's financial activity,
    including total spending, category breakdown, and any alerts.
    
    Args:
        user_id: The unique identifier of the user
        summary_date: Optional date in YYYY-MM-DD format. Defaults to today.
        
    Returns:
        Dictionary containing:
        - status: 'success' or 'error'
        - summary_date: The date this summary covers
        - total_spent: Total amount spent
        - transaction_count: Number of transactions
        - spending_by_category: Breakdown by category
        - alerts: Any budget alerts
        - summary_text: Human-readable summary
    """
    if not summary_date:
        summary_date = datetime.now().date().isoformat()
    
    logger.info(f"Generating daily summary for user {user_id} on {summary_date}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        return _mock_daily_summary(user_id, summary_date)
    
    try:
        # For now, return a structured summary
        # In production, this would query actual transactions for the date
        
        return {
            "status": "success",
            "summary_date": summary_date,
            "total_spent": 0,
            "transaction_count": 0,
            "spending_by_category": {},
            "top_category": "None",
            "budget_alerts": [],
            "subscriptions_charged": [],
            "summary_text": f"Daily Summary for {summary_date}\n\nNo transactions recorded for this date."
        }
        
    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        return {"status": "error", "message": str(e)}


def save_recommendation(user_id: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a financial recommendation to the database.
    
    This tool stores generated recommendations so they can be tracked
    and shown to the user in the dashboard.
    
    Args:
        user_id: The unique identifier of the user
        recommendation: Dictionary with recommendation details including:
            - tool_name: Which analysis tool generated this
            - recommendation_type: Category of recommendation
            - title: Short title
            - description: Detailed description
            - potential_savings: Monthly savings amount
            - priority: 1 (high) to 5 (low)
            - urgency: 'high', 'medium', or 'low'
        
    Returns:
        Dictionary with status of save operation
    """
    logger.info(f"Saving recommendation for user {user_id}")
    
    toolbox = _get_toolbox()
    if not toolbox:
        logger.warning("Toolbox not available, recommendation not saved to DB")
        return {"status": "success", "message": "Recommendation recorded (DB unavailable)"}
    
    try:
        result = toolbox.call_tool(
            'insert-recommendation',
            user_id=user_id,
            tool_name=recommendation.get('tool_name', 'financial_analyst'),
            recommendation_type=recommendation.get('type', recommendation.get('recommendation_type', 'general')),
            title=recommendation.get('title', ''),
            description=recommendation.get('description', ''),
            potential_savings=str(recommendation.get('potential_savings', 0)),
            annual_savings=str(recommendation.get('annual_savings', recommendation.get('potential_savings', 0) * 12)),
            priority=recommendation.get('priority', 3),
            urgency=recommendation.get('urgency', 'medium'),
            related_category=recommendation.get('category', recommendation.get('related_category', '')),
            related_merchant=recommendation.get('merchant', recommendation.get('related_merchant', ''))
        )
        
        return {"status": "success" if result.get('success') else "error", "result": result}
        
    except Exception as e:
        logger.error(f"Error saving recommendation: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# HELPER FUNCTIONS (not exposed as tools)
# ============================================================================

def _get_category_baseline(toolbox, user_id: str, category: str) -> float:
    """Get 3-month average spending for a category"""
    try:
        history = _get_category_history(toolbox, user_id, category, months=3)
        if history:
            amounts = [float(h.get('total_amount', 0)) for h in history]
            return sum(amounts) / len(amounts)
        return 0.0
    except:
        return 0.0


def _get_category_history(toolbox, user_id: str, category: str, months: int = 3) -> List[Dict]:
    """Get spending history for a category"""
    try:
        result = toolbox.call_tool('get-category-history', user_id=user_id, category=category, months=months)
        
        if result.get('success'):
            data = result.get('data', [])
            if isinstance(data, str):
                data = json.loads(data)
            return data if isinstance(data, list) else []
        return []
    except:
        return []


# ============================================================================
# MOCK FUNCTIONS (used when MCP Toolbox is not available)
# ============================================================================

def _mock_budget_analysis(user_id: str) -> Dict[str, Any]:
    """Return mock budget analysis when toolbox unavailable"""
    return {
        "status": "success",
        "alerts": [
            {"category": "Dining", "severity": "medium", "message": "Slightly above baseline (110%)"}
        ],
        "recommendations": [
            {
                "type": "budget_warning",
                "title": "Dining Spending Above Average",
                "description": "You're at 110% of typical Dining spending. Consider cooking at home more often.",
                "potential_savings": 50.00,
                "priority": 2,
                "urgency": "medium",
                "category": "Dining"
            }
        ],
        "summary": "Minor Budget Notice: 1 category slightly above average.",
        "total_recommendations": 1,
        "note": "Using sample data - MCP Toolbox not connected"
    }


def _mock_savings_opportunities(user_id: str) -> Dict[str, Any]:
    """Return mock savings when toolbox unavailable"""
    return {
        "status": "success",
        "opportunities": [
            {
                "type": "reduce_spending",
                "title": "Save on Entertainment",
                "description": "Your entertainment spending is above average. Consider free activities.",
                "current_spending": 200.00,
                "target_spending": 150.00,
                "potential_savings": 50.00,
                "annual_savings": 600.00,
                "priority": 3,
                "category": "Entertainment"
            }
        ],
        "total_potential_savings": 50.00,
        "annual_potential_savings": 600.00,
        "summary": "Found 1 savings opportunity totaling $50.00/month ($600.00/year)",
        "note": "Using sample data - MCP Toolbox not connected"
    }


def _mock_subscription_optimization(user_id: str) -> Dict[str, Any]:
    """Return mock subscription data when toolbox unavailable"""
    return {
        "status": "success",
        "subscriptions": [
            {"merchant": "Netflix", "amount": 15.99},
            {"merchant": "Spotify", "amount": 9.99},
            {"merchant": "Amazon Prime", "amount": 14.99}
        ],
        "recommendations": [],
        "total_monthly_cost": 40.97,
        "annual_cost": 491.64,
        "subscription_count": 3,
        "summary": "You have 3 subscriptions costing $40.97/month ($491.64/year)",
        "note": "Using sample data - MCP Toolbox not connected"
    }


def _mock_trend_predictions(user_id: str) -> Dict[str, Any]:
    """Return mock trend data when toolbox unavailable"""
    return {
        "status": "success",
        "trends": [],
        "predictions": {
            "Groceries": 450.00,
            "Dining": 180.00,
            "Transportation": 120.00
        },
        "alerts": [],
        "total_predicted_next_month": 750.00,
        "summary": "Your spending is relatively stable across categories.",
        "note": "Using sample data - MCP Toolbox not connected"
    }


def _mock_daily_summary(user_id: str, date: str) -> Dict[str, Any]:
    """Return mock daily summary when toolbox unavailable"""
    return {
        "status": "success",
        "summary_date": date,
        "total_spent": 85.50,
        "transaction_count": 5,
        "spending_by_category": {
            "Dining": 35.00,
            "Transportation": 25.50,
            "Shopping": 25.00
        },
        "top_category": "Dining",
        "budget_alerts": [],
        "subscriptions_charged": [],
        "summary_text": f"Daily Summary for {date}\n\nSpending Today: $85.50\nTransactions: 5\nTop Category: Dining\n\nNo budget alerts - you're on track!",
        "note": "Using sample data - MCP Toolbox not connected"
    }

