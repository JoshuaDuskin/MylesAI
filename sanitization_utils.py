import re
import json
from typing import Dict, Any

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitizes a dictionary to remove sensitive information.
    
    Redaction Rules:
    - Email addresses -> [REDACTED_EMAIL]
    - Phone numbers (US format) -> [REDACTED_PHONE]
    - SSN patterns (XXX-XX-XXXX) -> [REDACTED_SSN]
    - Credit Card patterns -> [REDACTED_CC]
    - API Keys / Secrets -> [REDACTED_SECRET]
    """
    
    def redact_value(value):
        if isinstance(value, str):
            # Email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            value = re.sub(email_pattern, '[REDACTED_EMAIL]', value)
            
            # US Phone (XXX) XXX-XXXX
            phone_pattern = r'\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}'
            value = re.sub(phone_pattern, '[REDACTED_PHONE]', value)
            
            # SSN
            ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
            value = re.sub(ssn_pattern, '[REDACTED_SSN]', value)
            
            # Credit Card (16 digits with optional separators)
            cc_pattern = r'\b(?:\d[ -]*){15}\d\b'
            value = re.sub(cc_pattern, '[REDACTED_CC]', value)
            
            # Generic Secrets/Keys
            secret_patterns = [
                r'(?:api[_-]?key|secret|password|token)\s*[=:]\s*"[^"]+"',
                r'(?i)(?:api[_-]?key|secret|password|token)\s*[=:]\s*\S+'
            ]
            for pattern in secret_patterns:
                value = re.sub(pattern, '[REDACTED_SECRET]', value)
            
            return value
        elif isinstance(value, dict):
            return {k: redact_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [redact_value(item) for item in value]
        else:
            return value
    
    return redact_value(data)