"""
Query Agent - Answers analytical questions
File: mcp_toolbox/tools/query_agent.py

FIXED VERSION - Proper exception handling and variable scoping
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from toolbox_core import ToolboxSyncClient


class QueryAgent:
    """Agent for answering analytical questions about finances"""
    
    def __init__(self, toolbox_url: str = "http://127.0.0.1:5000"):
        print("Initializing Query Agent...")
        self.toolbox_client = ToolboxSyncClient(toolbox_url)
        
        try:
            self.tools = self.toolbox_client.load_toolset()
            print(f"   Loaded {len(self.tools)} tools")
        except Exception as e:
            print(f"   Failed to load tools: {e}")
            raise
        
        print("Query Agent initialized successfully")
    
    def answer_question(self, user_id: str, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Answer a question about user's finances"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        question_lower = question.lower()
        intent = self._detect_intent(question_lower)
        
        print(f"\nQuery: {question}")
        print(f"Intent: {intent}")
        
        # Check cache
        try:
            cached = self._check_similar_queries(user_id, intent)
            
            if cached:
                print("✓ Cached answer found")
                self._save_conversation(user_id, session_id, 'user', question, intent, "", "")
                self._save_conversation(user_id, session_id, 'assistant', cached['answer'], intent, "", "")
                
                return {
                    'status': 'success',
                    'answer': cached['answer'] + "\n\n_💡 (Cached)_",
                    'data': cached.get('data'),
                    'cached': True
                }
        except Exception as e:
            print(f"Cache check failed: {e}")
            cached = None
        
        # Execute query
        try:
            result = self._execute_query(user_id, question_lower, intent)
            
            # Save conversation
            tools_called = result.get('tools_called', [])
            tool_results = result.get('tool_results', {})
            
            self._save_conversation(
                user_id, session_id, 'user', question, intent,
                json.dumps(tools_called) if tools_called else "",
                json.dumps(tool_results) if tool_results else ""
            )
            
            if result.get('answer'):
                self._save_conversation(user_id, session_id, 'assistant', result['answer'], intent, "", "")
            
            return result
        
        except Exception as e:
            print(f"Query execution failed: {e}")
            return {
                'status': 'error',
                'message': f'Error processing question: {str(e)}'
            }
    
    def _detect_intent(self, question: str) -> str:
        """Detect user's intent"""
        
        if 'subscription' in question:
            if any(w in question for w in ['most', 'highest', 'expensive', 'maximum']):
                return 'subscription_most_expensive'
            elif any(w in question for w in ['total', 'how much']):
                return 'subscription_total_cost'
            return 'subscription_list'
        elif any(w in question for w in ['merchant', 'store', 'where']):
            return 'merchant_top_spending'
        elif any(w in question for w in ['category', 'expense']):
            return 'category_breakdown'
        elif any(w in question for w in ['bill', 'due']):
            return 'bills_upcoming'
        elif any(w in question for w in ['anomal', 'unusual']):
            return 'spending_anomalies'
        elif any(w in question for w in ['compare', 'vs']):
            return 'month_comparison'
        return 'general_query'
    
    def _check_similar_queries(self, user_id: str, intent: str) -> Optional[Dict]:
        """Check cache for similar queries"""
        
        try:
            tool = self.toolbox_client.load_tool('get-similar-queries')
            similar = tool(user_id=user_id, intent=intent, limit=1)
            
            if isinstance(similar, str):
                similar = json.loads(similar)
            
            if similar and len(similar) > 0:
                from datetime import datetime, timedelta
                recent = similar[0]
                
                if recent.get('created_at') and recent.get('assistant_response'):
                    created_at = datetime.fromisoformat(recent['created_at'].replace('Z', '+00:00'))
                    
                    if datetime.now().astimezone() - created_at < timedelta(hours=1):
                        return {
                            'answer': recent['assistant_response'],
                            'data': json.loads(recent['tool_results']) if recent.get('tool_results') else None
                        }
            
            return None
        
        except Exception as e:
            print(f"Cache check error: {e}")
            return None
    
    def _execute_query(self, user_id: str, question: str, intent: str) -> Dict[str, Any]:
        """Execute appropriate query based on intent"""
        
        handlers = {
            'subscription_most_expensive': self._handle_subscription_query,
            'subscription_total_cost': self._handle_subscription_query,
            'subscription_list': self._handle_subscription_query,
            'merchant_top_spending': self._handle_merchant_query,
            'category_breakdown': self._handle_category_query,
            'bills_upcoming': self._handle_bills_query,
            'spending_anomalies': self._handle_anomaly_query,
            'month_comparison': self._handle_comparison_query
        }
        
        handler = handlers.get(intent, self._handle_unknown)
        return handler(user_id, question)
    
    def _save_conversation(self, user_id: str, session_id: str, role: str, message: str,
                          intent: str, tools_called: str, tool_results: str):
        """Save conversation to database"""
        
        try:
            tool = self.toolbox_client.load_tool('save-conversation')
            tool(
                user_id=user_id,
                session_id=session_id,
                role=role,
                message=message,
                intent=intent,
                tools_called=tools_called,
                tool_results=tool_results
            )
        except Exception as e:
            print(f"Warning: Could not save conversation: {e}")
    
    def get_frequent_questions(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get frequently asked questions"""
        
        try:
            tool = self.toolbox_client.load_tool('get-frequent-questions')
            result = tool(user_id=user_id, limit=limit)
            
            if isinstance(result, str):
                result = json.loads(result)
            
            return result if isinstance(result, list) else []
        
        except Exception as e:
            print(f"Error getting frequent questions: {e}")
            return []
    
    # =========================================================================
    # QUERY HANDLERS
    # =========================================================================
    
    def _handle_subscription_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle subscription questions"""
        
        subscriptions = []  # Initialize to avoid UnboundLocalError
        
        try:
            tool = self.toolbox_client.load_tool('get-subscription-details')
            result = tool(user_id=user_id)
            
            if isinstance(result, str):
                subscriptions = json.loads(result)
            else:
                subscriptions = result if isinstance(result, list) else []
            
            if not subscriptions:
                return {
                    'status': 'success',
                    'answer': 'You have no active subscriptions.',
                    'data': [],
                    'tools_called': ['get-subscription-details']
                }
            
            # Most expensive
            if any(w in question for w in ['most', 'highest', 'expensive', 'maximum']):
                top = max(subscriptions, key=lambda x: float(x.get('amount', 0)))
                
                answer = f"💰 Your most expensive subscription is **{top['merchant_standardized']}** at **${float(top['amount']):.2f}/month** (${float(top['annual_cost']):.2f}/year)."
                
                return {
                    'status': 'success',
                    'answer': answer,
                    'data': [top],
                    'all_subscriptions': subscriptions,
                    'tools_called': ['get-subscription-details']
                }
            
            # Total cost
            elif any(w in question for w in ['total', 'how much']):
                total_monthly = sum(float(s.get('amount', 0)) for s in subscriptions)
                total_annual = sum(float(s.get('annual_cost', 0)) for s in subscriptions)
                
                answer = f"💵 You have **{len(subscriptions)} active subscriptions** costing **${total_monthly:.2f}/month** (${total_annual:.2f}/year)."
                
                return {
                    'status': 'success',
                    'answer': answer,
                    'data': subscriptions,
                    'tools_called': ['get-subscription-details']
                }
            
            # List all
            else:
                total_monthly = sum(float(s.get('amount', 0)) for s in subscriptions)
                
                answer = f"📋 You have **{len(subscriptions)} subscriptions** (${total_monthly:.2f}/month):\n\n"
                
                sorted_subs = sorted(subscriptions, key=lambda x: float(x.get('amount', 0)), reverse=True)
                for i, sub in enumerate(sorted_subs, 1):
                    answer += f"{i}. **{sub['merchant_standardized']}**: ${float(sub['amount']):.2f}/{sub['frequency']}\n"
                
                return {
                    'status': 'success',
                    'answer': answer,
                    'data': subscriptions,
                    'tools_called': ['get-subscription-details']
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error querying subscriptions: {str(e)}'
            }
    
    def _handle_merchant_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle merchant spending questions"""
        
        try:
            tool = self.toolbox_client.load_tool('get-top-merchants')
            result = tool(user_id=user_id, limit=10)
            
            if isinstance(result, str):
                merchants = json.loads(result)
            else:
                merchants = result if isinstance(result, list) else []
            
            if not merchants:
                return {
                    'status': 'success',
                    'answer': 'No merchant data available yet.',
                    'data': []
                }
            
            top = merchants[0]
            answer = f"🏪 You spend the most at **{top['merchant_standardized']}** with **${float(top['total_spent']):.2f}** total across {top['transaction_count']} transactions."
            
            return {
                'status': 'success',
                'answer': answer,
                'data': merchants[:5],
                'tools_called': ['get-top-merchants']
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error querying merchants: {str(e)}'
            }
    
    def _handle_category_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle category spending questions"""
        
        try:
            tool = self.toolbox_client.load_tool('get-category-breakdown')
            result = tool(user_id=user_id)
            
            if isinstance(result, str):
                categories = json.loads(result)
            else:
                categories = result if isinstance(result, list) else []
            
            if not categories:
                return {
                    'status': 'success',
                    'answer': 'No spending data available for this month.',
                    'data': []
                }
            
            if any(w in question for w in ['most', 'highest', 'biggest']):
                top = max(categories, key=lambda x: float(x.get('total_amount', 0)))
                
                answer = f"📊 Your highest spending category is **{top['category']}** at **${float(top['total_amount']):.2f}** ({top['transaction_count']} transactions)."
                
                return {
                    'status': 'success',
                    'answer': answer,
                    'data': [top],
                    'tools_called': ['get-category-breakdown']
                }
            
            else:
                total = sum(float(c.get('total_amount', 0)) for c in categories)
                
                answer = f"💰 Spending breakdown this month (${total:.2f} total):\n\n"
                
                for cat in sorted(categories, key=lambda x: float(x.get('total_amount', 0)), reverse=True):
                    pct = (float(cat['total_amount']) / total * 100) if total > 0 else 0
                    answer += f"• **{cat['category']}**: ${float(cat['total_amount']):.2f} ({pct:.1f}%)\n"
                
                return {
                    'status': 'success',
                    'answer': answer,
                    'data': categories,
                    'tools_called': ['get-category-breakdown']
                }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error querying categories: {str(e)}'
            }
    
    def _handle_bills_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle bill questions"""
        
        try:
            tool = self.toolbox_client.load_tool('get-upcoming-bills')
            result = tool(user_id=user_id)
            
            if isinstance(result, str):
                bills = json.loads(result)
            else:
                bills = result if isinstance(result, list) else []
            
            if not bills:
                return {
                    'status': 'success',
                    'answer': '✅ No bills due in the next 7 days!',
                    'data': []
                }
            
            answer = f"📅 You have **{len(bills)} bills** coming up:\n\n"
            
            for bill in bills:
                answer += f"• **{bill['merchant_standardized']}**: ~${abs(float(bill['typical_amount'])):.2f} (day {bill['bill_cycle_day']})\n"
            
            return {
                'status': 'success',
                'answer': answer,
                'data': bills,
                'tools_called': ['get-upcoming-bills']
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error querying bills: {str(e)}'
            }
    
    def _handle_anomaly_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle unusual spending questions"""
        
        try:
            tool = self.toolbox_client.load_tool('get-anomalous-spending')
            result = tool(user_id=user_id, limit=5)
            
            if isinstance(result, str):
                anomalies = json.loads(result)
            else:
                anomalies = result if isinstance(result, list) else []
            
            if not anomalies:
                return {
                    'status': 'success',
                    'answer': '✅ No unusual spending detected. Great job staying consistent!',
                    'data': []
                }
            
            answer = f"⚠️ Found **{len(anomalies)} unusual transactions**:\n\n"
            
            for a in anomalies:
                answer += f"• **{a['merchant_standardized']}**: ${abs(float(a['amount'])):.2f} on {a['date']}\n"
            
            return {
                'status': 'success',
                'answer': answer,
                'data': anomalies,
                'tools_called': ['get-anomalous-spending']
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error querying anomalies: {str(e)}'
            }
    
    def _handle_comparison_query(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle month comparison questions"""
        
        try:
            tool = self.toolbox_client.load_tool('compare-month-spending')
            result = tool(user_id=user_id)
            
            if isinstance(result, str):
                comparison = json.loads(result)
            else:
                comparison = result if isinstance(result, list) else []
            
            if not comparison:
                return {
                    'status': 'success',
                    'answer': 'Not enough data to compare months yet.',
                    'data': []
                }
            
            answer = "📊 **This Month vs Last Month:**\n\n"
            
            for cat in comparison:
                change = float(cat.get('difference', 0))
                
                if abs(change) > 10:
                    direction = "📈 increased" if change > 0 else "📉 decreased"
                    answer += f"• **{cat['category']}**: {direction} by ${abs(change):.2f}\n"
            
            return {
                'status': 'success',
                'answer': answer,
                'data': comparison,
                'tools_called': ['compare-month-spending']
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error comparing months: {str(e)}'
            }
    
    def _handle_unknown(self, user_id: str, question: str) -> Dict[str, Any]:
        """Handle unknown questions"""
        
        return {
            'status': 'unclear',
            'message': 'I can answer questions about subscriptions, merchants, categories, bills, and spending comparisons.'
        }


if __name__ == "__main__":
    import sys
    
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dfea6d34-dc5d-407e-b39a-329ad905cc57"
    question = sys.argv[2] if len(sys.argv) > 2 else "which subscription costs the most"
    
    try:
        agent = QueryAgent()
        result = agent.answer_question(user_id, question)
        
        print("\n" + "="*70)
        print("ANSWER:")
        print("="*70)
        print(result.get('answer', result.get('message', 'No answer')))
        print("="*70 + "\n")
        
        if result.get('data'):
            print("DATA:")
            print(json.dumps(result['data'], indent=2))
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()