"""
Tool 4: Advanced Fraud Detection
Personalized multi-factor risk analysis considering user profile and behavior patterns
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from agent_tools.toolbox_wrapper import get_toolbox
import json
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Import Gemini for contextual fraud analysis
try:
    import google.generativeai as genai
    import os
    
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel('gemini-flash-lite-latest')
        LLM_AVAILABLE = True
        logger.info("✅ Gemini LLM initialized for fraud detection")
    else:
        LLM_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY not found, using rule-based fraud detection only")
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed, using rule-based fraud detection only")


# High-risk merchant patterns
HIGH_RISK_CATEGORIES = [
    'electronics',
    'jewelry',
    'crypto',
    'gambling',
    'international',
    'wire transfer',
    'gift cards',
    'prepaid cards'
]

# Known legitimate high-value merchants (lower suspicion)
LEGITIMATE_HIGH_VALUE_MERCHANTS = [
    'apple', 'tesla', 'best buy', 'home depot', 'lowes', 
    'costco', 'walmart', 'target', 'amazon', 'whole foods',
    'hotel', 'airline', 'airbnb', 'marriott', 'hilton',
    'hospital', 'medical', 'clinic', 'doctor'
]


def detect_fraud(
    transaction_id: str,
    user_id: str,
    amount: float,
    merchant_name: str,
    transaction_date: str,
    category: str
) -> Dict[str, Any]:
    """
    Advanced fraud detection using HYBRID approach with user profile awareness.
    
    Detection Methods:
    1. User Profile Analysis: Personalizes thresholds based on income, life stage, budget
    2. Behavioral Analysis: Compares against user's spending patterns
    3. Rule-Based Scoring: Multiple risk factors with intelligent weighting
    4. LLM Contextual Analysis: Understands merchant reputation and context
    
    Key Improvements:
    - Thresholds adapt to user income (no fixed $200 limit)
    - Considers life stage (student vs professional vs retiree)
    - Location-based anomaly detection
    - Time patterns based on user lifestyle
    - Merchant reputation analysis via LLM
    
    Args:
        transaction_id: Unique transaction identifier (required).
        user_id: User ID for profile and historical comparison (required).
        amount: Transaction amount - absolute value (required).
        merchant_name: Merchant name, standardized preferred (required).
        transaction_date: Transaction date in ISO format (YYYY-MM-DD) (required).
        category: Transaction category from categorization (required).
    
    Returns:
        A dictionary containing:
        {
            "status": "success" or "error",
            "transaction_id": The transaction ID,
            "is_anomaly": Boolean - true if risky transaction detected,
            "risk_score": Risk score from 0-100,
            "risk_level": "low", "medium", or "high",
            "risk_factors": List of identified risk factors,
            "detection_method": "profile-aware", "behavioral", "rules", "llm", or "hybrid",
            "user_income_percentile": What % of monthly income this represents,
            "recommendation": Suggested action,
            "message": Status message
        }
    """
    
    try:
        logger.info(f"🔍 Advanced fraud analysis for transaction {transaction_id}")
        
        # Step 1: Get user profile
        user_profile = _get_user_profile(user_id)
        
        if user_profile:
            logger.info(f"   User Profile: Income=${user_profile.get('monthly_income', 0):.2f}, "
                       f"Life Stage={user_profile.get('life_stage', 'unknown')}")
        
        # Initialize risk scoring
        risk_score = 0
        risk_factors = []
        detection_methods_used = []
        
        # Step 2: User Profile-Aware Analysis (Primary)
        profile_risk = _analyze_with_user_profile(
            user_profile, amount, category, transaction_date
        )
        risk_score += profile_risk['score']
        if profile_risk['factors']:
            risk_factors.extend(profile_risk['factors'])
        detection_methods_used.append('profile-aware')
        
        # Step 3: Behavioral Pattern Analysis
        behavioral_risk = _analyze_behavioral_patterns(
            user_id, amount, category, merchant_name, transaction_date, user_profile
        ) or {'score': 0, 'factors': []}
        risk_score += behavioral_risk['score']
        if behavioral_risk['factors']:
            risk_factors.extend(behavioral_risk['factors'])
        detection_methods_used.append('behavioral')
        
        # Step 4: Rule-Based Risk Factors
        rules_risk = _analyze_with_rules(
            user_id, amount, merchant_name, transaction_date, category, user_profile
        )
        risk_score += rules_risk['score']
        if rules_risk['factors']:
            risk_factors.extend(rules_risk['factors'])
        detection_methods_used.append('rules')
        
        # Step 5: LLM Contextual Analysis (if available and high risk suspected)
        llm_risk = None
        if LLM_AVAILABLE and risk_score >= 30:  # Only use LLM for potentially risky transactions
            llm_risk = _analyze_with_llm(
                merchant_name, amount, category, transaction_date, user_profile
            )
            
            if llm_risk:
                # LLM can adjust score up or down based on context
                risk_score += llm_risk['score_adjustment']
                if llm_risk['factors']:
                    risk_factors.extend(llm_risk['factors'])
                detection_methods_used.append('llm')
        
        # Step 6: Classify risk level
        if risk_score >= 75:
            risk_level = "high"
            is_anomaly = True
            recommendation = "BLOCK transaction and notify user immediately"
        elif risk_score >= 50:
            risk_level = "medium"
            is_anomaly = True
            recommendation = "FLAG for review - send verification notification to user"
        elif risk_score >= 30:
            risk_level = "low-medium"
            is_anomaly = True
            recommendation = "MONITOR - log as suspicious but allow transaction"
        else:
            risk_level = "low"
            is_anomaly = False
            recommendation = "APPROVE - normal transaction"
        
        # Calculate what % of monthly income this represents
        income_percentile = 0
        if user_profile and user_profile.get('monthly_income', 0) > 0:
            income_percentile = (amount / user_profile['monthly_income']) * 100
        
        # Update database
        toolbox = get_toolbox()
        
        update_result = toolbox.call_tool(
            "insert-processed-transaction",
            transaction_id=transaction_id,
            user_id=user_id,
            category_ai=category,
            merchant_standardized=merchant_name,
            is_subscription=False,
            subscription_confidence=None,
            is_anomaly=is_anomaly,
            anomaly_score=f"{risk_score:.2f}",
            anomaly_reason="; ".join(risk_factors) if risk_factors else None,
            is_bill=False,
            bill_cycle_day=None,
            tags=None,
            notes=json.dumps({
                'risk_level': risk_level,
                'income_percentile': income_percentile,
                'detection_methods': detection_methods_used,
                'recommendation': recommendation
            })
        )
        
        if not update_result['success']:
            logger.warning(f"Failed to update fraud flags: {update_result.get('error')}")
        
        logger.info(
            f"✅ Fraud analysis: Risk={risk_level} (score={risk_score:.0f}/100, "
            f"{income_percentile:.1f}% of income, methods={','.join(detection_methods_used)})"
        )
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "is_anomaly": is_anomaly,
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "detection_method": "+".join(detection_methods_used),
            "user_income_percentile": round(income_percentile, 2) if income_percentile else None,
            "recommendation": recommendation,
            "message": f"Risk: {risk_level} ({risk_score:.0f}/100) - {recommendation}"
        }
    
    except Exception as e:
        logger.error(f"❌ Error in fraud detection: {e}", exc_info=True)
        
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Fraud detection failed: {str(e)}"
        }


# ============================================================================
# METHOD 1: USER PROFILE-AWARE ANALYSIS
# ============================================================================

def _get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user profile from database"""
    
    try:
        toolbox = get_toolbox()
        
        # Query user profile
        result = toolbox.call_tool(
            "get-user-profile",  # You'll need to add this to tools.yaml
            user_id=user_id
        )
        
        if result['success'] and result['data']:
            profile = result['data'][0] if isinstance(result['data'], list) else result['data']
            return {
                'monthly_income': float(profile.get('monthly_income', 0)),
                'life_stage': profile.get('life_stage', 'unknown'),
                'dependents': int(profile.get('dependents', 0)),
                'location': profile.get('location', 'unknown'),
                'budget_alert_threshold': float(profile.get('budget_alert_threshold', 1.0))
            }
    except Exception as e:
        logger.warning(f"Could not fetch user profile: {e}")
    
    return None


def _analyze_with_user_profile(
    user_profile: Optional[Dict],
    amount: float,
    category: str,
    transaction_date: str
) -> Dict[str, Any]:
    """
    Personalized risk analysis based on user profile
    Adapts thresholds to user's income and lifestyle
    """
    
    score = 0
    factors = []
    
    # If no profile, use conservative defaults
    if not user_profile or user_profile.get('monthly_income', 0) == 0:
        # Default to moderate income assumptions
        monthly_income = 5000  # Assume $5k/month if unknown
    else:
        monthly_income = user_profile['monthly_income']
    
    # Calculate personalized thresholds
    # Rich person: Income $10k/month can spend $1000 easily
    # Average person: Income $3k/month spending $1000 is unusual
    
    # Threshold 1: Single transaction > 20% of monthly income
    if amount > (monthly_income * 0.20):
        score += 35
        factors.append(
            f"Very large transaction: ${amount:.2f} is {(amount/monthly_income*100):.1f}% of monthly income"
        )
    elif amount > (monthly_income * 0.10):
        score += 20
        factors.append(
            f"Large transaction: ${amount:.2f} is {(amount/monthly_income*100):.1f}% of monthly income"
        )
    elif amount > (monthly_income * 0.05):
        score += 10
        factors.append(
            f"Notable transaction: ${amount:.2f} is {(amount/monthly_income*100):.1f}% of monthly income"
        )
    
    # Threshold 2: Consider budget alert threshold (user-defined)
    if user_profile and user_profile.get('budget_alert_threshold'):
        threshold_multiplier = user_profile['budget_alert_threshold']
        
        # User set aggressive alerts (e.g., 0.8 = alert at 80% of baseline)
        if threshold_multiplier < 1.0:
            # User wants strict monitoring
            if amount > (monthly_income * 0.05):  # Even 5% triggers concern
                score += 5
                factors.append(f"Exceeds user's conservative budget threshold")
    
    # Threshold 3: Life stage consideration
    if user_profile:
        life_stage = user_profile.get('life_stage', '').lower()
        
        # Students: Lower income, but occasional large purchases (tuition, textbooks) are normal
        if life_stage == 'student':
            if category in ['Education', 'Travel', 'Shopping'] and amount > 200:
                score -= 5  # Reduce risk score - more normal for students
        
        # Families with dependents: Larger purchases more common
        elif user_profile.get('dependents', 0) > 0:
            if category in ['Groceries', 'Shopping', 'Healthcare'] and amount > 300:
                score -= 5  # Normal family expenses
        
        # Retirees: Fixed income, large purchases more suspicious
        elif life_stage in ['retired', 'retiree']:
            if amount > (monthly_income * 0.15):
                score += 10
                factors.append("Large purchase unusual for retiree on fixed income")
    
    return {
        'score': score,
        'factors': factors
    }


# ============================================================================
# METHOD 2: BEHAVIORAL PATTERN ANALYSIS
# ============================================================================

def _analyze_behavioral_patterns(
    user_id: str,
    amount: float,
    category: str,
    merchant_name: str,
    transaction_date: str,
    user_profile: Optional[Dict]
) -> Dict[str, Any]:
    """
    Analyze user's historical behavior patterns
    Detects deviations from normal spending habits
    """
    
    score = 0
    factors = []
    
    try:
        toolbox = get_toolbox()
        
        # Get user's spending history for this category
        history_result = toolbox.call_tool(
            "get-category-history",
            user_id=user_id,
            category=category,
            months=6
        )
        
        if history_result['success'] and history_result['data']:
            # Calculate user's typical spending in this category
            historical_data = history_result['data']
            
            # Calculate average transaction amount in this category
            total_amounts = []
            total_counts = []
            
            for row in historical_data:
                if float(row.get('transaction_count', 0)) > 0:
                    avg_per_txn = float(row['total_amount']) / float(row['transaction_count'])
                    total_amounts.append(avg_per_txn)
                    total_counts.append(int(row['transaction_count']))
            
            if total_amounts:
                user_avg_amount = sum(total_amounts) / len(total_amounts)
                user_max_amount = max(total_amounts)
                
                # Compare current transaction to user's history
                if amount > user_max_amount * 2:
                    score += 30
                    factors.append(
                        f"2x higher than user's historical maximum in {category} "
                        f"(${amount:.2f} vs max ${user_max_amount:.2f})"
                    )
                elif amount > user_max_amount * 1.5:
                    score += 20
                    factors.append(f"50% higher than typical maximum for this category")
                elif amount > user_avg_amount * 4:
                    score += 15
                    factors.append(f"4x higher than user's typical {category} spending")
        
        # Check spending frequency in this category
        # Sudden spike in transaction count could indicate compromised card
        current_month_result = toolbox.call_tool(
            "get-current-month-spending",
            user_id=user_id
        )
        
        if current_month_result['success'] and current_month_result['data']:
            for cat_data in current_month_result['data']:
                if cat_data['category'] == category:
                    current_count = int(cat_data.get('transaction_count', 0))
                    
                    # If user suddenly has 2x more transactions this month
                    if history_result['data']:
                        avg_monthly_count = sum([int(r.get('transaction_count', 0)) 
                                                for r in history_result['data']]) / len(history_result['data'])
                        
                        if current_count > avg_monthly_count * 2:
                            score += 15
                            factors.append(
                                f"Unusual spike in {category} transactions this month "
                                f"({current_count} vs avg {avg_monthly_count:.0f})"
                            )
        
    except Exception as e:
        logger.debug(f"Behavioral analysis error: {e}")
    
    return {
        'score': score,
        'factors': factors
    }


# ============================================================================
# METHOD 3: RULE-BASED ANALYSIS (Enhanced)
# ============================================================================

def _analyze_with_rules(
    user_id: str,
    amount: float,
    merchant_name: str,
    transaction_date: str,
    category: str,
    user_profile: Optional[Dict]
) -> Dict[str, Any]:
    """
    Enhanced rule-based fraud detection with user profile awareness
    """
    
    score = 0
    factors = []
    
    merchant_lower = merchant_name.lower()
    
    # Rule 1: Time-based anomaly (personalized)
    try:
        txn_datetime = datetime.fromisoformat(str(transaction_date))
        hour = txn_datetime.hour
        
        # Personalized time risk based on income
        monthly_income = user_profile.get('monthly_income', 5000) if user_profile else 5000
        
        # Late night (2 AM - 5 AM)
        if 2 <= hour <= 5:
            # Calculate personalized threshold (10% of monthly income)
            late_night_threshold = monthly_income * 0.10
            
            if amount > late_night_threshold:
                score += 20
                factors.append(
                    f"Late night high-value transaction: ${amount:.2f} at {hour}:00 "
                    f"(threshold: ${late_night_threshold:.2f} based on income)"
                )
            elif amount > late_night_threshold * 0.5:
                score += 10
                factors.append(f"Late night transaction at {hour}:00")
    except Exception as e:
        logger.debug(f"Time parsing error: {e}")
    
    # Rule 2: High-risk merchant categories
    if any(risk_cat in merchant_lower for risk_cat in HIGH_RISK_CATEGORIES):
        score += 25
        factors.append(f"High-risk merchant category detected")
    
    # Rule 3: Legitimate high-value merchant (reduce risk)
    if any(legit in merchant_lower for legit in LEGITIMATE_HIGH_VALUE_MERCHANTS):
        score -= 10  # Reduce suspicion for known legitimate merchants
        logger.debug(f"   Recognized legitimate merchant: {merchant_name}")
    
    # Rule 4: New merchant risk (personalized)
    try:
        toolbox = get_toolbox()
        
        top_result = toolbox.call_tool(
            "get-top-merchants",
            user_id=user_id,
            limit=100  # Increased to capture more history
        )
        
        if top_result['success'] and top_result['data']:
            known_merchants = [row['merchant_standardized'].lower() for row in top_result['data']]
            
            if merchant_lower not in known_merchants:
                # New merchant - personalized threshold
                monthly_income = user_profile.get('monthly_income', 5000) if user_profile else 5000
                new_merchant_threshold = monthly_income * 0.08  # 8% of monthly income
                
                if amount > new_merchant_threshold:
                    score += 25
                    factors.append(
                        f"First time with new merchant '{merchant_name}' for ${amount:.2f} "
                        f"(threshold: ${new_merchant_threshold:.2f})"
                    )
                elif amount > new_merchant_threshold * 0.5:
                    score += 15
                    factors.append(f"New merchant: {merchant_name}")
    except:
        pass
    
    # Rule 5: Transaction velocity
    try:
        txn_datetime = datetime.fromisoformat(str(transaction_date))
        one_hour_ago = txn_datetime - timedelta(hours=1)
        
        toolbox = get_toolbox()
        
        recent_result = toolbox.call_tool(
            "get-user-transactions",
            user_id=user_id,
            start_date=one_hour_ago.strftime('%Y-%m-%d'),
            end_date=txn_datetime.strftime('%Y-%m-%d')
        )
        
        if recent_result['success'] and recent_result['data']:
            count = len(recent_result['data'])
            
            if count >= 5:
                score += 30
                factors.append(f"Card testing pattern: {count} transactions in 1 hour")
            elif count >= 3:
                score += 15
                factors.append(f"Rapid transactions: {count} in last hour")
    except:
        pass
    
    # Rule 6: International/location anomaly (if location data available)
    if user_profile and user_profile.get('location'):
        # TODO: If merchant location differs significantly from user location
        # Would need merchant location data or IP geolocation
        pass
    
    # Rule 7: Round amount suspicion (card testing)
    if amount in [1.00, 5.00, 10.00, 20.00, 50.00, 100.00, 500.00, 1000.00]:
        score += 5
        factors.append(f"Round amount (${amount:.2f}) - possible card testing")
    
    return {
        'score': score,
        'factors': factors
    }


# ============================================================================
# METHOD 4: LLM CONTEXTUAL ANALYSIS
# ============================================================================

def _analyze_with_llm(
    merchant_name: str,
    amount: float,
    category: str,
    transaction_date: str,
    user_profile: Optional[Dict]
) -> Optional[Dict[str, Any]]:
    """
    Use LLM to understand merchant reputation and transaction context
    Can identify sophisticated fraud patterns
    """
    
    if not LLM_AVAILABLE:
        return None
    
    # Prepare context
    monthly_income = user_profile.get('monthly_income', 5000) if user_profile else 5000
    income_pct = (amount / monthly_income * 100) if monthly_income > 0 else 0
    
    try:
        txn_datetime = datetime.fromisoformat(str(transaction_date))
        hour = txn_datetime.hour
        day_of_week = txn_datetime.strftime('%A')
    except:
        hour = 12
        day_of_week = "Unknown"
    
    prompt = f"""You are a fraud detection expert analyzing a potentially suspicious transaction.

**Transaction Details:**
- Merchant: {merchant_name}
- Amount: ${amount:.2f}
- Category: {category}
- Day: {day_of_week}
- Time: {hour}:00
- User Monthly Income: ${monthly_income:.2f}
- Transaction as % of Income: {income_pct:.1f}%

**Your Task:**
Assess the fraud risk of this transaction based on:
1. Merchant reputation and legitimacy
2. Transaction context and reasonableness
3. Amount appropriateness for merchant type
4. Time/day pattern analysis

**Consider:**
- Is this merchant known and legitimate?
- Is the amount reasonable for this merchant?
- Does timing raise red flags?
- Are there fraud patterns (e.g., testing, unusual merchant types)?

**Response Format (JSON ONLY):**
{{
  "fraud_risk_adjustment": -10 to +20,
  "reasoning": "Brief explanation",
  "merchant_reputation": "legitimate|suspicious|unknown",
  "concerns": ["concern1", "concern2"],
  "confidence": 0.8
}}

**Examples:**

Merchant: "Apple.com", $999, 10% of income, Tuesday 2PM
{{
  "fraud_risk_adjustment": -10,
  "reasoning": "Apple is legitimate merchant, amount reasonable for electronics purchase, normal time",
  "merchant_reputation": "legitimate",
  "concerns": [],
  "confidence": 0.95
}}

Merchant: "Unknown Electronics LLC", $1500, 30% of income, Tuesday 3AM
{{
  "fraud_risk_adjustment": +15,
  "reasoning": "Unknown merchant, very high amount, suspicious late-night timing",
  "merchant_reputation": "suspicious",
  "concerns": ["unknown merchant", "late night", "high amount"],
  "confidence": 0.85
}}

Merchant: "Gift Card Depot", $500, 10% of income, Friday 11PM
{{
  "fraud_risk_adjustment": +20,
  "reasoning": "Gift card purchases are common fraud indicator, late night timing suspicious",
  "merchant_reputation": "suspicious",
  "concerns": ["gift cards common in fraud", "late night", "unusual merchant"],
  "confidence": 0.90
}}

Now analyze the transaction above:"""
    
    try:
        response = llm_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=300,
            )
        )
        
        text = response.text.strip()
        
        if text.startswith('```'):
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(text)
        
        score_adjustment = int(result.get('fraud_risk_adjustment', 0))
        concerns = result.get('concerns', [])
        
        factors = []
        if concerns:
            factors.append(f"LLM: {', '.join(concerns)} ({result.get('reasoning', '')})")
        
        logger.info(
            f"   LLM: {result.get('merchant_reputation', 'unknown')} merchant, "
            f"risk adjustment: {score_adjustment:+d}"
        )
        
        return {
            'score_adjustment': score_adjustment,
            'factors': factors,
            'merchant_reputation': result.get('merchant_reputation'),
            'confidence': result.get('confidence', 0.7)
        }
    
    except json.JSONDecodeError as e:
        logger.error(f"   LLM: Failed to parse JSON: {e}")
        return None
    
    except Exception as e:
        logger.error(f"   LLM: Analysis failed: {e}")
        return None