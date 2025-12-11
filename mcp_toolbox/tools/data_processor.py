"""
Agent 1: Data Processor - FIXED VERSION
Properly detects subscriptions, bills, and sets all database fields correctly
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from dotenv import load_dotenv

from google.adk.agents import Agent
from toolbox_core import ToolboxSyncClient
from google.genai import types

load_dotenv()


class DataProcessorAgent:
    """Agent 1: Processes and enhances transaction data - IMPROVED"""
    
    STANDARD_CATEGORIES = [
        'Groceries', 'Dining', 'Transportation', 'Entertainment',
        'Shopping', 'Bills', 'Healthcare', 'Income', 'Transfers', 'Other'
    ]
    
    PLAID_CATEGORY_MAP = {
        'TRANSPORTATION': 'Transportation',
        'FOOD_AND_DRINK': 'Dining',
        'GENERAL_MERCHANDISE': 'Shopping',
        'ENTERTAINMENT': 'Entertainment',
        'HEALTHCARE': 'Healthcare',
        'TRAVEL': 'Travel',
        'INCOME': 'Income',
        'LOAN_PAYMENTS': 'Bills',
        'TRANSFER': 'Transfers',
        'BANK_FEES': 'Fees'
    }
    
    MERCHANT_PATTERNS = {
        r'AMZN|AMAZON\.COM|Amazon\.com': 'Amazon',
        r'LINKEDPRE|LINKEDIN PREMIUM': 'LinkedIn Premium',
        r'SQ \*(.+)': r'\1',
        r'TST\*(.+)': r'\1',
        r'PAYPAL \*(.+)': r'\1',
        r'UBER.*POOL': 'Uber Pool',
        r'UBER.*EATS': 'Uber Eats',
        r'UBER \d+': 'Uber',
        r'SPOTIFY': 'Spotify',
        r'NETFLIX': 'Netflix',
        r'HULU': 'Hulu',
        r'DISNEY\+|DISNEY PLUS': 'Disney Plus',
        r'HBO MAX': 'HBO Max',
        r'PRIME VIDEO': 'Amazon Prime Video',
        r'AMAZON PRIME': 'Amazon Prime',
        r'STARBUCKS': 'Starbucks',
        r'MCDONALDS|MCDONALD\'S': "McDonald's",
        r'WHOLE FOODS': 'Whole Foods Market',
        r'TARGET': 'Target',
        r'WALMART': 'Walmart',
        r'COSTCO': 'Costco',
        r'CVS': 'CVS Pharmacy',
        r'WALGREENS': 'Walgreens',
        r'SHELL OIL': 'Shell',
        r'CHEVRON': 'Chevron',
        r'EXXON': 'ExxonMobil',
        r'CHIPOTLE': 'Chipotle',
        r'VENMO': 'Venmo',
        r'INTRST PYMNT': 'Interest Payment',
        r'CREDIT CARD.*PAYMENT': 'Credit Card Payment',
        r'RENT PAYMENT|RENT': 'Rent Payment',
        r'PAYROLL DEPOSIT': 'Payroll Deposit',
        r'ELECTRIC|ELECTRICITY': 'Electric Company',
        r'GAS BILL|GAS COMPANY': 'Gas Company',
        r'WATER BILL': 'Water Company',
        r'INTERNET|ISP': 'Internet Service',
        r'PHONE BILL|MOBILE|WIRELESS': 'Phone Service',
        r'INSURANCE': 'Insurance Payment'
    }
    
    # Keywords that indicate bills
    BILL_KEYWORDS = [
        'RENT', 'MORTGAGE', 'LEASE',
        'ELECTRIC', 'ELECTRICITY', 'POWER',
        'GAS BILL', 'GAS COMPANY',
        'WATER', 'SEWER',
        'INTERNET', 'ISP', 'BROADBAND',
        'PHONE BILL', 'MOBILE', 'WIRELESS', 'AT&T', 'VERIZON', 'T-MOBILE',
        'INSURANCE', 'PREMIUM',
        'LOAN PAYMENT', 'MORTGAGE PAYMENT',
        'CREDIT CARD PAYMENT',
        'HOA', 'HOMEOWNERS ASSOCIATION',
        'UTILITY', 'UTILITIES'
    ]
    
    # Subscription keywords
    SUBSCRIPTION_KEYWORDS = [
        'SUBSCRIPTION', 'PREMIUM', 'PRO', 'PLUS', 'MEMBERSHIP',
        'SPOTIFY', 'SPOTIFY PREMIUM', 'NETFLIX', 'NETFLIX PREMIUM', 'HULU', 'DISNEY', 'HBO', 'APPLE MUSIC',
        'GYM', 'GYM MEMBERSHIP', 'Library Membership', 'CHIPOTLE', 'MCD', 'FOOD SUBSCRIPTION', 'FITNESS', 'YOGA', 'PELOTON',
        'UberOne', 'Uber', 'Uber Eats', 'Stop & Shop Subscription', 'Target Subscription', 'Walmart Susbscription', 'Columbia Subscription',
        'CLOUD', 'STORAGE', 'DROPBOX', 'GOOGLE ONE', 'Chat gpt premium', 'Chat gpt subscription', 'claude',
        'LINKEDIN', 'LINKEDIN PREMIUM', 'ADOBE', 'MICROSOFT 365', 'PRIME', 'HOTSTAR', 'IMDB',
        'ANNUAL', 'MONTHLY', 'YEARLY', 'HOTSTAR'
    ]
    
    def __init__(self, toolbox_url: str = "http://127.0.0.1:5000"):
        """Initialize Agent 1 with MCP Toolbox connection"""
        
        print("Initializing Agent 1: Data Processor (FIXED VERSION)...")
        print(f"   Connecting to toolbox at {toolbox_url}...")
        
        import time
        import requests
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{toolbox_url}/health", timeout=2)
                print(f"   Toolbox is accessible (HTTP {response.status_code})")
                break
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"   Attempt {attempt + 1}/{max_retries}: Toolbox not ready, waiting...")
                    time.sleep(2)
                else:
                    raise RuntimeError(
                        f"Toolbox is not running at {toolbox_url}\n"
                        f"   Please start toolbox first"
                    )
        
        try:
            self.toolbox_client = ToolboxSyncClient(toolbox_url)
            print(f"   Loading tools from toolbox...")
            
            try:
                self.tools = self.toolbox_client.load_toolset("default")
                print(f"   Loaded tools from 'default' toolset")
            except:
                print(f"   Trying to load tools without toolset name...")
                self.tools = self.toolbox_client.load_toolset()
            
            print(f"   Loaded {len(self.tools) if isinstance(self.tools, list) else 'multiple'} tools")
        except Exception as e:
            print(f"   Failed to load tools: {e}")
            raise
        
        self.agent = Agent(
            name='data_processor_agent',
            model='gemini-2.5-flash',
            instruction=self._get_instruction(),
            tools=self.tools,
            generate_content_config=types.GenerateContentConfig(
                temperature=0.1,
            )
        )
        
        print("Agent 1: Data Processor initialized successfully (FIXED)")
    
    def _get_instruction(self) -> str:
        """Agent 1 system instruction"""
        categories_str = ', '.join(self.STANDARD_CATEGORIES)
        
        return f"""
You are Agent 1: Data Processor for Smart Expense Analyzer.

Your mission: Process raw transaction data and enhance it with AI insights.

RESPONSIBILITIES:
1. Fetch unprocessed transactions using database tools
2. Categorize transactions into: {categories_str}
3. Standardize merchant names
4. Detect recurring bills (rent, utilities, insurance, etc.)
5. Detect subscriptions (streaming, software, memberships)
6. Flag anomalous transactions
7. Calculate spending patterns
8. Save all processed data with correct flags

STANDARD CATEGORIES: {categories_str}

IMPORTANT FLAGS:
- is_bill: True for recurring monthly bills (rent, utilities, phone, insurance)
- bill_cycle_day: Day of month the bill typically occurs
- is_subscription: True for recurring subscriptions (Spotify, Netflix, etc.)
- is_anomaly: True only for unusually high discretionary spending

AVAILABLE TOOLS:
- fetch-unprocessed-transactions: Get transactions needing processing
- get-user-transactions: Get transactions in a date range
- insert-processed-transaction: Save enhanced transaction data
- upsert-subscription: Save detected subscriptions
- get-user-subscriptions: Check existing subscriptions
- insert-spending-pattern: Save spending analytics
- get-category-history: Get historical spending data

RULES:
- Always set is_bill=true for Bills category
- Calculate bill_cycle_day from transaction date
- Check historical data to confirm recurring patterns
- Be consistent in categorization
- Save everything to avoid reprocessing
"""
    
    def process_user_transactions(self, user_id: str) -> Dict[str, Any]:
        """Main entry point: Process all unprocessed transactions for a user"""
        
        print(f"\n{'='*70}")
        print(f"AGENT 1: PROCESSING TRANSACTIONS (FIXED VERSION)")
        print(f"   User ID: {user_id}")
        print(f"{'='*70}\n")
        
        print("STEP 1: Fetching unprocessed transactions...")
        unprocessed = self._fetch_unprocessed_transactions(user_id)
        
        if not unprocessed:
            print("No new transactions to process\n")
            return {
                'status': 'success',
                'message': 'No new transactions',
                'processed_count': 0,
                'subscriptions_detected': 0,
                'bills_detected': 0,
                'patterns_calculated': 0
            }
        
        print(f"   Found {len(unprocessed)} unprocessed transactions\n")
        
        # Fetch historical data for better detection
        print(f"STEP 2: Fetching historical data for pattern detection...")
        historical_data = self._fetch_historical_transactions(user_id, days=180)
        print(f"   Historical transactions: {len(historical_data)}\n")
        
        print(f"STEP 3: Processing transactions with AI...")
        processed_results = self._process_transactions(unprocessed, historical_data, user_id)
        print(f"   Processed: {processed_results['count']} transactions")
        print(f"   Bills detected: {processed_results['bills']}")
        print(f"   Subscriptions detected: {processed_results['subscriptions']}")
        print(f"   Anomalies: {processed_results['anomalies']} flagged\n")
        
        print(f"STEP 4: Calculating spending patterns...")
        pattern_results = self._calculate_spending_patterns(user_id)
        print(f"   Patterns: {pattern_results['categories']} categories analyzed\n")
        
        print(f"{'='*70}")
        print(f"AGENT 1: PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"   Transactions processed: {processed_results['count']}")
        print(f"   Bills detected: {processed_results['bills']}")
        print(f"   Subscriptions detected: {processed_results['subscriptions']}")
        print(f"   Spending categories: {pattern_results['categories']}")
        print(f"   Anomalies flagged: {processed_results['anomalies']}")
        print(f"{'='*70}\n")
        
        return {
            'status': 'success',
            'processed_count': processed_results['count'],
            'bills_detected': processed_results['bills'],
            'subscriptions_detected': processed_results['subscriptions'],
            'patterns_calculated': pattern_results['categories'],
            'anomalies_flagged': processed_results['anomalies']
        }
    
    def _fetch_unprocessed_transactions(self, user_id: str) -> List[Dict]:
        """Fetch transactions not yet processed using MCP tool"""
        try:
            tool = self.toolbox_client.load_tool('fetch-unprocessed-transactions')
            result = tool(user_id=user_id)
            
            if isinstance(result, str):
                result = json.loads(result)
            
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"Error fetching unprocessed transactions: {e}")
            return []
    
    def _fetch_historical_transactions(self, user_id: str, days: int = 180) -> List[Dict]:
        """Fetch historical transactions for pattern detection"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            tool = self.toolbox_client.load_tool('get-user-transactions')
            result = tool(
                user_id=user_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            
            if isinstance(result, str):
                result = json.loads(result)
            
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"Error fetching historical transactions: {e}")
            return []
    
    def _process_transactions(self, transactions: List[Dict], historical_data: List[Dict], user_id: str) -> Dict:
        """Process each transaction with categorization and enhanced detection"""
        processed_count = 0
        anomaly_count = 0
        bill_count = 0
        subscription_count = 0
        
        # Build historical merchant patterns
        merchant_history = self._build_merchant_history(historical_data)
        
        for i, txn in enumerate(transactions, 1):
            try:
                if i % 10 == 0:
                    print(f"   Processing... {i}/{len(transactions)}")
                
                txn_id = txn.get('transaction_id')
                user_id_txn = txn.get('user_id')
                
                # Step 1: Categorize
                category_ai = self._categorize_transaction(txn)
                
                # Step 2: Standardize merchant
                merchant_std = self._standardize_merchant_name(
                    txn.get('merchant_name') or txn.get('name', 'Unknown')
                )
                
                # Step 3: Detect if it's a bill
                is_bill, bill_cycle_day = self._detect_bill(txn, category_ai, merchant_std, merchant_history)
                if is_bill:
                    bill_count += 1
                
                # Step 4: Enhanced subscription detection
                is_subscription, sub_confidence = self._detect_subscription_enhanced(
                    txn, merchant_std, merchant_history
                )
                if is_subscription:
                    subscription_count += 1
                    # Save to subscriptions table
                    self._save_subscription_from_transaction(user_id_txn, txn, merchant_std, merchant_history)
                
                # Step 5: Detect anomalies
                is_anomaly, anomaly_score = self._detect_anomaly(txn, category_ai, merchant_std)
                if is_anomaly:
                    anomaly_count += 1
                
                # Step 6: Save with ALL fields - FIXED VERSION
                self._save_processed_transaction(
                    transaction_id=txn_id,
                    user_id=user_id_txn,
                    category_ai=category_ai,
                    merchant_standardized=merchant_std,
                    is_subscription=is_subscription,
                    subscription_confidence=str(sub_confidence) if is_subscription else "",
                    is_anomaly=is_anomaly,
                    anomaly_score=str(anomaly_score) if is_anomaly else "0.00",
                    anomaly_reason="",
                    is_bill=is_bill,
                    bill_cycle_day=bill_cycle_day if bill_cycle_day is not None else 0,  # Use 0 for non-bills
                    tags="",
                    notes=""
                )
                
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing transaction {txn.get('transaction_id')}: {e}")
                continue
        
        return {
            'count': processed_count,
            'bills': bill_count,
            'subscriptions': subscription_count,
            'anomalies': anomaly_count
        }
    
    def _build_merchant_history(self, historical_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Build a history of transactions by merchant for pattern detection"""
        merchant_history = defaultdict(list)
        
        for txn in historical_data:
            merchant = txn.get('merchant_name') or txn.get('name', 'Unknown')
            merchant_std = self._standardize_merchant_name(merchant)
            
            try:
                amount = abs(float(txn.get('amount', 0)))
                date_str = txn.get('date', '')
                
                merchant_history[merchant_std].append({
                    'amount': amount,
                    'date': date_str,
                    'original_name': merchant
                })
            except:
                continue
        
        return dict(merchant_history)
    
    def _detect_bill(self, txn: Dict, category: str, merchant: str, merchant_history: Dict) -> Tuple[bool, Optional[int]]:
        """
        Detect if transaction is a recurring bill
        Returns: (is_bill: bool, bill_cycle_day: Optional[int])
        """
        
        # Rule 1: Bills category should always be marked as bills
        if category == 'Bills':
            try:
                date_str = txn.get('date', '')
                if date_str:
                    txn_date = datetime.fromisoformat(date_str.split('T')[0])
                    return True, txn_date.day
            except:
                return True, None
        
        # Rule 2: Check for bill keywords in merchant name or transaction name
        merchant_upper = merchant.upper()
        name_upper = (txn.get('name') or '').upper()
        
        for keyword in self.BILL_KEYWORDS:
            if keyword in merchant_upper or keyword in name_upper:
                try:
                    date_str = txn.get('date', '')
                    if date_str:
                        txn_date = datetime.fromisoformat(date_str.split('T')[0])
                        return True, txn_date.day
                except:
                    return True, None
        
        # Rule 3: Check if merchant has recurring monthly pattern in history
        if merchant in merchant_history:
            history = merchant_history[merchant]
            if len(history) >= 2:
                dates = []
                for h in history:
                    try:
                        date_obj = datetime.fromisoformat(h['date'].split('T')[0])
                        dates.append(date_obj)
                    except:
                        continue
                
                if len(dates) >= 2:
                    sorted_dates = sorted(dates)
                    intervals = []
                    
                    for i in range(1, len(sorted_dates)):
                        interval = (sorted_dates[i] - sorted_dates[i-1]).days
                        intervals.append(interval)
                    
                    if intervals:
                        avg_interval = sum(intervals) / len(intervals)
                        if 25 <= avg_interval <= 35:
                            amounts = [h['amount'] for h in history]
                            if amounts:
                                avg_amount = sum(amounts) / len(amounts)
                                current_amount = abs(float(txn.get('amount', 0)))
                                
                                if 0.9 * avg_amount <= current_amount <= 1.1 * avg_amount:
                                    try:
                                        date_str = txn.get('date', '')
                                        if date_str:
                                            txn_date = datetime.fromisoformat(date_str.split('T')[0])
                                            return True, txn_date.day
                                    except:
                                        return True, None
        
        return False, None
    
    def _detect_subscription_enhanced(self, txn: Dict, merchant: str, merchant_history: Dict) -> Tuple[bool, float]:
        """
        Enhanced subscription detection with confidence score
        Returns: (is_subscription: bool, confidence: float)
        """
        
        merchant_upper = merchant.upper()
        name_upper = (txn.get('name') or '').upper()
        
        # Rule 1: Keyword-based detection (high confidence)
        for keyword in self.SUBSCRIPTION_KEYWORDS:
            if keyword in merchant_upper or keyword in name_upper:
                return True, 0.95
        
        # Rule 2: Pattern-based detection using historical data
        if merchant in merchant_history:
            history = merchant_history[merchant]
            
            if len(history) >= 2:
                dates = []
                amounts = []
                
                for h in history:
                    try:
                        date_obj = datetime.fromisoformat(h['date'].split('T')[0])
                        dates.append(date_obj)
                        amounts.append(h['amount'])
                    except:
                        continue
                
                if len(dates) >= 2:
                    sorted_dates = sorted(dates)
                    intervals = []
                    
                    for i in range(1, len(sorted_dates)):
                        interval = (sorted_dates[i] - sorted_dates[i-1]).days
                        intervals.append(interval)
                    
                    if intervals:
                        avg_interval = sum(intervals) / len(intervals)
                        
                        if 25 <= avg_interval <= 35 or 350 <= avg_interval <= 380:
                            if amounts:
                                avg_amount = sum(amounts) / len(amounts)
                                current_amount = abs(float(txn.get('amount', 0)))
                                
                                if 0.95 * avg_amount <= current_amount <= 1.05 * avg_amount:
                                    confidence = 0.9 if len(history) >= 3 else 0.75
                                    return True, confidence
        
        return False, 0.0
    
    def _save_subscription_from_transaction(self, user_id: str, txn: Dict, merchant_std: str, merchant_history: Dict):
        """Save detected subscription to subscriptions table"""
        try:
            frequency = 'monthly'
            
            if merchant_std in merchant_history:
                history = merchant_history[merchant_std]
                if len(history) >= 2:
                    dates = []
                    for h in history:
                        try:
                            date_obj = datetime.fromisoformat(h['date'].split('T')[0])
                            dates.append(date_obj)
                        except:
                            continue
                    
                    if len(dates) >= 2:
                        sorted_dates = sorted(dates)
                        intervals = []
                        for i in range(1, len(sorted_dates)):
                            interval = (sorted_dates[i] - sorted_dates[i-1]).days
                            intervals.append(interval)
                        
                        if intervals:
                            avg_interval = sum(intervals) / len(intervals)
                            
                            if 25 <= avg_interval <= 35:
                                frequency = 'monthly'
                            elif 350 <= avg_interval <= 380:
                                frequency = 'yearly'
                            elif 85 <= avg_interval <= 95:
                                frequency = 'quarterly'
            
            amount = abs(float(txn.get('amount', 0)))
            start_date = txn.get('date', '').split('T')[0]
            category = self._categorize_by_merchant(merchant_std)
            
            tool = self.toolbox_client.load_tool('upsert-subscription')
            tool(
                user_id=user_id,
                merchant_name=txn.get('merchant_name') or txn.get('name', 'Unknown'),
                merchant_standardized=merchant_std,
                amount=str(amount),
                frequency=frequency,
                start_date=start_date,
                category=category
            )
            
        except Exception as e:
            print(f"Error saving subscription: {e}")
    
    def _categorize_transaction(self, txn: Dict) -> str:
        """Categorize transaction into standard category"""
        
        plaid_cat = txn.get('personal_finance_category')
        
        if plaid_cat:
            try:
                if isinstance(plaid_cat, str):
                    plaid_cat = json.loads(plaid_cat)
                
                primary = plaid_cat.get('primary', '')
                
                if primary in self.PLAID_CATEGORY_MAP:
                    return self.PLAID_CATEGORY_MAP[primary]
                
                detailed = plaid_cat.get('detailed', '')
                if 'GROCERIES' in detailed or 'SUPERMARKETS' in detailed:
                    return 'Groceries'
                elif 'RESTAURANTS' in detailed or 'FAST_FOOD' in detailed or 'COFFEE' in detailed:
                    return 'Dining'
                
            except:
                pass
        
        merchant = (txn.get('merchant_name') or txn.get('name') or '').upper()
        
        for keyword in self.BILL_KEYWORDS:
            if keyword in merchant:
                return 'Bills'
        
        if any(word in merchant for word in ['PAYROLL', 'DEPOSIT', 'SALARY', 'INCOME', 'WAGES']):
            return 'Income'
        elif any(word in merchant for word in ['UBER', 'LYFT', 'TAXI', 'GAS', 'SHELL', 'CHEVRON']):
            return 'Transportation'
        elif any(word in merchant for word in ['RESTAURANT', 'CAFE', 'STARBUCKS', 'MCDONALD', 'CHIPOTLE']):
            return 'Dining'
        elif any(word in merchant for word in ['WHOLE FOODS', 'SAFEWAY', 'KROGER', 'MARKET']):
            return 'Groceries'
        elif any(word in merchant for word in ['NETFLIX', 'SPOTIFY', 'HULU', 'DISNEY', 'HBO']):
            return 'Entertainment'
        elif any(word in merchant for word in ['AMAZON', 'TARGET', 'WALMART']):
            return 'Shopping'
        elif any(word in merchant for word in ['CVS', 'WALGREENS', 'PHARMACY', 'MEDICAL']):
            return 'Healthcare'
        elif any(word in merchant for word in ['PAYMENT', 'CREDIT CARD']):
            return 'Bills'
        elif any(word in merchant for word in ['TRANSFER', 'VENMO', 'ZELLE']):
            return 'Transfers'
        else:
            return 'Other'
    
    def _standardize_merchant_name(self, merchant: str) -> str:
        """Standardize merchant name using pattern matching"""
        if not merchant:
            return 'Unknown'
        
        for pattern, replacement in self.MERCHANT_PATTERNS.items():
            match = re.search(pattern, merchant, re.IGNORECASE)
            if match:
                if r'\1' in replacement:
                    extracted = match.group(1).strip()
                    return extracted.title()
                else:
                    return replacement
        
        cleaned = re.sub(r'^(SQ |TST\*|PAYPAL \*|\*)', '', merchant, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned.title() if cleaned else merchant
    
    def _detect_anomaly(self, txn: Dict, category: str, merchant: str) -> Tuple[bool, float]:
        """Detect if transaction is anomalous"""
        
        try:
            amount = abs(float(txn.get('amount', 0)))
        except:
            return False, 0.0
        
        merchant_upper = merchant.upper()
        name_upper = (txn.get('name') or '').upper()
        
        never_anomaly_keywords = [
            'PAYROLL', 'SALARY', 'DEPOSIT', 'INCOME', 'WAGES',
            'RENT', 'MORTGAGE', 'LEASE',
            'INSURANCE', 'PREMIUM',
            'TUITION', 'EDUCATION',
            'TAX', 'IRS',
            'LOAN', 'CREDIT CARD PAYMENT',
            'TRANSFER', 'SAVINGS'
        ]
        
        for keyword in never_anomaly_keywords:
            if keyword in merchant_upper or keyword in name_upper:
                return False, 0.0
        
        discretionary_categories = ['Dining', 'Entertainment', 'Shopping', 'Transportation']
        
        if category not in discretionary_categories:
            return False, 0.0
        
        category_thresholds = {
            'Dining': 150,
            'Transportation': 200,
            'Entertainment': 150,
            'Shopping': 400
        }
        
        threshold = category_thresholds.get(category, 300)
        
        if amount > threshold * 3:
            return True, 0.95
        elif amount > threshold * 2.5:
            return True, 0.8
        elif amount > threshold * 2:
            return True, 0.6
        
        return False, 0.0
    
    def _save_processed_transaction(self, **data):
        """Save processed transaction with ALL fields"""
        try:
            tool = self.toolbox_client.load_tool('insert-processed-transaction')
            result = tool(**data)
            return result
        except Exception as e:
            print(f"Error saving processed transaction: {e}")
            return None
    
    def _categorize_by_merchant(self, merchant: str) -> str:
        """Determine subscription category based on merchant"""
        merchant_upper = merchant.upper()
        
        if any(word in merchant_upper for word in ['NETFLIX', 'HULU', 'DISNEY', 'HBO', 'PRIME VIDEO']):
            return 'Streaming Services'
        elif any(word in merchant_upper for word in ['SPOTIFY', 'APPLE MUSIC', 'YOUTUBE MUSIC']):
            return 'Music Services'
        elif any(word in merchant_upper for word in ['GYM', 'FITNESS', 'YOGA', 'PELOTON']):
            return 'Health & Fitness'
        elif any(word in merchant_upper for word in ['LINKEDIN', 'ADOBE', 'MICROSOFT', 'GITHUB', 'DROPBOX']):
            return 'Software & Tools'
        elif any(word in merchant_upper for word in ['PHONE', 'INTERNET', 'CABLE', 'UTILITY']):
            return 'Utilities'
        elif any(word in merchant_upper for word in ['AMAZON PRIME']):
            return 'Membership'
        else:
            return 'Subscriptions'
    
    def _calculate_spending_patterns(self, user_id: str) -> Dict:
        """Calculate monthly spending patterns by category"""
        
        now = datetime.now()
        year = now.year
        month = now.month
        
        period_start = datetime(year, month, 1).date()
        if month == 12:
            period_end = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            period_end = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        try:
            tool = self.toolbox_client.load_tool('get-user-transactions')
            transactions = tool(
                user_id=user_id,
                start_date=period_start.isoformat(),
                end_date=period_end.isoformat()
            )
            
            if isinstance(transactions, str):
                transactions = json.loads(transactions)
                
        except Exception as e:
            print(f"Error fetching transactions for patterns: {e}")
            return {'categories': 0}
        
        category_data = defaultdict(list)
        
        for txn in transactions:
            category = self._categorize_transaction(txn)
            try:
                amount = abs(float(txn.get('amount', 0)))
                category_data[category].append(amount)
            except:
                continue
        
        categories_saved = 0
        
        for category, amounts in category_data.items():
            if amounts:
                total = sum(amounts)
                count = len(amounts)
                avg = total / count
                
                try:
                    tool = self.toolbox_client.load_tool('insert-spending-pattern')
                    tool(
                        user_id=user_id,
                        category=category,
                        year=year,
                        month=month,
                        period_start=period_start.isoformat(),
                        period_end=period_end.isoformat(),
                        total_amount=str(total),
                        transaction_count=count,
                        avg_amount=str(avg)
                    )
                    categories_saved += 1
                    print(f"   {category}: ${total:.2f} ({count} txns)")
                    
                except Exception as e:
                    print(f"Error saving pattern for {category}: {e}")
        
        return {'categories': categories_saved}


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("AGENT 1: DATA PROCESSOR - FIXED VERSION")
    print("="*70 + "\n")
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = "82575d97-833e-4bb9-a799-ca19b5bcb9c2"
        print(f"No user_id provided, using default: {user_id}\n")
    
    try:
        agent1 = DataProcessorAgent()
        result = agent1.process_user_transactions(user_id)
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(json.dumps(result, indent=2))
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}\n")
        import traceback
        traceback.print_exc()