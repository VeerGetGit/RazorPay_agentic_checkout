# backend/validators/input_validators.py

import os
import logging
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(_env_path, override=True)

logger = logging.getLogger(__name__)

INJECTION_KEYWORDS = [
    "ignore previous",
    "ignore your instructions",
    "ignore all instructions",
    "forget your instructions",
    "forget all previous",          # ← add
    "forget previous instructions", # ← add
    "disregard your",
    "you are now",
    "you are a different",          # ← add
    "pretend you are",
    "act as if",
    "override",
    "jailbreak",
    "ignore spend limit",
    "bypass",
    "do not follow",
    "ignore the rules",
    "remove all restrictions",      # ← add
    "set spend limit to",           # ← add
    "no restrictions",              # ← add
]

TOXIC_KEYWORDS = [
    "idiot", "stupid", "hate", "kill", "die",
    "abuse", "scam", "fraud", "cheat"
]

def _is_injection(text: str) -> bool:
    return any(kw in text.lower() for kw in INJECTION_KEYWORDS)

def _is_toxic(text: str) -> bool:
    return any(kw in text.lower() for kw in TOXIC_KEYWORDS)

def check_malformed(text: str) -> dict:
    if not text or not text.strip():
        return {"passed": False, "reason": "Empty message"}
    if len(text.strip()) < 2:
        return {"passed": False, "reason": "Message too short"}
    if len(text) > 2000:
        return {"passed": False, "reason": "Message too long"}
    return {"passed": True, "reason": None}

def validate_input(text: str) -> dict:
    malformed = check_malformed(text)
    if not malformed["passed"]:
        logger.info(f"🚫 Malformed: {malformed['reason']}")
        return malformed

    if _is_toxic(text):
        logger.warning(f"🚫 Toxic blocked: {text[:50]}")
        return {"passed": False, "reason": "Abusive language detected"}

    if _is_injection(text):
        logger.warning(f"🚨 Injection blocked: {text[:50]}")
        return {"passed": False, "reason": "Prompt injection detected"}

    logger.info("✅ Input validation passed")
    return {"passed": True, "reason": None}