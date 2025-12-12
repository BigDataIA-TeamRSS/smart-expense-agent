"""
Agent 2: Financial Analyst
File: mcp_toolbox/tools/financial_analyst.py
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
from toolbox_core import ToolboxSyncClient
from dotenv import load_dotenv
import os
load_dotenv()
CLIENT_URL = os.getenv("CLIENT_URL", "https://toolbox-service-440584682160.us-central1.run.app")
class FinancialAnalystAgent:
    
    def __init__(self, toolbox_url: str = CLIENT_URL):
        print("Initializing Agent 2: Financial Analyst...")
        self.toolbox_client = ToolboxSyncClient(toolbox_url)
        
        try:
            self.tools = self.toolbox_client.load_toolset()
            print(f"   Loaded {len(self.tools)} tools")
        except Exception as e:
            print(f"   Failed to load tools: {e}")
            raise
        
        print("Agent 2: Financial Analyst initialized successfully")
    
    def generate_recommendations(self, user_id: str) -> Dict[str, Any]:
        print(f"\n{'='*70}")
        print(f"AGENT 2: GENERATING RECOMMENDATIONS")
        print(f"   User ID: {user_id}")
        print(f"{'='*70}\n")
        
        recommendations_created = []
        
        print("STEP 1: Analyzing budget health...")
        budget_recs = self._analyze_budget_health(user_id)
        recommendations_created.extend(budget_recs)
        print(f"   Created {len(budget_recs)} budget recommendations\n")
        
        print("STEP 2: Finding savings opportunities...")
        savings_recs = self._find_savings_opportunities(user_id)
        recommendations_created.extend(savings_recs)
        print(f"   Created {len(savings_recs)} savings recommendations\n")
        
        print("STEP 3: Optimizing subscriptions...")
        subscription_recs = self._optimize_subscriptions(user_id)
        recommendations_created.extend(subscription_recs)
        print(f"   Created {len(subscription_recs)} subscription recommendations\n")
        
        print("STEP 4: Predicting spending trends...")
        trend_recs = self._predict_spending_trends(user_id)
        recommendations_created.extend(trend_recs)
        print(f"   Created {len(trend_recs)} trend-based recommendations\n")
        
        total_savings = sum(r.get('potential_savings', 0) for r in recommendations_created)
        high_priority = sum(1 for r in recommendations_created if r['priority'] <= 2)
        
        print(f"{'='*70}")
        print(f"AGENT 2: RECOMMENDATIONS COMPLETE")
        print(f"{'='*70}")
        print(f"   Total recommendations: {len(recommendations_created)}")
        print(f"   High priority: {high_priority}")
        print(f"   Potential monthly savings: ${total_savings:.2f}")
        print(f"{'='*70}\n")
        
        return {
            'status': 'success',
            'total_recommendations': len(recommendations_created),
            'high_priority': high_priority,
            'potential_monthly_savings': total_savings,
            'potential_annual_savings': total_savings * 12,
            'recommendations': recommendations_created
        }
    
    def generate_daily_summary(self, user_id: str, summary_date: Optional[str] = None) -> Dict[str, Any]:
        if not summary_date:
            summary_date = datetime.now().date().isoformat()
        
        print(f"\n{'='*70}")
        print(f"AGENT 2: GENERATING DAILY SUMMARY")
        print(f"   User ID: {user_id}")
        print(f"   Date: {summary_date}")
        print(f"{'='*70}\n")
        
        print("STEP 1: Fetching today's transactions...")
        today_txns = self._get_transactions_for_date(user_id, summary_date)
        print(f"   Found {len(today_txns)} transactions\n")
        
        print("STEP 2: Analyzing spending by category...")
        spending_by_category = self._analyze_spending_by_category(today_txns)
        total_spent = sum(spending_by_category.values())
        print(f"   Total spent today: ${total_spent:.2f}\n")
        
        print("STEP 3: Checking budget status...")
        budget_alerts = self._check_budget_status(user_id)
        print(f"   Budget alerts: {len(budget_alerts)}\n")
        
        print("STEP 4: Checking subscription charges...")
        subscriptions_today = self._get_subscriptions_charged_today(user_id, summary_date)
        print(f"   Subscriptions charged: {len(subscriptions_today)}\n")
        
        top_category = max(spending_by_category, key=spending_by_category.get) if spending_by_category else 'None'
        
        summary_text = self._create_summary_text(
            date=summary_date,
            total_spent=total_spent,
            transaction_count=len(today_txns),
            top_category=top_category,
            budget_alerts=budget_alerts,
            subscriptions_charged=len(subscriptions_today)
        )
        
        print(f"{'='*70}")
        print(f"DAILY SUMMARY")
        print(f"{'='*70}")
        print(summary_text)
        print(f"{'='*70}\n")
        
        return {
            'status': 'success',
            'summary_date': summary_date,
            'total_spent': total_spent,
            'transaction_count': len(today_txns),
            'spending_by_category': spending_by_category,
            'top_category': top_category,
            'budget_alerts': budget_alerts,
            'subscriptions_charged': subscriptions_today,
            'summary_text': summary_text
        }
    
    def _analyze_budget_health(self, user_id: str) -> List[Dict]:
        recommendations = []
        
        try:
            tool = self.toolbox_client.load_tool('get-current-month-spending')
            current_spending = tool(user_id=user_id)
            
            if isinstance(current_spending, str):
                current_spending = json.loads(current_spending)
            
            if not current_spending:
                return recommendations
            
            for category_data in current_spending:
                category = category_data['category']
                current = float(category_data['total_amount'])
                baseline = self._get_category_baseline(user_id, category)
                
                if baseline > 0:
                    utilization = (current / baseline) * 100
                    
                    if utilization > 120:
                        potential_savings = current - baseline
                        
                        rec = {
                            'tool_name': 'budget_analyzer',
                            'recommendation_type': 'budget_alert',
                            'title': f'Over Budget in {category}',
                            'description': f'You\'ve spent ${current:.2f} in {category} this month, which is {utilization:.0f}% of your typical spending (${baseline:.2f}).',
                            'potential_savings': potential_savings,
                            'annual_savings': potential_savings * 12,
                            'priority': 1,
                            'urgency': 'high',
                            'related_category': category
                        }
                        
                        recommendations.append(rec)
                        self._save_recommendation(user_id, rec)
                    
                    elif utilization > 100:
                        potential_savings = current - baseline
                        
                        rec = {
                            'tool_name': 'budget_analyzer',
                            'recommendation_type': 'budget_warning',
                            'title': f'{category} Spending Above Average',
                            'description': f'You\'re at {utilization:.0f}% of typical {category} spending.',
                            'potential_savings': potential_savings,
                            'annual_savings': potential_savings * 12,
                            'priority': 2,
                            'urgency': 'medium',
                            'related_category': category
                        }
                        
                        recommendations.append(rec)
                        self._save_recommendation(user_id, rec)
        
        except Exception as e:
            print(f"Error analyzing budget: {e}")
        
        return recommendations
    
    def _find_savings_opportunities(self, user_id: str) -> List[Dict]:
        recommendations = []
        
        try:
            tool = self.toolbox_client.load_tool('get-current-month-spending')
            current_spending = tool(user_id=user_id)
            
            if isinstance(current_spending, str):
                current_spending = json.loads(current_spending)
            
            if not current_spending:
                return recommendations
            
            for category_data in current_spending:
                category = category_data['category']
                current = float(category_data['total_amount'])
                
                if category in ['Dining', 'Shopping', 'Entertainment']:
                    baseline = self._get_category_baseline(user_id, category)
                    
                    if baseline > 0 and current > baseline * 1.2:
                        potential_savings = (current - baseline) * 0.5
                        
                        rec = {
                            'tool_name': 'savings_finder',
                            'recommendation_type': 'reduce_spending',
                            'title': f'Save on {category}',
                            'description': f'You\'re spending ${current:.2f}/month on {category}, above baseline of ${baseline:.2f}.',
                            'potential_savings': potential_savings,
                            'annual_savings': potential_savings * 12,
                            'priority': 3,
                            'urgency': 'low',
                            'related_category': category
                        }
                        
                        recommendations.append(rec)
                        self._save_recommendation(user_id, rec)
        
        except Exception as e:
            print(f"Error finding savings: {e}")
        
        return recommendations
    
    def _optimize_subscriptions(self, user_id: str) -> List[Dict]:
        recommendations = []
        
        try:
            tool = self.toolbox_client.load_tool('get-user-subscriptions')
            subscriptions = tool(user_id=user_id)
            
            if isinstance(subscriptions, str):
                subscriptions = json.loads(subscriptions)
            
            if not subscriptions:
                return recommendations
            
            total_monthly = sum(float(s.get('amount', 0)) for s in subscriptions)
            
            if total_monthly > 100:
                rec = {
                    'tool_name': 'subscription_optimizer',
                    'recommendation_type': 'reduce_subscriptions',
                    'title': 'High Subscription Spending',
                    'description': f'You\'re spending ${total_monthly:.2f}/month on {len(subscriptions)} subscriptions.',
                    'potential_savings': total_monthly * 0.3,
                    'annual_savings': total_monthly * 12 * 0.3,
                    'priority': 2,
                    'urgency': 'medium',
                    'related_category': 'Subscriptions'
                }
                recommendations.append(rec)
                self._save_recommendation(user_id, rec)
            
            for sub in subscriptions:
                amount = float(sub.get('amount', 0))
                merchant = sub.get('merchant_standardized', '')
                
                if amount > 50:
                    rec = {
                        'tool_name': 'subscription_optimizer',
                        'recommendation_type': 'expensive_subscription',
                        'title': f'Review {merchant} Subscription',
                        'description': f'{merchant} costs ${amount:.2f}/month (${amount * 12:.2f}/year).',
                        'potential_savings': amount,
                        'annual_savings': amount * 12,
                        'priority': 3,
                        'urgency': 'low',
                        'related_merchant': merchant,
                        'related_category': 'Subscriptions'
                    }
                    recommendations.append(rec)
                    self._save_recommendation(user_id, rec)
        
        except Exception as e:
            print(f"Error optimizing subscriptions: {e}")
        
        return recommendations
    
    def _predict_spending_trends(self, user_id: str) -> List[Dict]:
        recommendations = []
        
        try:
            tool = self.toolbox_client.load_tool('get-user-categories')
            categories = tool(user_id=user_id)
            
            if isinstance(categories, str):
                categories = json.loads(categories)
            
            for cat_data in categories:
                category = cat_data['category']
                history = self._get_category_history(user_id, category, months=3)
                
                if len(history) >= 2:
                    amounts = [float(h['total_amount']) for h in history]
                    avg_amount = sum(amounts) / len(amounts)
                    recent_amount = amounts[0]
                    
                    if recent_amount > avg_amount * 1.2:
                        predicted_next = recent_amount * 1.1
                        
                        rec = {
                            'tool_name': 'trend_predictor',
                            'recommendation_type': 'trend_alert',
                            'title': f'{category} Spending Trending Up',
                            'description': f'Last month: ${recent_amount:.2f}, predicted: ${predicted_next:.2f}.',
                            'potential_savings': predicted_next - avg_amount,
                            'annual_savings': (predicted_next - avg_amount) * 12,
                            'priority': 2,
                            'urgency': 'medium',
                            'related_category': category
                        }
                        
                        recommendations.append(rec)
                        self._save_recommendation(user_id, rec)
        
        except Exception as e:
            print(f"Error predicting trends: {e}")
        
        return recommendations
    
    def _get_category_baseline(self, user_id: str, category: str) -> float:
        try:
            history = self._get_category_history(user_id, category, months=3)
            if history:
                amounts = [float(h['total_amount']) for h in history]
                return sum(amounts) / len(amounts)
            return 0.0
        except:
            return 0.0
    
    def _get_category_history(self, user_id: str, category: str, months: int = 3) -> List[Dict]:
        try:
            tool = self.toolbox_client.load_tool('get-category-history')
            result = tool(user_id=user_id, category=category, months=months)
            
            if isinstance(result, str):
                result = json.loads(result)
            
            return result if isinstance(result, list) else []
        except:
            return []
    
    def _save_recommendation(self, user_id: str, rec: Dict):
        try:
            tool = self.toolbox_client.load_tool('insert-recommendation')
            tool(
                user_id=user_id,
                tool_name=rec['tool_name'],
                recommendation_type=rec['recommendation_type'],
                title=rec['title'],
                description=rec['description'],
                potential_savings=str(rec['potential_savings']),
                annual_savings=str(rec['annual_savings']),
                priority=rec['priority'],
                urgency=rec['urgency'],
                related_category=rec.get('related_category', ''),
                related_merchant=rec.get('related_merchant', '')
            )
        except Exception as e:
            print(f"Error saving recommendation: {e}")
    
    def _get_transactions_for_date(self, user_id: str, date_str: str) -> List[Dict]:
        try:
            tool = self.toolbox_client.load_tool('get-user-transactions')
            result = tool(user_id=user_id, start_date=date_str, end_date=date_str)
            
            if isinstance(result, str):
                result = json.loads(result)
            
            return result if isinstance(result, list) else []
        except:
            return []
    
    def _analyze_spending_by_category(self, transactions: List[Dict]) -> Dict[str, float]:
        spending = defaultdict(float)
        
        for txn in transactions:
            try:
                amount = abs(float(txn.get('amount', 0)))
                category = txn.get('category', 'Other')
                
                if amount > 0 and txn.get('transaction_type') != 'credit':
                    spending[category] += amount
            except:
                continue
        
        return dict(spending)
    
    def _check_budget_status(self, user_id: str) -> List[str]:
        alerts = []
        
        try:
            tool = self.toolbox_client.load_tool('get-current-month-spending')
            current_spending = tool(user_id=user_id)
            
            if isinstance(current_spending, str):
                current_spending = json.loads(current_spending)
            
            for category_data in current_spending:
                category = category_data['category']
                current = float(category_data['total_amount'])
                baseline = self._get_category_baseline(user_id, category)
                
                if baseline > 0 and current > baseline * 1.2:
                    alerts.append(f"{category}: ${current:.2f} (120% of baseline)")
        
        except:
            pass
        
        return alerts
    
    def _get_subscriptions_charged_today(self, user_id: str, date_str: str) -> List[Dict]:
        subscriptions_charged = []
        
        try:
            transactions = self._get_transactions_for_date(user_id, date_str)
            
            for txn in transactions:
                merchant = (txn.get('merchant_name') or txn.get('name', '')).upper()
                
                if any(word in merchant for word in ['SPOTIFY', 'NETFLIX', 'LINKEDIN', 'PRIME', 'DISNEY', 'GYM']):
                    subscriptions_charged.append({
                        'merchant': merchant,
                        'amount': abs(float(txn.get('amount', 0)))
                    })
        
        except:
            pass
        
        return subscriptions_charged
    
    def _create_summary_text(self, date: str, total_spent: float, transaction_count: int,
                            top_category: str, budget_alerts: List[str], subscriptions_charged: int) -> str:
        
        lines = [
            f"Daily Summary for {date}",
            "",
            f"Spending Today: ${total_spent:.2f}",
            f"Transactions: {transaction_count}",
            f"Top Category: {top_category}",
            "",
            f"Budget Alerts: {len(budget_alerts)}" if budget_alerts else "No budget alerts",
            f"Subscriptions Charged: {subscriptions_charged}"
        ]
        
        if budget_alerts:
            lines.append("")
            for alert in budget_alerts[:3]:
                lines.append(f"  - {alert}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dfea6d34-dc5d-407e-b39a-329ad905cc57"
    
    try:
        agent2 = FinancialAnalystAgent()
        
        print("\nTEST 1: Recommendations")
        result = agent2.generate_recommendations(user_id)
        print(json.dumps(result, indent=2))
        
        print("\n\nTEST 2: Daily Summary")
        summary = agent2.generate_daily_summary(user_id)
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()