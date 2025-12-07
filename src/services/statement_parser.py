"""
Universal Bank Statement PDF Parser
Handles PDFs from any US bank using Gemini + Pydantic.

SECURITY: PII is sanitized before sending to LLM.

Usage:
    from src.services.statement_parser import StatementParser
    
    parser = StatementParser(api_key="your_gemini_key")
    result = parser.parse("path/to/statement.pdf")
    print(result.transactions)
"""

import io
import json
import re
import hashlib
import time
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import logging

import pdfplumber
from pydantic import BaseModel, Field, field_validator

# Import PII sanitizer
try:
    from src.services.pii_sanitizer import PIISanitizer, SanitizationResult
except ImportError:
    # Fallback if running standalone
    from pii_sanitizer import PIISanitizer, SanitizationResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============== Enums ==============

class TransactionType(str, Enum):
    CREDIT = "credit"   # Money coming in
    DEBIT = "debit"     # Money going out


class BankType(str, Enum):
    CHASE_CHECKING = "chase_checking"
    CHASE_CREDIT = "chase_credit"
    BANK_OF_AMERICA_CHECKING = "boa_checking"
    BANK_OF_AMERICA_CREDIT = "boa_credit"
    WELLS_FARGO_CHECKING = "wells_fargo_checking"
    WELLS_FARGO_CREDIT = "wells_fargo_credit"
    CAPITAL_ONE = "capital_one"
    DISCOVER = "discover"
    AMEX = "amex"
    CITI = "citi"
    US_BANK = "us_bank"
    PNC = "pnc"
    TD_BANK = "td_bank"
    REGIONS = "regions"
    FIFTH_THIRD = "fifth_third"
    HUNTINGTON = "huntington"
    NAVY_FEDERAL = "navy_federal"
    USAA = "usaa"
    ALLY = "ally"
    MARCUS = "marcus"
    SOFI = "sofi"
    CHIME = "chime"
    UNKNOWN = "unknown"


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    MONEY_MARKET = "money_market"
    UNKNOWN = "unknown"


# ============== Pydantic Models ==============

class ParsedTransaction(BaseModel):
    """Single transaction extracted from statement."""
    
    transaction_id: str = ""
    date: date
    description: str
    original_description: str = ""
    amount: float
    transaction_type: TransactionType
    category: Optional[str] = None
    balance_after: Optional[float] = None
    location: Optional[str] = None
    is_recurring: bool = False
    pending: bool = False
    check_number: Optional[str] = None
    reference_number: Optional[str] = None
    
    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        if isinstance(v, (int, float, Decimal)):
            return abs(float(v))
        if isinstance(v, str):
            cleaned = re.sub(r'[$,]', '', v.strip())
            # Handle parentheses for negative: (123.45)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = cleaned[1:-1]
            cleaned = cleaned.replace('-', '')
            try:
                return abs(float(cleaned)) if cleaned else 0.0
            except ValueError:
                return 0.0
        return 0.0
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Try common formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            # Last resort - try to parse
            try:
                from dateutil import parser as date_parser
                return date_parser.parse(v).date()
            except:
                pass
        raise ValueError(f"Cannot parse date: {v}")
    
    def generate_id(self) -> str:
        """Generate unique transaction ID based on content."""
        content = f"{self.date}_{self.description[:30]}_{self.amount}"
        return f"pdf_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "transaction_id": self.transaction_id or self.generate_id(),
            "date": str(self.date),
            "description": self.description,
            "original_description": self.original_description,
            "amount": self.amount,
            "transaction_type": self.transaction_type.value,
            "category": self.category,
            "balance_after": self.balance_after,
            "location": self.location,
            "is_recurring": self.is_recurring,
            "pending": self.pending,
            "check_number": self.check_number,
            "reference_number": self.reference_number
        }
    
    def to_plaid_format(self, account_id: str) -> Dict[str, Any]:
        """Convert to Plaid-compatible format."""
        if not self.transaction_id:
            self.transaction_id = self.generate_id()
        
        # Plaid format: positive = spent, negative = received
        plaid_amount = self.amount if self.transaction_type == TransactionType.DEBIT else -self.amount
        
        return {
            "transaction_id": self.transaction_id,
            "account_id": account_id,
            "amount": plaid_amount,
            "date": str(self.date),
            "name": self.description,
            "merchant_name": self.description.split()[0] if self.description else None,
            "category": [self.category] if self.category else ["Uncategorized"],
            "pending": self.pending,
            "payment_channel": "other",
            "transaction_type": "place" if self.transaction_type == TransactionType.DEBIT else "credit",
            "source": "pdf_upload",
            "original_description": self.original_description or self.description
        }


class AccountInfo(BaseModel):
    """Account information from statement header."""
    
    account_holder: Optional[str] = None
    account_number_last4: Optional[str] = None
    account_number_masked: Optional[str] = None
    account_type: AccountType = AccountType.UNKNOWN
    bank_name: Optional[str] = None
    bank_type: BankType = BankType.UNKNOWN
    statement_start_date: Optional[date] = None
    statement_end_date: Optional[date] = None
    routing_number: Optional[str] = None
    
    @field_validator('statement_start_date', 'statement_end_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_holder": self.account_holder,
            "account_number_last4": self.account_number_last4,
            "account_number_masked": self.account_number_masked,
            "account_type": self.account_type.value,
            "bank_name": self.bank_name,
            "bank_type": self.bank_type.value,
            "statement_start_date": str(self.statement_start_date) if self.statement_start_date else None,
            "statement_end_date": str(self.statement_end_date) if self.statement_end_date else None,
            "routing_number": self.routing_number
        }


class StatementSummary(BaseModel):
    """Summary totals from the statement."""
    
    # Universal fields
    beginning_balance: Optional[float] = None
    ending_balance: Optional[float] = None
    total_deposits: Optional[float] = None
    total_withdrawals: Optional[float] = None
    total_fees: Optional[float] = None
    
    # Credit card specific
    previous_balance: Optional[float] = None
    new_balance: Optional[float] = None
    payments_credits: Optional[float] = None
    purchases: Optional[float] = None
    cash_advances: Optional[float] = None
    balance_transfers: Optional[float] = None
    fees_charged: Optional[float] = None
    interest_charged: Optional[float] = None
    credit_limit: Optional[float] = None
    available_credit: Optional[float] = None
    minimum_payment: Optional[float] = None
    payment_due_date: Optional[date] = None
    apr_purchase: Optional[str] = None
    apr_cash_advance: Optional[str] = None
    rewards_earned: Optional[int] = None
    rewards_balance: Optional[int] = None
    
    @field_validator('payment_due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: (str(v) if isinstance(v, date) else v) for k, v in self.__dict__.items() if v is not None}


class ParsedStatement(BaseModel):
    """Complete parsed bank statement."""
    
    account_info: AccountInfo
    summary: StatementSummary
    transactions: List[ParsedTransaction]
    parsing_confidence: float = Field(ge=0, le=1, default=0.8)
    parsing_notes: List[str] = Field(default_factory=list)
    source_filename: str = ""
    parsed_at: str = ""
    raw_text_length: int = 0
    page_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire statement to dictionary."""
        return {
            "account_info": self.account_info.to_dict(),
            "summary": self.summary.to_dict(),
            "transactions": [t.to_dict() for t in self.transactions],
            "parsing_confidence": self.parsing_confidence,
            "parsing_notes": self.parsing_notes,
            "source_filename": self.source_filename,
            "parsed_at": self.parsed_at,
            "raw_text_length": self.raw_text_length,
            "page_count": self.page_count,
            "transaction_count": len(self.transactions)
        }
    
    def save_json(self, output_path: Union[str, Path]) -> str:
        """Save parsed statement to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        
        return str(output_path)
    
    def get_transactions_df(self):
        """Get transactions as pandas DataFrame."""
        try:
            import pandas as pd
            return pd.DataFrame([t.to_dict() for t in self.transactions])
        except ImportError:
            raise ImportError("pandas required for DataFrame output")


# ============== Bank Detection ==============

BANK_PATTERNS = {
    # Chase
    (r'chase.*freedom|freedom.*flex|chase.*sapphire|chase.*slate|chase.*ink', BankType.CHASE_CREDIT, AccountType.CREDIT_CARD),
    (r'amazon.*visa.*chase|chase.*amazon', BankType.CHASE_CREDIT, AccountType.CREDIT_CARD),
    (r'chase.*checking|total\s+checking', BankType.CHASE_CHECKING, AccountType.CHECKING),
    (r'chase.*savings', BankType.CHASE_CHECKING, AccountType.SAVINGS),
    
    # Bank of America
    (r'bank\s*of\s*america.*credit|boa.*credit|bofa.*credit', BankType.BANK_OF_AMERICA_CREDIT, AccountType.CREDIT_CARD),
    (r'bank\s*of\s*america|bofa|boa\s+checking', BankType.BANK_OF_AMERICA_CHECKING, AccountType.CHECKING),
    
    # Wells Fargo
    (r'wells\s*fargo.*credit|wells.*active\s*cash|wells.*propel', BankType.WELLS_FARGO_CREDIT, AccountType.CREDIT_CARD),
    (r'wells\s*fargo', BankType.WELLS_FARGO_CHECKING, AccountType.CHECKING),
    
    # Capital One
    (r'capital\s*one.*quicksilver|capital\s*one.*savor|capital\s*one.*venture', BankType.CAPITAL_ONE, AccountType.CREDIT_CARD),
    (r'capital\s*one', BankType.CAPITAL_ONE, AccountType.CREDIT_CARD),
    
    # Discover
    (r'discover.*card|discover.*it|discover.*cashback', BankType.DISCOVER, AccountType.CREDIT_CARD),
    
    # American Express
    (r'american\s*express|amex|platinum\s*card|gold\s*card|blue\s*cash', BankType.AMEX, AccountType.CREDIT_CARD),
    
    # Citi
    (r'citi.*double|citi.*custom|citi.*premier|citi.*diamond', BankType.CITI, AccountType.CREDIT_CARD),
    (r'citibank|citi\s+checking', BankType.CITI, AccountType.CHECKING),
    
    # Other banks
    (r'us\s*bank|u\.s\.\s*bank', BankType.US_BANK, AccountType.CHECKING),
    (r'pnc\s*bank|pnc\s+checking', BankType.PNC, AccountType.CHECKING),
    (r'td\s*bank', BankType.TD_BANK, AccountType.CHECKING),
    (r'regions\s*bank', BankType.REGIONS, AccountType.CHECKING),
    (r'fifth\s*third', BankType.FIFTH_THIRD, AccountType.CHECKING),
    (r'huntington', BankType.HUNTINGTON, AccountType.CHECKING),
    (r'navy\s*federal', BankType.NAVY_FEDERAL, AccountType.CHECKING),
    (r'usaa', BankType.USAA, AccountType.CHECKING),
    (r'ally\s*bank', BankType.ALLY, AccountType.CHECKING),
    (r'marcus.*goldman|goldman.*marcus', BankType.MARCUS, AccountType.SAVINGS),
    (r'sofi', BankType.SOFI, AccountType.CHECKING),
    (r'chime', BankType.CHIME, AccountType.CHECKING),
}


def detect_bank_type(text: str) -> tuple[BankType, AccountType]:
    """Detect bank and account type from statement text."""
    text_lower = text.lower()
    
    # Check patterns
    for pattern, bank_type, account_type in BANK_PATTERNS:
        if re.search(pattern, text_lower):
            return bank_type, account_type
    
    # Fallback detection by keywords
    is_credit_card = any(kw in text_lower for kw in [
        'credit limit', 'minimum payment due', 'apr', 'annual percentage rate',
        'interest charge', 'payment due date', 'new balance', 'credit card'
    ])
    
    if is_credit_card:
        return BankType.UNKNOWN, AccountType.CREDIT_CARD
    
    is_checking = any(kw in text_lower for kw in [
        'checking', 'direct deposit', 'atm withdrawal', 'debit card',
        'beginning balance', 'ending balance'
    ])
    
    if is_checking:
        return BankType.UNKNOWN, AccountType.CHECKING
    
    if 'savings' in text_lower:
        return BankType.UNKNOWN, AccountType.SAVINGS
    
    return BankType.UNKNOWN, AccountType.UNKNOWN


def get_bank_display_name(bank_type: BankType) -> str:
    """Get human-readable bank name."""
    names = {
        BankType.CHASE_CHECKING: "Chase",
        BankType.CHASE_CREDIT: "Chase",
        BankType.BANK_OF_AMERICA_CHECKING: "Bank of America",
        BankType.BANK_OF_AMERICA_CREDIT: "Bank of America",
        BankType.WELLS_FARGO_CHECKING: "Wells Fargo",
        BankType.WELLS_FARGO_CREDIT: "Wells Fargo",
        BankType.CAPITAL_ONE: "Capital One",
        BankType.DISCOVER: "Discover",
        BankType.AMEX: "American Express",
        BankType.CITI: "Citi",
        BankType.US_BANK: "US Bank",
        BankType.PNC: "PNC Bank",
        BankType.TD_BANK: "TD Bank",
        BankType.REGIONS: "Regions Bank",
        BankType.FIFTH_THIRD: "Fifth Third Bank",
        BankType.HUNTINGTON: "Huntington Bank",
        BankType.NAVY_FEDERAL: "Navy Federal",
        BankType.USAA: "USAA",
        BankType.ALLY: "Ally Bank",
        BankType.MARCUS: "Marcus by Goldman Sachs",
        BankType.SOFI: "SoFi",
        BankType.CHIME: "Chime",
        BankType.UNKNOWN: "Unknown Bank"
    }
    return names.get(bank_type, "Unknown Bank")


# ============== PDF Text Extraction ==============

def extract_text_from_pdf(pdf_source: Union[str, bytes, Path]) -> tuple[str, int]:
    """
    Extract text from PDF with table-aware processing.
    Returns (text, page_count).
    """
    all_text = []
    page_count = 0
    
    try:
        if isinstance(pdf_source, (str, Path)):
            pdf_file = pdfplumber.open(pdf_source)
        else:
            pdf_file = pdfplumber.open(io.BytesIO(pdf_source))
        
        with pdf_file as pdf:
            page_count = len(pdf.pages)
            
            for i, page in enumerate(pdf.pages):
                page_text = []
                
                # Extract tables first (better for transaction data)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if row and any(cell for cell in row if cell):
                                clean_row = [str(c).strip() if c else '' for c in row]
                                clean_row = [c for c in clean_row if c]
                                if clean_row:
                                    page_text.append(' | '.join(clean_row))
                
                # Also get regular text
                text = page.extract_text()
                if text:
                    page_text.append(text)
                
                if page_text:
                    all_text.append(f"\n{'='*20} PAGE {i+1} {'='*20}\n")
                    all_text.extend(page_text)
    
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Could not extract text from PDF: {str(e)}")
    
    full_text = '\n'.join(all_text)
    
    if len(full_text) < 100:
        raise ValueError("PDF appears to be empty or image-based. Text-based PDFs required.")
    
    return full_text, page_count


# ============== Prompt Builder ==============

def build_parsing_prompt(text: str, bank_type: BankType, account_type: AccountType, previous_errors: Optional[List[str]] = None) -> str:
    """Build the Gemini prompt based on detected bank/account type.
    
    Args:
        text: The statement text to parse
        bank_type: Detected bank type
        account_type: Detected account type
        previous_errors: Optional list of error messages from previous attempts
    """
    
    # Bank-specific hints
    bank_hints = {
        BankType.CHASE_CREDIT: "Chase credit card: Look for ACCOUNT ACTIVITY section. Purchases=DEBIT, Payments=CREDIT.",
        BankType.CHASE_CHECKING: "Chase checking: Look for TRANSACTION DETAIL. Deposits=CREDIT, Withdrawals/Zelle sent=DEBIT.",
        BankType.BANK_OF_AMERICA_CREDIT: "Bank of America credit: Look for Transaction Details. Purchases=DEBIT, Payments=CREDIT.",
        BankType.BANK_OF_AMERICA_CHECKING: "Bank of America checking: Look for Deposits/Withdrawals sections.",
        BankType.WELLS_FARGO_CREDIT: "Wells Fargo credit: Look for Transaction History.",
        BankType.WELLS_FARGO_CHECKING: "Wells Fargo checking: Look for Account Activity.",
        BankType.CAPITAL_ONE: "Capital One: Look for Transactions section. Purchases=DEBIT, Payments=CREDIT.",
        BankType.DISCOVER: "Discover: Look for Account Activity. Purchases=DEBIT, Cashback/Payments=CREDIT.",
        BankType.AMEX: "American Express: Look for Activity. Charges=DEBIT, Payments/Credits=CREDIT.",
        BankType.CITI: "Citi: Look for Account Activity section.",
    }
    
    bank_hint = bank_hints.get(bank_type, "Parse this bank statement carefully.")
    
    # Account type specific rules
    if account_type == AccountType.CREDIT_CARD:
        type_rules = """
For CREDIT CARDS:
- Purchases, charges, fees = DEBIT (money you owe)
- Payments, refunds, credits, cashback = CREDIT (reduces what you owe)
- Extract: credit limit, minimum payment, due date, APR, rewards if shown"""
    else:
        type_rules = """
For CHECKING/SAVINGS:
- Deposits, transfers in, refunds, income = CREDIT (money received)
- Withdrawals, purchases, transfers out, bills, Zelle sent = DEBIT (money spent)
- Extract: beginning balance, ending balance"""

    # Build error context if previous errors exist
    error_context = ""
    if previous_errors:
        error_context = f"""

⚠️ PREVIOUS ATTEMPT ERRORS (DO NOT REPEAT THESE MISTAKES):
{chr(10).join(f"- {error}" for error in previous_errors)}

IMPORTANT: The previous parsing attempt failed due to the errors above. Please:
1. Carefully review the error messages and understand what went wrong
2. Ensure all values are valid (e.g., dates are valid YYYY-MM-DD format)
3. Double-check all values before returning.
"""

    return f"""You are a financial document parser. Parse this bank statement and extract ALL transactions.

BANK DETECTED: {get_bank_display_name(bank_type)}
ACCOUNT TYPE: {account_type.value}
{bank_hint}
{type_rules}
{error_context}
STATEMENT TEXT:
{text}

CRITICAL RULES:
1. Extract EVERY transaction - do not skip any, even small amounts
2. All amounts must be POSITIVE numbers (use transaction_type for direction)
3. Dates must be YYYY-MM-DD format (infer year from statement period if needed)
4. Do not clean payment descriptions but preserve identifying information
5. Set parsing_confidence 0.0-1.0 based on text clarity
6. Add any issues or uncertainties to parsing_notes

Return ONLY valid JSON with this exact structure:
{{
    "account_info": {{
        "account_holder": "name or null",
        "account_number_last4": "last 4 digits or null",
        "account_number_masked": "masked number like XXXX1234 or null",
        "account_type": "{account_type.value}",
        "bank_name": "{get_bank_display_name(bank_type)}",
        "bank_type": "{bank_type.value}",
        "statement_start_date": "YYYY-MM-DD or null",
        "statement_end_date": "YYYY-MM-DD or null"
    }},
    "summary": {{
        "beginning_balance": number_or_null,
        "ending_balance": number_or_null,
        "total_deposits": number_or_null,
        "total_withdrawals": number_or_null,
        "previous_balance": number_or_null,
        "new_balance": number_or_null,
        "payments_credits": number_or_null,
        "purchases": number_or_null,
        "fees_charged": number_or_null,
        "interest_charged": number_or_null,
        "credit_limit": number_or_null,
        "available_credit": number_or_null,
        "minimum_payment": number_or_null,
        "payment_due_date": "YYYY-MM-DD or null",
        "rewards_balance": number_or_null
    }},
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "description": "cleaned merchant/description",
            "original_description": "raw text from statement",
            "amount": positive_number,
            "transaction_type": "credit" or "debit",
            "category": "category or null",
            "balance_after": number_or_null,
            "location": "city, state or null",
            "is_recurring": true_or_false,
            "check_number": "if check payment or null",
            "reference_number": "if shown or null"
        }}
    ],
    "parsing_confidence": 0.0_to_1.0,
    "parsing_notes": ["list any issues found"]
}}"""


# ============== Main Parser Class ==============

class StatementParser:
    """
    Universal bank statement parser using Gemini + Pydantic.
    
    SECURITY: All PII is sanitized before sending to LLM.
    
    Supports:
    - Chase (Credit & Checking)
    - Bank of America
    - Wells Fargo
    - Capital One
    - Discover
    - American Express
    - Citi
    - And most other US banks
    
    Example:
        parser = StatementParser("your_gemini_api_key")
        result = parser.parse("statement.pdf")
        result.save_json("output.json")
    """
    
    def __init__(self, gemini_api_key: str, output_dir: str = "data/parsed_statements"):
        """
        Initialize parser with Gemini API key.
        
        Args:
            gemini_api_key: Your Google Gemini API key
            output_dir: Directory to save parsed JSON files
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            self._genai = genai
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize PII sanitizer
            self.pii_sanitizer = PIISanitizer()
            
            logger.info("StatementParser initialized successfully (PII sanitization enabled)")
        except ImportError:
            raise ImportError(
                "google-generativeai package required.\n"
                "Install with: pip install google-generativeai"
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini: {str(e)}")
    
    def parse(
        self, 
        pdf_source: Union[str, bytes, Path],
        filename: str = None,
        save_json: bool = True,
        sanitize_pii: bool = True,
        previous_errors: Optional[List[str]] = None
    ) -> ParsedStatement:
        """
        Parse a bank statement PDF.
        
        Args:
            pdf_source: File path, Path object, or PDF bytes
            filename: Original filename (auto-detected if pdf_source is path)
            save_json: Whether to save parsed output to JSON file
            sanitize_pii: Whether to sanitize PII before sending to LLM (default: True)
            
        Returns:
            ParsedStatement with all extracted data
        """
        # Determine filename
        if filename is None:
            if isinstance(pdf_source, (str, Path)):
                filename = Path(pdf_source).name
            else:
                filename = f"statement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        logger.info(f"Parsing: {filename}")
        
        # Step 1: Extract text from PDF
        text, page_count = extract_text_from_pdf(pdf_source)
        logger.info(f"Extracted {len(text)} chars from {page_count} pages")
        
        # Step 2: Sanitize PII before sending to LLM
        pii_report = None
        original_text = text  # Keep original for local processing
        
        if sanitize_pii:
            sanitization_result = self.pii_sanitizer.sanitize(text)
            text = sanitization_result.sanitized_text
            
            if sanitization_result.pii_found:
                pii_report = self.pii_sanitizer.get_sanitization_report(sanitization_result)
                logger.info(f"PII sanitized: {list(sanitization_result.pii_found.keys())}")
        
        # Step 3: Detect bank and account type
        bank_type, account_type = detect_bank_type(original_text)  # Use original for detection
        logger.info(f"Detected: {bank_type.value} / {account_type.value}")
        
        # Step 4: Build prompt and call Gemini (with sanitized text)
        prompt = build_parsing_prompt(text, bank_type, account_type, previous_errors=previous_errors)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self._genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            logger.info("Gemini response received")
            
            # Step 5: Parse and validate response
            result = self._parse_response(
                response.text, 
                bank_type, 
                account_type, 
                filename,
                len(original_text),
                page_count
            )
            
            # Add PII sanitization note
            if pii_report:
                result.parsing_notes.append("PII was sanitized before LLM processing")
            
            logger.info(f"Parsed {len(result.transactions)} transactions (confidence: {result.parsing_confidence:.0%})")
            
            # Step 6: Save JSON if requested
            if save_json:
                json_path = self._save_parsed_output(result, filename)
                logger.info(f"Saved to: {json_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Parsing error: {str(e)}")
            raise ValueError(f"Failed to parse statement: {str(e)}")
    
    def parse_bytes(self, pdf_bytes: bytes, filename: str = "statement.pdf", save_json: bool = True, sanitize_pii: bool = True) -> ParsedStatement:
        """Parse PDF from bytes (for Streamlit uploads)."""
        return self.parse(pdf_bytes, filename=filename, save_json=save_json, sanitize_pii=sanitize_pii)
    
    def parse_file(self, file_path: Union[str, Path], save_json: bool = True, sanitize_pii: bool = True) -> ParsedStatement:
        """Parse PDF from file path."""
        return self.parse(file_path, save_json=save_json, sanitize_pii=sanitize_pii)
    
    def parse_with_retry(
        self, 
        pdf_source: Union[str, bytes, Path],
        filename: str = None,
        max_retries: int = 2,
        save_json: bool = True,
        sanitize_pii: bool = True
    ) -> ParsedStatement:
        """Parse with automatic retry on failure or low confidence."""
        
        last_error = None
        best_result = None
        previous_errors = []  # Track errors from previous attempts
        
        for attempt in range(max_retries + 1):
            try:
                result = self.parse(
                    pdf_source, 
                    filename, 
                    save_json=False, 
                    sanitize_pii=sanitize_pii,
                    previous_errors=previous_errors if attempt > 0 else None
                )
                
                # Keep best result
                if best_result is None or result.parsing_confidence > best_result.parsing_confidence:
                    best_result = result
                
                if result.parsing_confidence >= 0.7:
                    if save_json:
                        self._save_parsed_output(result, filename or "statement.pdf")
                    return result
                
                if attempt < max_retries:
                    logger.warning(f"Low confidence ({result.parsing_confidence:.0%}), retrying in 60 seconds...")
                    time.sleep(60)  # Wait 1 minute before retry
                    
            except Exception as e:
                last_error = e
                
                # Extract validation error details for LLM feedback
                error_message = str(e)
                if "validation error" in error_message.lower() or "value error" in error_message.lower():
                    # Extract useful error information
                    error_summary = self._extract_validation_errors(error_message)
                    if error_summary:
                        previous_errors.append(error_summary)
                        logger.info(f"Extracted validation error for retry: {error_summary}")
                
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {error_message}")
                    logger.info("Waiting 60 seconds before retry...")
                    time.sleep(60)  # Wait 1 minute before retry
        
        # Return best result or raise error
        if best_result:
            if save_json:
                self._save_parsed_output(best_result, filename or "statement.pdf")
            return best_result
        
        raise last_error or ValueError("Parsing failed")
    
    def _extract_validation_errors(self, error_message: str) -> Optional[str]:
        """Extract meaningful validation error information for LLM feedback.
        
        Args:
            error_message: The full error message from Pydantic validation
            
        Returns:
            A concise error summary string, or None if not a validation error
        """
        # Look for common validation error patterns
        if "validation error" not in error_message.lower() and "value error" not in error_message.lower():
            return None
        
        # Extract field names and error details
        errors = []
        
        # Pattern for field errors like "transactions.3.date"
        field_pattern = r'(\w+(?:\.\w+)*)\.(\w+)'
        # Pattern for error messages like "Cannot parse date: 2025-04-00"
        value_pattern = r'Cannot parse (\w+):\s*([^\s\[\]]+)'
        
        # Find all field errors
        for line in error_message.split('\n'):
            line = line.strip()
            if not line or line.startswith('For further information'):
                continue
            
            # Match field patterns
            field_match = re.search(field_pattern, line)
            value_match = re.search(value_pattern, line)
            
            if field_match and value_match:
                field_path = field_match.group(1)  # e.g., "transactions.3"
                field_name = field_match.group(2)  # e.g., "date"
                error_type = value_match.group(1)  # e.g., "date"
                invalid_value = value_match.group(2)  # e.g., "2025-04-00"
                
                # Create a helpful error message
                if error_type == "date":
                    errors.append(
                        f"Invalid date format in {field_path}.{field_name}: '{invalid_value}'. "
                        f"Dates must be valid YYYY-MM-DD format (e.g., 2025-04-15). "
                        f"Never use '00' or 'XX' as placeholders. If date is unclear, use null."
                    )
                else:
                    errors.append(
                        f"Invalid {error_type} in {field_path}.{field_name}: '{invalid_value}'"
                    )
            elif field_match:
                # Just field info without value
                field_path = field_match.group(1)
                field_name = field_match.group(2)
                errors.append(f"Validation error in {field_path}.{field_name}")
        
        if errors:
            return "; ".join(errors)
        
        # Fallback: return a simplified version of the error
        if "date" in error_message.lower():
            return "Date validation error: Ensure all dates are valid YYYY-MM-DD format, never use '00' or 'XX' as placeholders"
        
        return "Validation error occurred - please check all field formats"
    
    def _parse_response(
        self, 
        response_text: str,
        bank_type: BankType,
        account_type: AccountType,
        filename: str,
        text_length: int,
        page_count: int
    ) -> ParsedStatement:
        """Parse and validate Gemini response."""
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
            else:
                raise ValueError("Invalid JSON response")
        
        # Ensure required fields
        data.setdefault('account_info', {})
        data.setdefault('summary', {})
        data.setdefault('transactions', [])
        data.setdefault('parsing_notes', [])
        data.setdefault('parsing_confidence', 0.8)
        
        # Override detected values
        data['account_info']['bank_type'] = bank_type.value
        data['account_info']['account_type'] = account_type.value
        if not data['account_info'].get('bank_name'):
            data['account_info']['bank_name'] = get_bank_display_name(bank_type)
        
        # Add metadata
        data['source_filename'] = filename
        data['parsed_at'] = datetime.now().isoformat()
        data['raw_text_length'] = text_length
        data['page_count'] = page_count
        
        # Generate transaction IDs
        for txn in data['transactions']:
            if not txn.get('transaction_id'):
                content = f"{txn.get('date')}_{txn.get('description', '')[:30]}_{txn.get('amount')}"
                txn['transaction_id'] = f"pdf_{hashlib.md5(content.encode()).hexdigest()[:12]}"
            if not txn.get('original_description'):
                txn['original_description'] = txn.get('description', '')
        
        return ParsedStatement.model_validate(data)
    
    def _save_parsed_output(self, result: ParsedStatement, filename: str) -> str:
        """Save parsed statement to JSON file."""
        # Create safe filename
        safe_name = re.sub(r'[^\w\-.]', '_', filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"{Path(safe_name).stem}_{timestamp}.json"
        
        output_path = self.output_dir / json_filename
        result.save_json(output_path)
        
        return str(output_path)


# ============== CLI / Testing Functions ==============

def test_parser(pdf_path: str, api_key: str = None):
    """
    Test the parser with a PDF file.
    
    Usage:
        python -m src.services.statement_parser test path/to/statement.pdf
    """
    import os
    
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY environment variable or pass api_key")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing Statement Parser")
    print(f"{'='*60}")
    print(f"File: {pdf_path}")
    
    try:
        parser = StatementParser(api_key)
        result = parser.parse_file(pdf_path)
        
        print(f"\n✅ SUCCESS!")
        print(f"{'='*60}")
        print(f"Bank: {result.account_info.bank_name}")
        print(f"Account Type: {result.account_info.account_type.value}")
        print(f"Period: {result.account_info.statement_start_date} to {result.account_info.statement_end_date}")
        print(f"Transactions: {len(result.transactions)}")
        print(f"Confidence: {result.parsing_confidence:.0%}")
        
        if result.transactions:
            print(f"\n📋 First 5 Transactions:")
            print("-" * 60)
            for txn in result.transactions[:5]:
                sign = "+" if txn.transaction_type == TransactionType.CREDIT else "-"
                print(f"  {txn.date} | {sign}${txn.amount:>8.2f} | {txn.description[:35]}")
        
        if result.parsing_notes:
            print(f"\n⚠️ Notes:")
            for note in result.parsing_notes:
                print(f"  - {note}")
        
        print(f"\n📁 JSON saved to: data/parsed_statements/")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("""
Usage:
    python -m src.services.statement_parser <pdf_path>
    python -m src.services.statement_parser test <pdf_path>
    
Example:
    python -m src.services.statement_parser resources/chase_statement.pdf
    
Environment:
    GEMINI_API_KEY - Your Google Gemini API key
        """)
        return
    
    command = sys.argv[1]
    
    if command == "test" and len(sys.argv) > 2:
        test_parser(sys.argv[2])
    elif Path(command).exists():
        test_parser(command)
    else:
        print(f"File not found: {command}")


if __name__ == "__main__":
    main()