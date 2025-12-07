"""
Transaction Deduplication Service

Handles deduplication of transactions from multiple sources:
- Same statement uploaded multiple times
- Transactions already from Plaid API
- Same transaction appearing multiple times

Uses fuzzy matching on multiple fields to identify duplicates.
"""

import hashlib
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Set
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class TransactionDeduplicator:
    """Service for detecting and filtering duplicate transactions."""
    
    # Tolerance for amount matching (in dollars)
    AMOUNT_TOLERANCE = 0.01
    
    # Date tolerance (in days) - transactions within this range are considered potential duplicates
    DATE_TOLERANCE_DAYS = 1
    
    def __init__(self):
        """Initialize the deduplicator."""
        pass
    
    def normalize_amount(self, amount: float) -> float:
        """Normalize amount for comparison."""
        if amount is None:
            return 0.0
        return abs(float(amount))
    
    def normalize_date(self, date_str: Optional[str]) -> Optional[date]:
        """Normalize date string to date object."""
        if not date_str:
            return None
        
        if isinstance(date_str, date):
            return date_str
        
        if isinstance(date_str, datetime):
            return date_str.date()
        
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d/%m/%Y']:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except ValueError:
                continue
        
        # Last resort
        try:
            from dateutil import parser as date_parser
            return date_parser.parse(str(date_str)).date()
        except:
            return None
    
    def normalize_description(self, desc: Optional[str]) -> str:
        """Normalize description for comparison."""
        if not desc:
            return ""
        
        # Convert to lowercase, remove extra whitespace
        normalized = " ".join(str(desc).lower().split())
        
        # Remove common prefixes/suffixes that vary
        # Remove reference numbers in format *XXXXX
        import re
        normalized = re.sub(r'\*[A-Z0-9]+', '', normalized)
        normalized = re.sub(r'#\d+', '', normalized)
        
        # Remove common merchant variations
        normalized = normalized.replace('amzn.com/bill', 'amazon')
        normalized = normalized.replace('amzn mkpt', 'amazon')
        normalized = normalized.replace('amzn.com', 'amazon')
        
        return normalized.strip()
    
    def generate_fingerprint(self, transaction: Dict) -> str:
        """
        Generate a unique fingerprint for a transaction.
        Uses date, amount, and normalized description.
        
        Note: If date cannot be parsed, uses original date string to avoid
        false matches between transactions with unparseable dates.
        """
        date_val = self.normalize_date(transaction.get("date"))
        amount = self.normalize_amount(transaction.get("amount"))
        desc = self.normalize_description(transaction.get("name") or transaction.get("description"))
        
        # Use reference number if available (more reliable)
        ref_num = transaction.get("reference_number") or transaction.get("transaction_code")
        
        # Handle None dates: use original date string to avoid false matches
        # If date is None, include original date string in fingerprint
        if date_val is None:
            original_date = str(transaction.get("date", ""))
            date_str = f"UNPARSEABLE_{original_date}"
        else:
            date_str = str(date_val)
        
        if ref_num:
            # If we have a reference number, use it for fingerprinting
            fingerprint_str = f"{date_str}|{amount}|{ref_num}"
        else:
            # Otherwise use normalized description
            fingerprint_str = f"{date_str}|{amount}|{desc}"
        
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def are_transactions_similar(
        self, 
        txn1: Dict, 
        txn2: Dict,
        check_reference: bool = True
    ) -> Tuple[bool, str]:
        """
        Check if two transactions are similar (likely duplicates).
        
        Returns:
            (is_duplicate, reason)
        """
        # Check 1: Same transaction_id
        txn1_id = txn1.get("transaction_id")
        txn2_id = txn2.get("transaction_id")
        
        if txn1_id and txn2_id and txn1_id == txn2_id:
            return True, "same_transaction_id"
        
        # Check 2: Same reference number (if available)
        if check_reference:
            ref1 = txn1.get("reference_number") or txn1.get("transaction_code")
            ref2 = txn2.get("reference_number") or txn2.get("transaction_code")
            
            if ref1 and ref2 and ref1 == ref2:
                # Same reference number - check if date and amount are close
                date1 = self.normalize_date(txn1.get("date"))
                date2 = self.normalize_date(txn2.get("date"))
                amount1 = self.normalize_amount(txn1.get("amount"))
                amount2 = self.normalize_amount(txn2.get("amount"))
                
                if date1 and date2:
                    date_diff = abs((date1 - date2).days)
                    amount_diff = abs(amount1 - amount2)
                    
                    if date_diff <= self.DATE_TOLERANCE_DAYS and amount_diff <= self.AMOUNT_TOLERANCE:
                        return True, "same_reference_number"
        
        # Check 3: Same fingerprint (only if both have valid dates)
        date1 = self.normalize_date(txn1.get("date"))
        date2 = self.normalize_date(txn2.get("date"))
        
        # Only use fingerprint matching if both dates are valid
        # This prevents false matches when dates are unparseable
        if date1 is not None and date2 is not None:
            fingerprint1 = self.generate_fingerprint(txn1)
            fingerprint2 = self.generate_fingerprint(txn2)
            
            if fingerprint1 == fingerprint2:
                return True, "same_fingerprint"
        
        # Check 4: Fuzzy match on date, amount, and description
        date1 = self.normalize_date(txn1.get("date"))
        date2 = self.normalize_date(txn2.get("date"))
        amount1 = self.normalize_amount(txn1.get("amount"))
        amount2 = self.normalize_amount(txn2.get("amount"))
        desc1 = self.normalize_description(txn1.get("name") or txn1.get("description"))
        desc2 = self.normalize_description(txn2.get("name") or txn2.get("description"))
        
        if date1 and date2 and desc1 and desc2:
            date_diff = abs((date1 - date2).days)
            amount_diff = abs(amount1 - amount2)
            
            # If date and amount match closely, and descriptions are similar
            if date_diff <= self.DATE_TOLERANCE_DAYS and amount_diff <= self.AMOUNT_TOLERANCE:
                # Check if descriptions are similar (at least 80% match)
                if self._description_similarity(desc1, desc2) >= 0.8:
                    return True, "fuzzy_match"
        
        return False, "different"
    
    def _description_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two descriptions (0.0 to 1.0)."""
        if not desc1 or not desc2:
            return 0.0
        
        if desc1 == desc2:
            return 1.0
        
        # Simple word overlap similarity
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def find_duplicates(
        self, 
        new_transactions: List[Dict], 
        existing_transactions: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Find duplicates between new and existing transactions.
        
        Args:
            new_transactions: List of new transactions to check
            existing_transactions: List of existing transactions to check against
        
        Returns:
            (unique_new_transactions, duplicate_transactions, matched_existing_transactions)
        """
        unique_new = []
        duplicates = []
        matched_existing = []
        
        # Build fingerprint index for faster lookup
        # Only include transactions with valid dates in fingerprint index
        existing_fingerprints: Dict[str, List[Dict]] = {}
        existing_ids: Set[str] = set()
        
        for existing in existing_transactions:
            # Only add to fingerprint index if date is valid
            existing_date = self.normalize_date(existing.get("date"))
            if existing_date is not None:
                fingerprint = self.generate_fingerprint(existing)
                if fingerprint not in existing_fingerprints:
                    existing_fingerprints[fingerprint] = []
                existing_fingerprints[fingerprint].append(existing)
            
            txn_id = existing.get("transaction_id")
            if txn_id:
                existing_ids.add(txn_id)
        
        # Check each new transaction
        for new_txn in new_transactions:
            is_duplicate = False
            match_reason = None
            matched_existing_txn = None
            
            # Quick check: transaction_id
            new_txn_id = new_txn.get("transaction_id")
            if new_txn_id and new_txn_id in existing_ids:
                is_duplicate = True
                match_reason = "same_transaction_id"
                # Find the matched transaction
                for existing in existing_transactions:
                    if existing.get("transaction_id") == new_txn_id:
                        matched_existing_txn = existing
                        break
            
            # Check fingerprint (only if new transaction has valid date)
            if not is_duplicate:
                new_date = self.normalize_date(new_txn.get("date"))
                # Only use fingerprint matching if date is valid
                if new_date is not None:
                    fingerprint = self.generate_fingerprint(new_txn)
                    if fingerprint in existing_fingerprints:
                        # Check each transaction with this fingerprint
                        for existing in existing_fingerprints[fingerprint]:
                            # Also verify existing transaction has valid date
                            existing_date = self.normalize_date(existing.get("date"))
                            if existing_date is not None:
                                similar, reason = self.are_transactions_similar(new_txn, existing)
                                if similar:
                                    is_duplicate = True
                                    match_reason = reason
                                    matched_existing_txn = existing
                                    break
            
            # If still not found, do a more thorough check
            if not is_duplicate:
                for existing in existing_transactions:
                    similar, reason = self.are_transactions_similar(new_txn, existing)
                    if similar:
                        is_duplicate = True
                        match_reason = reason
                        matched_existing_txn = existing
                        break
            
            if is_duplicate:
                duplicates.append(new_txn)
                if matched_existing_txn:
                    matched_existing.append(matched_existing_txn)
                logger.debug(
                    f"Duplicate transaction detected: {new_txn.get('transaction_id')} "
                    f"matches {matched_existing_txn.get('transaction_id') if matched_existing_txn else 'unknown'} "
                    f"(reason: {match_reason})"
                )
            else:
                unique_new.append(new_txn)
        
        return unique_new, duplicates, matched_existing
    
    def deduplicate_transactions(
        self,
        new_transactions: List[Dict],
        existing_transactions: List[Dict]
    ) -> Dict[str, any]:
        """
        Deduplicate transactions and return statistics.
        
        Args:
            new_transactions: List of new transactions to check
            existing_transactions: List of existing transactions to check against
        
        Returns:
            {
                "unique_new": List[Dict],
                "duplicates": List[Dict],
                "matched_existing": List[Dict],
                "stats": {
                    "total_new": int,
                    "unique_count": int,
                    "duplicate_count": int,
                    "deduplication_rate": float
                }
            }
        """
        unique_new, duplicates, matched_existing = self.find_duplicates(
            new_transactions, existing_transactions
        )
        
        total_new = len(new_transactions)
        unique_count = len(unique_new)
        duplicate_count = len(duplicates)
        deduplication_rate = (duplicate_count / total_new) if total_new > 0 else 0.0
        
        return {
            "unique_new": unique_new,
            "duplicates": duplicates,
            "matched_existing": matched_existing,
            "stats": {
                "total_new": total_new,
                "unique_count": unique_count,
                "duplicate_count": duplicate_count,
                "deduplication_rate": deduplication_rate
            }
        }


# Singleton instance
_deduplicator_instance: Optional[TransactionDeduplicator] = None


def get_deduplicator() -> TransactionDeduplicator:
    """Get singleton instance of TransactionDeduplicator."""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        _deduplicator_instance = TransactionDeduplicator()
    return _deduplicator_instance

