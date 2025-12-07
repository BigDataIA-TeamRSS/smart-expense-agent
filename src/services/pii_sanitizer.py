"""
PII Sanitizer for Bank Statements
Removes/masks sensitive information before sending to LLM.

Handles:
- Full names
- Addresses
- Account numbers
- SSN/Tax IDs
- Phone numbers
- Email addresses
- Date of birth
- Driver's license numbers
- Routing numbers
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class SanitizationResult:
    """Result of sanitization with mapping for restoration."""
    sanitized_text: str
    pii_found: Dict[str, List[str]] = field(default_factory=dict)
    replacement_map: Dict[str, str] = field(default_factory=dict)
    
    def get_original(self, placeholder: str) -> str:
        """Get original value for a placeholder."""
        return self.replacement_map.get(placeholder, placeholder)


class PIISanitizer:
    """
    Sanitizes PII from bank statement text before sending to LLM.
    Preserves transaction data while removing personal information.
    """
    
    def __init__(self):
        # Counters for generating unique placeholders
        self._counters = {}
        
        # Common name prefixes/suffixes to help identify names
        self.name_prefixes = {'mr', 'mrs', 'ms', 'miss', 'dr', 'prof'}
        self.name_suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'md', 'phd', 'esq'}
        
        # US State abbreviations for address detection
        self.us_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
        }
    
    def _get_placeholder(self, pii_type: str) -> str:
        """Generate unique placeholder for PII type."""
        if pii_type not in self._counters:
            self._counters[pii_type] = 0
        self._counters[pii_type] += 1
        return f"[{pii_type}_{self._counters[pii_type]}]"
    
    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize all PII from text.
        
        Args:
            text: Raw bank statement text
            
        Returns:
            SanitizationResult with sanitized text and mappings
        """
        # Reset counters for each sanitization
        self._counters = {}
        
        result = SanitizationResult(
            sanitized_text=text,
            pii_found={},
            replacement_map={}
        )
        
        # Order matters - do more specific patterns first
        sanitizers = [
            ('SSN', self._sanitize_ssn),
            ('ACCOUNT_NUM', self._sanitize_account_numbers),
            ('ROUTING_NUM', self._sanitize_routing_numbers),
            ('EMAIL', self._sanitize_emails),
            ('PHONE', self._sanitize_phone_numbers),
            ('DOB', self._sanitize_dob),
            ('DRIVERS_LICENSE', self._sanitize_drivers_license),
            ('ADDRESS', self._sanitize_addresses),
            ('NAME', self._sanitize_names),
            ('ZIPCODE', self._sanitize_zipcodes),
        ]
        
        for pii_type, sanitizer_func in sanitizers:
            result = sanitizer_func(result, pii_type)
        
        return result
    
    def _sanitize_ssn(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove Social Security Numbers."""
        # Full SSN: 123-45-6789 or 123456789
        patterns = [
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # 123-45-6789 or 123 45 6789
            r'\bSSN[:\s]*\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # SSN: 123-45-6789
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                # Verify it looks like SSN (not a date or other number)
                digits = re.sub(r'\D', '', match)
                if len(digits) == 9 and not digits.startswith('0'):
                    placeholder = self._get_placeholder(pii_type)
                    result.sanitized_text = result.sanitized_text.replace(match, placeholder, 1)
                    result.replacement_map[placeholder] = match
                    if pii_type not in result.pii_found:
                        result.pii_found[pii_type] = []
                    result.pii_found[pii_type].append(f"***-**-{digits[-4:]}")
        
        return result
    
    def _sanitize_account_numbers(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove/mask account numbers (keep last 4 for reference)."""
        patterns = [
            # Account Number: 1234567890
            (r'(?:account\s*(?:number|#|no\.?)?[:\s]*?)(\d{8,17})', True),
            # XXXX XXXX XXXX 1234 (credit card format shown in statements)
            (r'(X{4}\s*X{4}\s*X{4}\s*\d{4})', False),  # Already masked, keep as is
            # Full credit card numbers (16 digits)
            (r'\b(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\b', True),
            # Account numbers 8-17 digits after "Account" keyword
            (r'(?:acct|account)[:\s#]*(\d{8,17})', True),
        ]
        
        for pattern, should_mask in patterns:
            matches = re.finditer(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                number = match.group(1) if match.lastindex else match.group(0)
                digits = re.sub(r'\D', '', number)
                
                if should_mask and len(digits) >= 8:
                    # Keep last 4 digits
                    masked = f"XXXX-XXXX-{digits[-4:]}"
                    placeholder = masked  # Use masked version directly
                    
                    # Replace just the number part, keep the label
                    if match.lastindex:
                        new_text = full_match.replace(number, masked)
                        result.sanitized_text = result.sanitized_text.replace(full_match, new_text, 1)
                    else:
                        result.sanitized_text = result.sanitized_text.replace(full_match, masked, 1)
                    
                    if pii_type not in result.pii_found:
                        result.pii_found[pii_type] = []
                    result.pii_found[pii_type].append(masked)
        
        return result
    
    def _sanitize_routing_numbers(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove routing numbers."""
        patterns = [
            r'(?:routing\s*(?:number|#|no\.?)?[:\s]*?)(\d{9})\b',
            r'(?:ABA|RTN)[:\s]*(\d{9})\b',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                number = match.group(1)
                masked = f"XXXXX{number[-4:]}"
                new_text = full_match.replace(number, masked)
                result.sanitized_text = result.sanitized_text.replace(full_match, new_text, 1)
                
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append(masked)
        
        return result
    
    def _sanitize_emails(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove email addresses."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        matches = re.findall(pattern, result.sanitized_text)
        for email in matches:
            placeholder = self._get_placeholder(pii_type)
            result.sanitized_text = result.sanitized_text.replace(email, placeholder, 1)
            result.replacement_map[placeholder] = email
            if pii_type not in result.pii_found:
                result.pii_found[pii_type] = []
            # Show domain only
            domain = email.split('@')[1] if '@' in email else 'hidden'
            result.pii_found[pii_type].append(f"***@{domain}")
        
        return result
    
    def _sanitize_phone_numbers(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove phone numbers."""
        patterns = [
            r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # (123) 456-7890
            r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',  # 123-456-7890
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # +1 123-456-7890
        ]
        
        # Don't remove customer service numbers (keep 1-800, 1-888, etc.)
        customer_service_pattern = r'1[-.]?8[0-9]{2}[-.]?\d{3}[-.]?\d{4}'
        
        for pattern in patterns:
            matches = re.findall(pattern, result.sanitized_text)
            for phone in matches:
                # Skip customer service numbers
                if re.match(customer_service_pattern, phone.replace(' ', '').replace('(', '').replace(')', '')):
                    continue
                
                placeholder = self._get_placeholder(pii_type)
                result.sanitized_text = result.sanitized_text.replace(phone, placeholder, 1)
                result.replacement_map[placeholder] = phone
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append("(XXX) XXX-XXXX")
        
        return result
    
    def _sanitize_dob(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove dates of birth."""
        patterns = [
            r'(?:DOB|date\s*of\s*birth|birth\s*date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:DOB|date\s*of\s*birth|birth\s*date)[:\s]*(\w+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                date_part = match.group(1)
                placeholder = self._get_placeholder(pii_type)
                result.sanitized_text = result.sanitized_text.replace(full_match, 
                    full_match.replace(date_part, placeholder), 1)
                result.replacement_map[placeholder] = date_part
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append("[REDACTED]")
        
        return result
    
    def _sanitize_drivers_license(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove driver's license numbers."""
        patterns = [
            r"(?:driver'?s?\s*license|DL|license\s*#?)[:\s]*([A-Z]?\d{6,12})",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                dl_num = match.group(1)
                placeholder = self._get_placeholder(pii_type)
                result.sanitized_text = result.sanitized_text.replace(full_match,
                    full_match.replace(dl_num, placeholder), 1)
                result.replacement_map[placeholder] = dl_num
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append("[REDACTED]")
        
        return result
    
    def _sanitize_addresses(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove street addresses."""
        # Pattern for street addresses
        # 123 Main St, City, ST 12345
        address_pattern = r'\b(\d{1,6}\s+[\w\s]{2,30}(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|circle|cir|boulevard|blvd|place|pl|terrace|ter|highway|hwy)\.?(?:\s*(?:apt|suite|unit|#)\s*[\w\d-]+)?)\b'
        
        matches = re.finditer(address_pattern, result.sanitized_text, re.IGNORECASE)
        found_addresses = []
        
        for match in matches:
            address = match.group(1)
            # Skip if it looks like a merchant address in transaction
            if len(address) < 10:  # Too short to be a real address
                continue
            found_addresses.append((match.start(), match.end(), address))
        
        # Replace from end to start to preserve positions
        for start, end, address in reversed(found_addresses):
            placeholder = self._get_placeholder(pii_type)
            result.sanitized_text = result.sanitized_text[:start] + placeholder + result.sanitized_text[end:]
            result.replacement_map[placeholder] = address
            if pii_type not in result.pii_found:
                result.pii_found[pii_type] = []
            result.pii_found[pii_type].append("[ADDRESS REDACTED]")
        
        # Also look for city, state ZIP patterns that might be part of addresses
        city_state_zip = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,?\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b'
        
        # Find potential mailing addresses (usually at top of statement)
        # Look for patterns that appear before "Statement" or similar
        header_match = re.search(r'^(.{0,500}?)(?:statement|account\s*summary|account\s*activity)', 
                                  result.sanitized_text, re.IGNORECASE | re.DOTALL)
        if header_match:
            header_text = header_match.group(1)
            city_matches = re.finditer(city_state_zip, header_text)
            for match in city_matches:
                full = match.group(0)
                if match.group(2) in self.us_states:
                    placeholder = self._get_placeholder(pii_type)
                    result.sanitized_text = result.sanitized_text.replace(full, placeholder, 1)
                    result.replacement_map[placeholder] = full
        
        return result
    
    def _sanitize_names(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Remove account holder names from header area."""
        # Look for name patterns in the first part of the document (header/address area)
        # This is tricky because we don't want to remove merchant names in transactions
        
        # Pattern 1: Name after specific labels
        name_label_patterns = [
            r'(?:account\s*holder|customer|name|attention|attn)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)',
            r'(?:dear|hello)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        ]
        
        for pattern in name_label_patterns:
            matches = re.finditer(pattern, result.sanitized_text, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                name = match.group(1)
                placeholder = self._get_placeholder(pii_type)
                result.sanitized_text = result.sanitized_text.replace(full_match,
                    full_match.replace(name, placeholder), 1)
                result.replacement_map[placeholder] = name
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append("[NAME REDACTED]")
        
        # Pattern 2: Names that appear alone on a line in header (mailing address format)
        # Only check first 500 chars (header area)
        header = result.sanitized_text[:500]
        
        # Look for ALL CAPS name (common in mailing addresses)
        caps_name_pattern = r'^([A-Z]{2,}\s+(?:[A-Z]\.?\s+)?[A-Z]{2,})$'
        lines = header.split('\n')
        for line in lines:
            line = line.strip()
            if re.match(caps_name_pattern, line) and len(line) < 40:
                # Likely a name
                placeholder = self._get_placeholder(pii_type)
                result.sanitized_text = result.sanitized_text.replace(line, placeholder, 1)
                result.replacement_map[placeholder] = line
                if pii_type not in result.pii_found:
                    result.pii_found[pii_type] = []
                result.pii_found[pii_type].append("[NAME REDACTED]")
        
        return result
    
    def _sanitize_zipcodes(self, result: SanitizationResult, pii_type: str) -> SanitizationResult:
        """Partially mask ZIP codes in header area (keep first 3 for region)."""
        # Only in header area, not in merchant locations
        header = result.sanitized_text[:800]
        
        # ZIP+4 pattern
        zip_pattern = r'\b(\d{5})-(\d{4})\b'
        
        for match in re.finditer(zip_pattern, header):
            full_zip = match.group(0)
            zip5 = match.group(1)
            # Keep first 3 digits (region), mask rest
            masked = f"{zip5[:3]}XX-XXXX"
            result.sanitized_text = result.sanitized_text.replace(full_zip, masked, 1)
            if pii_type not in result.pii_found:
                result.pii_found[pii_type] = []
            result.pii_found[pii_type].append(masked)
        
        return result
    
    def get_sanitization_report(self, result: SanitizationResult) -> str:
        """Generate a human-readable report of what was sanitized."""
        if not result.pii_found:
            return "No PII detected."
        
        lines = ["PII Sanitization Report:", "-" * 40]
        
        for pii_type, items in result.pii_found.items():
            lines.append(f"\n{pii_type}: {len(items)} found")
            for item in items[:5]:  # Show max 5 examples
                lines.append(f"  - {item}")
            if len(items) > 5:
                lines.append(f"  ... and {len(items) - 5} more")
        
        return "\n".join(lines)


# Convenience function
def sanitize_statement_text(text: str) -> Tuple[str, Dict[str, List[str]]]:
    """
    Quick function to sanitize text.
    
    Returns:
        Tuple of (sanitized_text, pii_found_dict)
    """
    sanitizer = PIISanitizer()
    result = sanitizer.sanitize(text)
    return result.sanitized_text, result.pii_found


# Test function
def test_sanitizer():
    """Test the sanitizer with sample text."""
    sample = """
    JOHN SMITH
    123 MAIN STREET APT 4B
    BOSTON MA 02120-1234
    
    Account Number: 4532789012345678
    SSN: 123-45-6789
    Email: john.smith@email.com
    Phone: (617) 555-1234
    
    Customer Service: 1-800-524-3880
    
    TRANSACTION DETAIL
    10/15 AMAZON MKTPLACE SEATTLE WA    $25.99
    10/16 STARBUCKS BOSTON MA           $5.50
    """
    
    sanitizer = PIISanitizer()
    result = sanitizer.sanitize(sample)
    
    print("Original Text:")
    print(sample)
    print("\n" + "="*50)
    print("\nSanitized Text:")
    print(result.sanitized_text)
    print("\n" + "="*50)
    print(sanitizer.get_sanitization_report(result))


if __name__ == "__main__":
    test_sanitizer()