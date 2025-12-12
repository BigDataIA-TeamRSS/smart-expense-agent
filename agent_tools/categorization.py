"""
Tool 2: Categorize Transaction
Hybrid approach: LLM + Rule-based logic for maximum accuracy
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from agent_tools.toolbox_wrapper import get_toolbox
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Import Gemini for LLM categorization
try:
    import google.generativeai as genai
    import os
    
    # Configure Gemini
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        llm_model = genai.GenerativeModel('gemini-flash-lite-latest')
        LLM_AVAILABLE = True
        logger.info("✅ Gemini LLM initialized for categorization")
    else:
        LLM_AVAILABLE = False
        logger.warning("⚠️ GEMINI_API_KEY not found, using rule-based categorization only")
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed, using rule-based categorization only")


# Category definitions
CATEGORIES = [
    "Food & Dining",
    "Groceries", 
    "Transportation",
    "Shopping",
    "Bills & Utilities",
    "Entertainment",
    "Healthcare",
    "Travel",
    "Personal Care",
    "Education",
    "Subscriptions",
    "Income",
    "Transfer",
    "Other"
]


def categorize_transaction(
    transaction_id: str,
    merchant_name: str,
    amount: float,
    description: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Categorizes a transaction using HYBRID approach (LLM + Rules) and standardizes merchant name.
    This tool should be called for EACH transaction after fetching them.
    
    Hybrid Strategy:
    1. Standardize merchant name using intelligent rules
    2. Get LLM categorization (if available)
    3. Get rule-based categorization (always)
    4. Combine both results for highest accuracy
    5. Store result in database
    
    Args:
        transaction_id: Unique transaction identifier (required).
        merchant_name: Raw merchant name from the transaction (required).
        amount: Transaction amount - use absolute value (required).
        description: Transaction description text (required).
        user_id: User ID for database storage (required).
    
    Returns:
        A dictionary containing:
        {
            "status": "success" or "error",
            "transaction_id": The transaction ID,
            "category": Assigned category (e.g., "Food & Dining"),
            "merchant_standardized": Cleaned/standardized merchant name,
            "confidence": Confidence score (0.0-1.0),
            "tags": List of relevant tags,
            "method": "llm", "rules", or "hybrid",
            "message": Status message
        }
    """
    
    try:
        logger.info(f"🏷️ Categorizing transaction {transaction_id}: {merchant_name}")
        
        # Step 1: Standardize merchant name
        merchant_standardized = _standardize_merchant_name(merchant_name)
        logger.info(f"   Standardized: {merchant_name} → {merchant_standardized}")
        
        # Step 2: Get LLM categorization (if available)
        llm_result = None
        if LLM_AVAILABLE:
            try:
                llm_result = _categorize_with_llm(
                    merchant=merchant_name,
                    merchant_standardized=merchant_standardized,
                    amount=abs(amount),
                    description=description
                )
                logger.info(f"   LLM: {llm_result['category']} (confidence: {llm_result['confidence']:.2f})")
            except Exception as e:
                logger.warning(f"   LLM categorization failed: {e}")
        
        # Step 3: Get rule-based categorization (always as fallback)
        rules_result = _categorize_with_rules(
            merchant=merchant_name,
            merchant_standardized=merchant_standardized,
            amount=abs(amount),
            description=description
        )
        logger.info(f"   Rules: {rules_result['category']} (confidence: {rules_result['confidence']:.2f})")
        
        # Step 4: Combine results intelligently
        final_result = _combine_categorization_results(llm_result, rules_result)
        
        logger.info(f"   ✅ FINAL: {final_result['category']} (method: {final_result['method']}, confidence: {final_result['confidence']:.2f})")
        
        # Step 5: Store in processed_transactions via MCP tool
        toolbox = get_toolbox()
        
        store_result = toolbox.call_tool(
            "insert-processed-transaction",
            transaction_id=transaction_id,
            user_id=user_id,
            category_ai=final_result['category'],
            merchant_standardized=merchant_standardized,
            is_subscription=False,  # Will be updated by subscription detector
            subscription_confidence=None,
            is_anomaly=False,  # Will be updated by fraud detector
            anomaly_score="0.00",
            anomaly_reason=None,
            is_bill=False,
            bill_cycle_day=None,
            tags=json.dumps(final_result.get('tags', [])) if final_result.get('tags') else None,
            notes=final_result.get('reasoning')
        )
        
        if not store_result['success']:
            return {
                "status": "error",
                "transaction_id": transaction_id,
                "message": f"Failed to store categorization: {store_result.get('error')}"
            }
        
        return {
            "status": "success",
            "transaction_id": transaction_id,
            "category": final_result['category'],
            "merchant_standardized": merchant_standardized,
            "confidence": final_result['confidence'],
            "tags": final_result.get('tags', []),
            "method": final_result['method'],
            "message": f"Successfully categorized as {final_result['category']} (via {final_result['method']})"
        }
    
    except Exception as e:
        logger.error(f"❌ Error categorizing transaction {transaction_id}: {e}", exc_info=True)
        
        return {
            "status": "error",
            "transaction_id": transaction_id,
            "message": f"Categorization failed: {str(e)}"
        }


# ============================================================================
# MERCHANT STANDARDIZATION
# ============================================================================

def _standardize_merchant_name(raw_merchant: str) -> str:
    """
    Intelligent merchant name standardization
    Cleans and normalizes merchant names for consistency
    """
    if not raw_merchant:
        return "Unknown"
    
    # Convert to uppercase for matching
    merchant_upper = raw_merchant.upper()
    
    # Step 1: Known merchant mappings (most accurate)
    MERCHANT_MAPPINGS = {
        # E-commerce
        'AMZN': 'Amazon',
        'AMAZON': 'Amazon',
        'AMAZON.COM': 'Amazon',
        'AMAZON MARKETPLACE': 'Amazon',
        'AMZ': 'Amazon',
        
        # Grocery
        'WM SUPERCENTER': 'Walmart',
        'WALMART': 'Walmart',
        'WAL-MART': 'Walmart',
        'WHOLEFDS': 'Whole Foods',
        'WHOLE FOODS': 'Whole Foods',
        'TRADER JOE': 'Trader Joe\'s',
        'SAFEWAY': 'Safeway',
        'KROGER': 'Kroger',
        
        # Food & Dining
        'MCDONALD': 'McDonald\'s',
        'MCDONALDS': 'McDonald\'s',
        'STARB': 'Starbucks',
        'STARBUCKS': 'Starbucks',
        'CHIPOTLE': 'Chipotle',
        'SUBWAY': 'Subway',
        'PANERA': 'Panera Bread',
        'DOMINO': 'Domino\'s Pizza',
        'PIZZA HUT': 'Pizza Hut',
        
        # Transportation
        'UBER': 'Uber',
        'LYFT': 'Lyft',
        'SHELL': 'Shell Gas',
        'CHEVRON': 'Chevron',
        'EXXON': 'ExxonMobil',
        'BP': 'BP Gas',
        '76': '76 Gas',
        
        # Subscriptions
        'NETFLIX': 'Netflix',
        'SPOTIFY': 'Spotify',
        'HULU': 'Hulu',
        'DISNEY': 'Disney+',
        'HBO': 'HBO Max',
        'AMAZON PRIME': 'Amazon Prime',
        'APPLE.COM': 'Apple',
        'APPLE.COM/BILL': 'Apple',
        'YOUTUBE': 'YouTube Premium',
        'GOOGLE': 'Google',
        
        # Utilities
        'VERIZON': 'Verizon',
        'AT&T': 'AT&T',
        'ATT': 'AT&T',
        'TMOBILE': 'T-Mobile',
        'T-MOBILE': 'T-Mobile',
        'COMCAST': 'Comcast',
        'XFINITY': 'Xfinity',
        
        # Retail
        'TARGET': 'Target',
        'COSTCO': 'Costco',
        'CVS': 'CVS Pharmacy',
        'WALGREENS': 'Walgreens',
        'BEST BUY': 'Best Buy',
        'HOME DEPOT': 'Home Depot',
        'LOWES': 'Lowe\'s',
        
        # Payment processors (remove)
        'SQ *': '',
        'TST*': '',
        'PAYPAL *': '',
    }
    
    # Check for exact matches first
    for pattern, replacement in MERCHANT_MAPPINGS.items():
        if pattern in merchant_upper:
            if replacement:  # Not empty (like SQ *)
                return replacement
            else:
                # Remove pattern and continue processing
                raw_merchant = raw_merchant.replace(pattern, '').strip()
    
    # Step 2: Remove common prefixes/suffixes
    merchant = raw_merchant
    
    # Remove payment processor prefixes
    prefixes_to_remove = [
        r'^SQ \*',
        r'^AMZN\*',
        r'^TST\*',
        r'^WM ',
        r'^PAYPAL \*',
        r'^GOOGLE \*',
        r'^APPLE\.COM\*',
    ]
    
    for prefix in prefixes_to_remove:
        merchant = re.sub(prefix, '', merchant, flags=re.IGNORECASE)
    
    # Step 3: Remove store numbers and IDs
    merchant = re.sub(r'#\d+', '', merchant)  # #1234
    merchant = re.sub(r'\s+\d{4,}$', '', merchant)  # trailing numbers
    merchant = re.sub(r'\s+\d{3}-\d{3}-\d{4}', '', merchant)  # phone numbers
    
    # Step 4: Remove locations/addresses
    merchant = re.sub(r'\s+(CA|NY|TX|FL|IL|PA|OH|GA|NC|MI)\s+\d{5}', '', merchant, flags=re.IGNORECASE)
    merchant = re.sub(r'\s+[A-Z]{2}\s+\d{5}', '', merchant)  # State + ZIP
    
    # Step 5: Clean up
    merchant = merchant.strip()
    merchant = ' '.join(merchant.split())  # Remove extra spaces
    
    # Step 6: Title case for readability
    if merchant.isupper() or merchant.islower():
        merchant = merchant.title()
    
    return merchant if merchant else "Unknown"


# ============================================================================
# LLM-BASED CATEGORIZATION
# ============================================================================

def _categorize_with_llm(
    merchant: str,
    merchant_standardized: str,
    amount: float,
    description: str
) -> Optional[Dict[str, Any]]:
    """
    Use Gemini LLM to categorize transaction with detailed prompt template
    """
    
    if not LLM_AVAILABLE:
        return None
    
    # Comprehensive prompt template
    prompt = f"""You are a financial transaction categorization expert. Analyze this transaction and provide accurate categorization.

**Transaction Details:**
- Original Merchant Name: {merchant}
- Standardized Merchant: {merchant_standardized}
- Amount: ${amount:.2f}
- Description: {description}

**Your Task:**
1. Categorize this transaction into ONE of these categories:
{chr(10).join(f"   - {cat}" for cat in CATEGORIES)}

2. Consider these factors:
   - Merchant name patterns (e.g., "Starbucks" → Food & Dining)
   - Industry knowledge (e.g., "Netflix" → Subscriptions)
   - Amount context (large amounts at gas stations → Transportation)
   - Description keywords
   - Common spending patterns

3. Provide reasoning for your choice

**Response Format (JSON ONLY):**
{{
  "category": "Category Name",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this category fits",
  "tags": ["relevant", "tags"],
  "merchant_context": "What this merchant typically sells/provides"
}}

**Examples:**

Transaction: Starbucks #1234, $5.50
{{
  "category": "Food & Dining",
  "confidence": 0.98,
  "reasoning": "Starbucks is a coffee shop chain, clearly food & beverage",
  "tags": ["coffee", "cafe", "beverages"],
  "merchant_context": "Coffee shop serving beverages and light food"
}}

Transaction: Netflix.com, $15.99
{{
  "category": "Subscriptions",
  "confidence": 0.99,
  "reasoning": "Netflix is a monthly streaming service subscription",
  "tags": ["streaming", "entertainment", "monthly"],
  "merchant_context": "Video streaming subscription service"
}}

Transaction: Shell Gas #5678, $45.00
{{
  "category": "Transportation",
  "confidence": 0.97,
  "reasoning": "Shell is a gas station, amount typical for fuel purchase",
  "tags": ["fuel", "gas", "vehicle"],
  "merchant_context": "Gas station for vehicle fuel"
}}

Transaction: Unknown Merchant, $1250.00
{{
  "category": "Other",
  "confidence": 0.60,
  "reasoning": "Merchant name unclear, cannot determine category confidently",
  "tags": ["unknown", "large-amount"],
  "merchant_context": "Unknown merchant type"
}}

**IMPORTANT:**
- Respond with ONLY the JSON object, no markdown, no explanation outside JSON
- Category MUST be exactly one of the {len(CATEGORIES)} provided categories
- Confidence should reflect certainty (0.6-0.7 = uncertain, 0.8-0.9 = confident, 0.95+ = very confident)
- Be conservative with confidence - if unsure, use 0.7 or lower

Now categorize the transaction above:"""
    
    try:
        # Call Gemini
        response = llm_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistency
                max_output_tokens=300,
            )
        )
        
        # Parse JSON response
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            # Extract content between ```json and ```
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        result = json.loads(text)
        
        # Validate category
        if result['category'] not in CATEGORIES:
            logger.warning(f"LLM returned invalid category: {result['category']}, defaulting to 'Other'")
            result['category'] = 'Other'
            result['confidence'] = max(result['confidence'] - 0.2, 0.5)
        
        # Ensure confidence is in valid range
        result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))
        
        return result
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Raw LLM response: {text}")
        return None
    
    except Exception as e:
        logger.error(f"LLM categorization error: {e}")
        return None


# ============================================================================
# RULE-BASED CATEGORIZATION
# ============================================================================

def _categorize_with_rules(
    merchant: str,
    merchant_standardized: str,
    amount: float,
    description: str
) -> Dict[str, Any]:
    """
    Rule-based categorization using keyword matching
    Always returns a result (fallback-safe)
    """
    
    merchant_lower = merchant_standardized.lower()
    desc_lower = description.lower() if description else ""
    combined_text = f"{merchant_lower} {desc_lower}"
    
    # Define rules with priority (checked in order)
    rules = [
        # Income (positive amounts)
        {
            'category': 'Income',
            'keywords': ['deposit', 'payroll', 'salary', 'direct dep', 'transfer from'],
            'condition': lambda: amount > 0,
            'confidence': 0.95,
            'tags': ['income', 'deposit']
        },
        
        # Subscriptions (high confidence if recurring keywords)
        {
            'category': 'Subscriptions',
            'keywords': ['netflix', 'spotify', 'hulu', 'disney', 'prime', 'apple music', 
                        'youtube premium', 'subscription', 'monthly'],
            'confidence': 0.92,
            'tags': ['subscription', 'recurring']
        },
        
        # Food & Dining
        {
            'category': 'Food & Dining',
            'keywords': ['starbucks', 'mcdonald', 'burger', 'pizza', 'restaurant', 'cafe',
                        'coffee', 'chipotle', 'subway', 'taco', 'kfc', 'wendy', 'chick-fil-a',
                        'panera', 'dunkin', 'domino', 'food', 'dining', 'bar', 'grill'],
            'confidence': 0.88,
            'tags': ['food', 'dining', 'restaurant']
        },
        
        # Groceries
        {
            'category': 'Groceries',
            'keywords': ['walmart', 'whole foods', 'safeway', 'kroger', 'trader joe', 
                        'albertsons', 'publix', 'wegmans', 'grocery', 'supermarket', 
                        'market', 'food lion', 'aldi', 'costco'],
            'confidence': 0.90,
            'tags': ['groceries', 'food', 'household']
        },
        
        # Transportation
        {
            'category': 'Transportation',
            'keywords': ['uber', 'lyft', 'gas', 'shell', 'chevron', 'exxon', 'bp', '76',
                        'parking', 'transit', 'metro', 'taxi', 'fuel', 'toll', 'car wash'],
            'confidence': 0.87,
            'tags': ['transport', 'vehicle']
        },
        
        # Bills & Utilities
        {
            'category': 'Bills & Utilities',
            'keywords': ['electric', 'water', 'internet', 'phone', 'utility', 'verizon',
                        'at&t', 'tmobile', 'comcast', 'xfinity', 'bill', 'utilities',
                        'insurance', 'rent', 'mortgage'],
            'confidence': 0.89,
            'tags': ['bills', 'utilities', 'recurring']
        },
        
        # Shopping
        {
            'category': 'Shopping',
            'keywords': ['amazon', 'target', 'ebay', 'best buy', 'apple store', 'walmart',
                        'macy', 'nordstrom', 'store', 'shop', 'retail', 'clothing',
                        'fashion', 'mall'],
            'confidence': 0.82,
            'tags': ['shopping', 'retail']
        },
        
        # Entertainment
        {
            'category': 'Entertainment',
            'keywords': ['gym', 'fitness', 'movie', 'theater', 'cinema', 'concert', 'event',
                        'tickets', 'amusement', 'games', 'entertainment', 'sports'],
            'confidence': 0.85,
            'tags': ['entertainment', 'leisure']
        },
        
        # Healthcare
        {
            'category': 'Healthcare',
            'keywords': ['doctor', 'hospital', 'pharmacy', 'cvs', 'walgreens', 'medical',
                        'clinic', 'health', 'dental', 'vision', 'prescription', 'medicine'],
            'confidence': 0.90,
            'tags': ['health', 'medical']
        },
        
        # Travel
        {
            'category': 'Travel',
            'keywords': ['hotel', 'airbnb', 'flight', 'airline', 'booking', 'expedia',
                        'marriott', 'hilton', 'airport', 'travel', 'vacation', 'resort'],
            'confidence': 0.88,
            'tags': ['travel', 'vacation']
        },
        
        # Education
        {
            'category': 'Education',
            'keywords': ['university', 'college', 'school', 'tuition', 'course', 'udemy',
                        'coursera', 'education', 'learning', 'books', 'textbook'],
            'confidence': 0.86,
            'tags': ['education', 'learning']
        },
        
        # Personal Care
        {
            'category': 'Personal Care',
            'keywords': ['salon', 'spa', 'haircut', 'barber', 'massage', 'beauty',
                        'cosmetics', 'sephora', 'ulta', 'personal care'],
            'confidence': 0.84,
            'tags': ['personal-care', 'beauty']
        },
    ]
    
    # Check rules in order
    for rule in rules:
        # Check keywords
        if any(keyword in combined_text for keyword in rule['keywords']):
            # Check condition if present
            if 'condition' in rule:
                if not rule['condition']():
                    continue
            
            return {
                'category': rule['category'],
                'confidence': rule['confidence'],
                'tags': rule['tags'],
                'reasoning': f"Rule-based: matched keywords {rule['keywords'][:3]}"
            }
    
    # Default fallback
    return {
        'category': 'Other',
        'confidence': 0.60,
        'tags': ['uncategorized'],
        'reasoning': 'No matching rules found'
    }


# ============================================================================
# RESULT COMBINATION
# ============================================================================

def _combine_categorization_results(
    llm_result: Optional[Dict[str, Any]],
    rules_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Intelligently combine LLM and rule-based results
    
    Strategy:
    1. If both agree on category: use highest confidence, mark as "hybrid"
    2. If LLM has high confidence (>0.85): trust LLM
    3. If rules have high confidence (>0.85) and LLM low: trust rules
    4. If both disagree with medium confidence: trust LLM (usually better)
    5. If LLM unavailable: use rules only
    """
    
    # Case 1: No LLM result - use rules only
    if llm_result is None:
        return {
            **rules_result,
            'method': 'rules'
        }
    
    llm_category = llm_result['category']
    llm_confidence = llm_result['confidence']
    
    rules_category = rules_result['category']
    rules_confidence = rules_result['confidence']
    
    # Case 2: Both agree on category - boost confidence
    if llm_category == rules_category:
        return {
            'category': llm_category,
            'confidence': min(0.98, max(llm_confidence, rules_confidence) + 0.05),  # Boost for agreement
            'tags': list(set(llm_result.get('tags', []) + rules_result.get('tags', []))),  # Combine tags
            'reasoning': f"Agreement: LLM ({llm_confidence:.2f}) and Rules ({rules_confidence:.2f})",
            'method': 'hybrid'
        }
    
    # Case 3: LLM has very high confidence - trust it
    if llm_confidence >= 0.85:
        return {
            **llm_result,
            'method': 'llm',
            'reasoning': f"LLM high confidence ({llm_confidence:.2f}) vs Rules ({rules_category}, {rules_confidence:.2f})"
        }
    
    # Case 4: Rules have high confidence, LLM is uncertain - trust rules
    if rules_confidence >= 0.85 and llm_confidence < 0.75:
        return {
            **rules_result,
            'method': 'rules',
            'reasoning': f"Rules high confidence ({rules_confidence:.2f}) vs LLM uncertain ({llm_confidence:.2f})"
        }
    
    # Case 5: Both disagree with medium confidence - trust LLM (context awareness)
    if llm_confidence >= 0.70:
        return {
            **llm_result,
            'method': 'llm',
            'reasoning': f"LLM preferred ({llm_confidence:.2f}) over Rules ({rules_category}, {rules_confidence:.2f})"
        }
    
    # Case 6: LLM has low confidence - trust rules
    return {
        **rules_result,
        'method': 'rules',
        'reasoning': f"Rules preferred ({rules_confidence:.2f}) - LLM uncertain ({llm_confidence:.2f})"
    }