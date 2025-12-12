"""
Tool 3: Detect Subscriptions
HYBRID approach: Pattern Analysis + LLM + Rule-based for maximum accuracy
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from agent_tools.toolbox_wrapper import get_toolbox
import json
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Import Gemini for LLM analysis
try:
    import google.generativeai as genai
    import os
    
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel('gemini-flash-lite-latest')
        LLM_AVAILABLE = True
        logger.info("✅ Gemini LLM initialized for subscription detection")
    else:
        LLM_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY not found, using pattern analysis only")
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed, using pattern analysis only")


# Known subscription services (high confidence)
KNOWN_SUBSCRIPTIONS = {
    # Streaming
    'netflix': {'type': 'streaming', 'typical_amount': 15.99, 'frequency': 'monthly'},
    'spotify': {'type': 'streaming', 'typical_amount': 10.99, 'frequency': 'monthly'},
    'hulu': {'type': 'streaming', 'typical_amount': 14.99, 'frequency': 'monthly'},
    'disney': {'type': 'streaming', 'typical_amount': 13.99, 'frequency': 'monthly'},
    'disney+': {'type': 'streaming', 'typical_amount': 13.99, 'frequency': 'monthly'},
    'hbo max': {'type': 'streaming', 'typical_amount': 15.99, 'frequency': 'monthly'},
    'youtube premium': {'type': 'streaming', 'typical_amount': 11.99, 'frequency': 'monthly'},
    'amazon prime': {'type': 'streaming', 'typical_amount': 14.99, 'frequency': 'monthly'},
    'paramount': {'type': 'streaming', 'typical_amount': 9.99, 'frequency': 'monthly'},
    'peacock': {'type': 'streaming', 'typical_amount': 5.99, 'frequency': 'monthly'},
    
    # Music
    'apple music': {'type': 'music', 'typical_amount': 10.99, 'frequency': 'monthly'},
    'tidal': {'type': 'music', 'typical_amount': 9.99, 'frequency': 'monthly'},
    'pandora': {'type': 'music', 'typical_amount': 9.99, 'frequency': 'monthly'},
    
    # Software/Cloud
    'adobe': {'type': 'software', 'typical_amount': 54.99, 'frequency': 'monthly'},
    'microsoft 365': {'type': 'software', 'typical_amount': 6.99, 'frequency': 'monthly'},
    'office 365': {'type': 'software', 'typical_amount': 6.99, 'frequency': 'monthly'},
    'dropbox': {'type': 'cloud', 'typical_amount': 11.99, 'frequency': 'monthly'},
    'icloud': {'type': 'cloud', 'typical_amount': 2.99, 'frequency': 'monthly'},
    'google one': {'type': 'cloud', 'typical_amount': 1.99, 'frequency': 'monthly'},
    
    # Fitness
    'peloton': {'type': 'fitness', 'typical_amount': 44.00, 'frequency': 'monthly'},
    'planet fitness': {'type': 'fitness', 'typical_amount': 10.00, 'frequency': 'monthly'},
    '24 hour fitness': {'type': 'fitness', 'typical_amount': 49.99, 'frequency': 'monthly'},
    'la fitness': {'type': 'fitness', 'typical_amount': 34.99, 'frequency': 'monthly'},
    
    # News/Media
    'new york times': {'type': 'news', 'typical_amount': 17.00, 'frequency': 'monthly'},
    'washington post': {'type': 'news', 'typical_amount': 9.99, 'frequency': 'monthly'},
    'wall street journal': {'type': 'news', 'typical_amount': 38.99, 'frequency': 'monthly'},
    
    # Gaming
    'playstation plus': {'type': 'gaming', 'typical_amount': 9.99, 'frequency': 'monthly'},
    'xbox game pass': {'type': 'gaming', 'typical_amount': 14.99, 'frequency': 'monthly'},
    'nintendo online': {'type': 'gaming', 'typical_amount': 3.99, 'frequency': 'monthly'},
    
    # Meal/Food
    'hello fresh': {'type': 'meal-kit', 'typical_amount': 60.00, 'frequency': 'weekly'},
    'blue apron': {'type': 'meal-kit', 'typical_amount': 47.95, 'frequency': 'weekly'},
    'doordash': {'type': 'food-delivery', 'typical_amount': 9.99, 'frequency': 'monthly'},
    'uber eats': {'type': 'food-delivery', 'typical_amount': 9.99, 'frequency': 'monthly'},
}


def detect_subscriptions(user_id: str) -> Dict[str, Any]:
    """
    Detects recurring subscription patterns using HYBRID approach.
    
    Three-pronged strategy:
    1. Pattern Analysis: Analyzes transaction intervals and amounts
    2. LLM Intelligence: Identifies subscription services by context
    3. Rule-based: Matches against known subscription services
    
    Should be called AFTER all transactions are categorized.
    
    Args:
        user_id: The user's ID to analyze subscriptions for (required).
    
    Returns:
        A dictionary containing:
        {
            "status": "success" or "error",
            "subscriptions_detected": Number of subscriptions found/updated,
            "subscriptions": List of detected subscriptions with:
                - merchant: Merchant name
                - amount: Subscription amount
                - frequency: "monthly", "quarterly", "yearly", or "weekly"
                - category: Spending category
                - confidence: Detection confidence
                - detection_method: "pattern", "llm", "rules", or "hybrid"
            "message": Status message
        }
    """
    
    try:
        logger.info(f"🔍 Detecting subscriptions for user: {user_id}")
        
        toolbox = get_toolbox()
        
        # Get user's transactions from last 12 months (longer for better pattern detection)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 12 months
        
        result = toolbox.call_tool(
            "get-user-transactions",
            user_id=user_id,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not result['success']:
            return {
                "status": "error",
                "subscriptions_detected": 0,
                "subscriptions": [],
                "message": f"Failed to fetch transactions: {result.get('error')}"
            }
        
        transactions = result['data'] if isinstance(result['data'], list) else []
        
        # Filter only debits (negative amounts)
        transactions = [t for t in transactions if float(t.get('amount', 0)) < 0]
        
        logger.info(f"   Analyzing {len(transactions)} transactions for patterns")
        
        # Group by merchant
        merchant_groups = defaultdict(list)
        for txn in transactions:
            merchant = txn.get('merchant_name', 'Unknown')
            if merchant and merchant != 'Unknown':
                merchant_groups[merchant].append(txn)
        
        detected_subscriptions = []
        
        # Analyze each merchant group with HYBRID approach
        for merchant, txns in merchant_groups.items():
            logger.info(f"   Analyzing: {merchant} ({len(txns)} transactions)")
            
            # Method 1: Pattern Analysis
            pattern_result = _analyze_pattern(merchant, txns)
            
            # Method 2: Rule-based Known Subscriptions
            rules_result = _check_known_subscription(merchant, txns)
            
            # Method 3: LLM Analysis (if available)
            llm_result = None
            if LLM_AVAILABLE and len(txns) >= 1:  # LLM can identify even with 1 transaction
                llm_result = _analyze_with_llm(merchant, txns)
            
            # Combine all methods
            final_result = _combine_subscription_results(
                pattern_result, 
                rules_result, 
                llm_result,
                merchant,
                txns
            )
            
            if final_result:
                # Store subscription via MCP tool
                store_result = toolbox.call_tool(
                    "upsert-subscription",
                    user_id=user_id,
                    merchant_name=merchant,
                    merchant_standardized=final_result['merchant_standardized'],
                    amount=str(final_result['amount']),
                    frequency=final_result['frequency'],
                    start_date=final_result['start_date'],
                    category=final_result.get('category', 'Subscriptions')
                )
                
                if store_result['success']:
                    detected_subscriptions.append({
                        'merchant': final_result['merchant_standardized'],
                        'amount': final_result['amount'],
                        'frequency': final_result['frequency'],
                        'category': final_result.get('category', 'Subscriptions'),
                        'confidence': final_result.get('confidence', 0.7),
                        'detection_method': final_result.get('method', 'hybrid')
                    })
                    
                    logger.info(
                        f"   ✅ {final_result['merchant_standardized']}: "
                        f"${abs(final_result['amount']):.2f} {final_result['frequency']} "
                        f"(confidence: {final_result.get('confidence', 0.7):.2f}, "
                        f"method: {final_result.get('method', 'hybrid')})"
                    )
        
        logger.info(f"✅ Subscription detection complete: {len(detected_subscriptions)} found")
        
        return {
            "status": "success",
            "subscriptions_detected": len(detected_subscriptions),
            "subscriptions": detected_subscriptions,
            "message": f"Detected {len(detected_subscriptions)} subscriptions using hybrid approach"
        }
    
    except Exception as e:
        logger.error(f"❌ Error detecting subscriptions: {e}", exc_info=True)
        return {
            "status": "error",
            "subscriptions_detected": 0,
            "subscriptions": [],
            "message": f"Subscription detection failed: {str(e)}"
        }


# ============================================================================
# METHOD 1: PATTERN ANALYSIS (Original Logic)
# ============================================================================

def _analyze_pattern(merchant: str, transactions: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Analyze transaction patterns for recurring subscriptions
    Looks at intervals, amounts, and consistency
    """
    
    if len(transactions) < 2:
        return None
    
    # Sort by date
    transactions = sorted(transactions, key=lambda x: x['date'])
    
    # Calculate intervals between transactions
    intervals = []
    for i in range(1, len(transactions)):
        try:
            prev_date = datetime.fromisoformat(str(transactions[i-1]['date']))
            curr_date = datetime.fromisoformat(str(transactions[i]['date']))
            days = (curr_date - prev_date).days
            intervals.append(days)
        except:
            continue
    
    if not intervals:
        return None
    
    # Check amount consistency (±5%)
    amounts = [abs(float(txn['amount'])) for txn in transactions]
    avg_amount = sum(amounts) / len(amounts)
    amount_variance = max(abs(amt - avg_amount) / avg_amount for amt in amounts) if avg_amount > 0 else 0
    
    if amount_variance > 0.05:  # More than 5% variance
        logger.debug(f"   Pattern: {merchant} - Amount variance too high ({amount_variance:.2%})")
        return None
    
    # Detect frequency
    avg_interval = sum(intervals) / len(intervals)
    interval_std = (sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)) ** 0.5
    
    frequency = _classify_frequency(avg_interval, interval_std)
    
    if not frequency:
        logger.debug(f"   Pattern: {merchant} - No clear frequency pattern")
        return None
    
    # Calculate confidence
    confidence = _calculate_pattern_confidence(len(transactions), interval_std, amount_variance)
    
    if confidence < 0.6:  # Minimum confidence threshold
        logger.debug(f"   Pattern: {merchant} - Confidence too low ({confidence:.2f})")
        return None
    
    logger.info(f"   Pattern: {merchant} - Detected {frequency} pattern (confidence: {confidence:.2f})")
    
    return {
        'amount': avg_amount,
        'frequency': frequency,
        'confidence': confidence,
        'method': 'pattern',
        'occurrence_count': len(transactions)
    }


def _classify_frequency(avg_interval: float, std_dev: float) -> Optional[str]:
    """Classify payment frequency based on intervals"""
    
    # Weekly: 7 days ± 2 days
    if 5 <= avg_interval <= 9 and std_dev < 3:
        return 'weekly'
    
    # Bi-weekly: 14 days ± 3 days
    if 11 <= avg_interval <= 17 and std_dev < 4:
        return 'monthly'  # Treat bi-weekly as monthly for simplicity
    
    # Monthly: 28-31 days ± 4 days
    if 24 <= avg_interval <= 35 and std_dev < 5:
        return 'monthly'
    
    # Quarterly: 90 days ± 10 days
    if 80 <= avg_interval <= 100 and std_dev < 10:
        return 'quarterly'
    
    # Yearly: 365 days ± 20 days
    if 345 <= avg_interval <= 385 and std_dev < 20:
        return 'yearly'
    
    return None


def _calculate_pattern_confidence(occurrence_count: int, interval_std: float, amount_variance: float) -> float:
    """Calculate confidence based on pattern consistency"""
    
    # Base confidence from occurrence count
    if occurrence_count >= 6:
        confidence = 0.95
    elif occurrence_count >= 4:
        confidence = 0.85
    elif occurrence_count >= 3:
        confidence = 0.75
    else:
        confidence = 0.65
    
    # Penalize for interval inconsistency
    if interval_std > 5:
        confidence -= 0.15
    elif interval_std > 3:
        confidence -= 0.10
    
    # Penalize for amount variance
    if amount_variance > 0.03:
        confidence -= 0.10
    elif amount_variance > 0.02:
        confidence -= 0.05
    
    return max(confidence, 0.5)


# ============================================================================
# METHOD 2: RULE-BASED KNOWN SUBSCRIPTIONS
# ============================================================================

def _check_known_subscription(merchant: str, transactions: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Check if merchant matches known subscription services
    High confidence if name matches and amount/frequency align
    """
    
    merchant_lower = merchant.lower()
    
    # Check against known subscriptions
    for known_name, sub_info in KNOWN_SUBSCRIPTIONS.items():
        if known_name in merchant_lower:
            # Calculate average amount from transactions
            amounts = [abs(float(txn['amount'])) for txn in transactions]
            avg_amount = sum(amounts) / len(amounts) if amounts else 0
            
            # Check if amount is close to typical amount (±30% tolerance)
            typical_amount = sub_info['typical_amount']
            amount_diff_pct = abs(avg_amount - typical_amount) / typical_amount if typical_amount > 0 else 1
            
            # High confidence if amount matches
            if amount_diff_pct < 0.30:  # Within 30%
                confidence = 0.92
            else:
                confidence = 0.80  # Still high confidence based on name
            
            logger.info(
                f"   Rules: {merchant} - Matched known subscription '{known_name}' "
                f"(confidence: {confidence:.2f})"
            )
            
            return {
                'amount': avg_amount,
                'frequency': sub_info['frequency'],
                'confidence': confidence,
                'method': 'rules',
                'subscription_type': sub_info['type']
            }
    
    return None


# ============================================================================
# METHOD 3: LLM-BASED SUBSCRIPTION IDENTIFICATION
# ============================================================================

def _analyze_with_llm(merchant: str, transactions: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Use LLM to identify if merchant is a subscription service
    Even with limited transaction history
    """
    
    if not LLM_AVAILABLE:
        return None
    
    # Prepare transaction summary
    amounts = [abs(float(txn['amount'])) for txn in transactions]
    avg_amount = sum(amounts) / len(amounts) if amounts else 0
    
    # Get dates
    dates = []
    for txn in transactions:
        try:
            dates.append(datetime.fromisoformat(str(txn['date'])))
        except:
            continue
    
    dates.sort()
    date_range = f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}" if dates else "Unknown"
    
    # Build prompt
    prompt = f"""You are a financial analyst expert in identifying subscription services.

**Merchant Analysis:**
- Merchant Name: {merchant}
- Number of Transactions: {len(transactions)}
- Average Amount: ${avg_amount:.2f}
- Date Range: {date_range}

**Your Task:**
Determine if this merchant is a SUBSCRIPTION SERVICE (recurring billing service).

**Subscription Indicators:**
- Streaming services (Netflix, Spotify, Hulu, etc.)
- Software/SaaS (Adobe, Microsoft 365, Dropbox, etc.)
- Gym memberships
- News/media subscriptions
- Cloud storage (iCloud, Google One, etc.)
- Gaming services (PlayStation Plus, Xbox Game Pass, etc.)
- Meal kits (HelloFresh, Blue Apron, etc.)
- Any service with recurring monthly/yearly charges

**NOT Subscriptions:**
- One-time purchases (even if same merchant)
- Variable utility bills (electricity, water)
- Irregular shopping (Amazon purchases that vary)
- Occasional dining or groceries

**Response Format (JSON ONLY):**
{{
  "is_subscription": true or false,
  "confidence": 0.95,
  "subscription_type": "streaming|software|fitness|news|cloud|gaming|meal-kit|other",
  "expected_frequency": "weekly|monthly|quarterly|yearly",
  "reasoning": "Brief explanation",
  "typical_amount_range": "low|medium|high"
}}

**Examples:**

Merchant: "Netflix.com", 3 transactions, $15.99 avg
{{
  "is_subscription": true,
  "confidence": 0.99,
  "subscription_type": "streaming",
  "expected_frequency": "monthly",
  "reasoning": "Netflix is a well-known streaming subscription service",
  "typical_amount_range": "medium"
}}

Merchant: "Amazon.com", 5 transactions, $42.30 avg
{{
  "is_subscription": false,
  "confidence": 0.85,
  "reasoning": "Amazon shows variable amounts typical of shopping, not recurring subscription",
  "typical_amount_range": "variable"
}}

Merchant: "Spotify", 2 transactions, $10.99 avg
{{
  "is_subscription": true,
  "confidence": 0.98,
  "subscription_type": "music",
  "expected_frequency": "monthly",
  "reasoning": "Spotify is a music streaming subscription service",
  "typical_amount_range": "low"
}}

Merchant: "Planet Fitness", 4 transactions, $10.00 avg
{{
  "is_subscription": true,
  "confidence": 0.95,
  "subscription_type": "fitness",
  "expected_frequency": "monthly",
  "reasoning": "Planet Fitness is a gym with monthly membership fees",
  "typical_amount_range": "medium"
}}

**IMPORTANT:**
- Respond with ONLY the JSON object
- Be conservative: if uncertain, set is_subscription to false
- High confidence (0.9+) only for well-known services
- Consider merchant name patterns carefully

Now analyze the merchant above:"""
    
    try:
        response = llm_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=300,
            )
        )
        
        # Parse JSON
        text = response.text.strip()
        
        if text.startswith('```'):
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(text)
        
        # Validate
        is_subscription = result.get('is_subscription', False)
        
        if not is_subscription:
            logger.info(f"   LLM: {merchant} - Not a subscription (confidence: {result.get('confidence', 0):.2f})")
            return None
        
        confidence = float(result.get('confidence', 0.7))
        frequency = result.get('expected_frequency', 'monthly')
        
        logger.info(
            f"   LLM: {merchant} - Identified as {result.get('subscription_type', 'subscription')} "
            f"(confidence: {confidence:.2f}, frequency: {frequency})"
        )
        
        return {
            'amount': avg_amount,
            'frequency': frequency,
            'confidence': confidence,
            'method': 'llm',
            'subscription_type': result.get('subscription_type', 'other'),
            'reasoning': result.get('reasoning', '')
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"   LLM: Failed to parse JSON response: {e}")
        return None
    
    except Exception as e:
        logger.error(f"   LLM: Analysis failed: {e}")
        return None


# ============================================================================
# RESULT COMBINATION
# ============================================================================

def _combine_subscription_results(
    pattern_result: Optional[Dict],
    rules_result: Optional[Dict],
    llm_result: Optional[Dict],
    merchant: str,
    transactions: List[Dict]
) -> Optional[Dict[str, Any]]:
    """
    Intelligently combine all three detection methods
    
    Priority:
    1. All three agree → Highest confidence (hybrid)
    2. Rules + LLM agree → High confidence (even without pattern)
    3. Rules + Pattern agree → High confidence
    4. LLM + Pattern agree → High confidence
    5. Single method with high confidence → Use it
    6. Disagreement → Trust highest confidence method
    """
    
    # Count how many methods detected a subscription
    methods_detected = sum([
        pattern_result is not None,
        rules_result is not None,
        llm_result is not None
    ])
    
    if methods_detected == 0:
        return None
    
    # Prepare merchant standardization
    import re
    merchant_clean = re.sub(r'#\d+', '', merchant).strip().title()
    
    # Calculate start date
    dates = sorted([datetime.fromisoformat(str(t['date'])) for t in transactions])
    start_date = dates[0].strftime('%Y-%m-%d') if dates else datetime.now().strftime('%Y-%m-%d')
    
    # Get category (prefer from transactions)
    category = transactions[0].get('category', 'Subscriptions') if transactions else 'Subscriptions'
    
    # Case 1: All three methods agree
    if methods_detected == 3:
        # Use average amount and most conservative frequency
        amounts = [r['amount'] for r in [pattern_result, rules_result, llm_result] if r]
        avg_amount = sum(amounts) / len(amounts)
        
        # Use pattern frequency if available, else rules
        frequency = pattern_result['frequency'] if pattern_result else rules_result['frequency']
        
        # Boost confidence
        confidences = [r['confidence'] for r in [pattern_result, rules_result, llm_result] if r]
        max_confidence = max(confidences)
        
        logger.info(f"   Combined: All 3 methods agree! (confidence boosted to {min(0.98, max_confidence + 0.05):.2f})")
        
        return {
            'merchant_standardized': merchant_clean,
            'amount': avg_amount,
            'frequency': frequency,
            'start_date': start_date,
            'category': category,
            'confidence': min(0.98, max_confidence + 0.05),
            'method': 'hybrid-all-three'
        }
    
    # Case 2: Two methods agree
    if methods_detected == 2:
        # Determine which two
        if pattern_result and rules_result:
            avg_amount = (pattern_result['amount'] + rules_result['amount']) / 2
            frequency = pattern_result['frequency']  # Prefer pattern for frequency
            confidence = max(pattern_result['confidence'], rules_result['confidence']) + 0.03
            method = 'hybrid-pattern-rules'
        
        elif pattern_result and llm_result:
            avg_amount = (pattern_result['amount'] + llm_result['amount']) / 2
            frequency = pattern_result['frequency']  # Prefer pattern for frequency
            confidence = max(pattern_result['confidence'], llm_result['confidence']) + 0.03
            method = 'hybrid-pattern-llm'
        
        else:  # rules_result and llm_result
            avg_amount = (rules_result['amount'] + llm_result['amount']) / 2
            frequency = rules_result['frequency']  # Prefer rules for known subscriptions
            confidence = max(rules_result['confidence'], llm_result['confidence']) + 0.03
            method = 'hybrid-rules-llm'
        
        logger.info(f"   Combined: 2 methods agree! (confidence: {min(0.95, confidence):.2f}, method: {method})")
        
        return {
            'merchant_standardized': merchant_clean,
            'amount': avg_amount,
            'frequency': frequency,
            'start_date': start_date,
            'category': category,
            'confidence': min(0.95, confidence),
            'method': method
        }
    
    # Case 3: Only one method detected (use highest confidence)
    single_result = pattern_result or rules_result or llm_result
    
    # Only accept single-method detection if confidence is high enough
    if single_result['confidence'] < 0.75:
        logger.info(f"   Combined: Single method but confidence too low ({single_result['confidence']:.2f})")
        return None
    
    logger.info(f"   Combined: Single method ({single_result['method']}) with confidence {single_result['confidence']:.2f}")
    
    return {
        'merchant_standardized': merchant_clean,
        'amount': single_result['amount'],
        'frequency': single_result['frequency'],
        'start_date': start_date,
        'category': category,
        'confidence': single_result['confidence'],
        'method': single_result['method']
    }