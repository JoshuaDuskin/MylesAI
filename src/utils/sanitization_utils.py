import re
import html

def sanitize_html(text: str) -> str:
    """Remove potentially malicious HTML tags and attributes."""
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = html.unescape(text)
    return text.strip()

def sanitize_status_feed(data: dict) -> dict:
    """Sanitize keys and values in the status feed dictionary."""
    sanitized = {}
    for key, value in data.items():
        safe_key = sanitize_html(str(key))
        safe_value = sanitize_html(str(value))
        sanitized[safe_key] = safe_value
    return sanitized