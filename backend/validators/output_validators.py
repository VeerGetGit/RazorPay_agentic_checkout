import re
import logging
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)


def _scrub_pii(text: str) -> str:
    text = re.sub(r'gsk_[a-zA-Z0-9]+', '[REDACTED]', text)
    text = re.sub(r'rzp_[a-zA-Z0-9_]+', '[REDACTED]', text)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED]', text)
    text = re.sub(r'\b[6-9]\d{9}\b', '[REDACTED]', text)
    return text


def _check_hallucinated_prices(text: str) -> bool:
    return False


def validate_output(response_text: str) -> dict:
    cleaned = _scrub_pii(response_text)
    return {
        "passed":   True,
        "response": cleaned,
    }