# backend/guardrails/output_validators.py

from guardrails import Guard, Validator, register_validator
from guardrails.hub import DetectPII
from guardrails.validator_base import (
    ValidationResult,
    PassResult,
    FailResult,
)
from db.database import SessionLocal
from db.models import Product
import re
import logging

logger = logging.getLogger(__name__)


# ── Custom Validator: Price Hallucination Guard ────────────────────────────
@register_validator(
    name      = "price-hallucination-guard",
    data_type = "string"
)
class PriceHallucinationGuard(Validator):
    """
    Checks if any price mentioned in the response
    actually exists in the product catalog DB.

    Prevents agent from making up prices like:
    "iPhone 15 is available for ₹45,000"
    when DB says ₹79,999.
    """

    def validate(
        self, value: str, metadata: dict
    ) -> ValidationResult:

        # Skip checkout summaries and payment confirmations
        skip_phrases = [
            "Cart total", "Order Summary", "order_",
            "Payment successful", "🛒", "Total:", "Remaining:",
            "Here's what you can buy",
            "Here's what you can get",      # ← add
            "products from our catalog",
            "Added to cart", "Removed from cart",
            "what you can buy", "you can buy with",
            "spend summary", "Your cart",
            "you can get",                   # ← add
            "under ₹",                       # ← add
        ]

        if any(phrase in value for phrase in skip_phrases):
            return PassResult()
    
        # Find all prices mentioned in response (₹ followed by numbers)
        price_pattern = r'₹([\d,]+(?:\.\d{1,2})?)'
        mentioned_prices = re.findall(price_pattern, value)

        if not mentioned_prices:
            return PassResult()  # no prices mentioned — safe

        db = SessionLocal()
        try:
            # Get all valid prices from DB
            all_products   = db.query(Product).all()
            valid_prices   = {p.price for p in all_products}

            for price_str in mentioned_prices:
                # Clean price string (remove commas)
                price = float(price_str.replace(",", ""))

                # Allow small rounding differences (±1 rupee)
                is_valid = any(
                    abs(price - valid) < 1.0
                    for valid in valid_prices
                )

                if not is_valid:
                    logger.warning(
                        f"🚨 Hallucinated price detected: ₹{price}"
                    )
                    return FailResult(
                        error_message = (
                            f"Hallucinated price ₹{price:,.0f} "
                            f"not found in catalog"
                        ),
                        fix_value = None,
                    )

            return PassResult()

        except Exception as e:
            logger.error(f"❌ Price guard error: {e}")
            return PassResult()  # fail open for output
        finally:
            db.close()


# ── Output Guard Chain ─────────────────────────────────────────────────────
# NEW:
output_guard = (
    Guard()
    .use(DetectPII(
        pii_entities=["API_KEY", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD"],
        on_fail="fix"
    ))
    .use(PriceHallucinationGuard(on_fail="exception"))
)


# ── Master output validator ────────────────────────────────────────────────
def validate_output(response_text: str) -> dict:
    """
    Runs output through:
    1. PII detection + scrubbing (DetectPII)
    2. Price hallucination check (PriceHallucinationGuard)

    Returns:
        {
            "passed":   True,
            "response": cleaned_response_text
        }
        {
            "passed":   False,
            "reason":   "why it failed",
            "response": original_text
        }
    """
    try:
        result = output_guard.validate(response_text)

        # DetectPII with on_fail="fix" returns cleaned text
        cleaned = result.validated_output or response_text

        logger.info("✅ Output validation passed")
        return {
            "passed":   True,
            "response": cleaned,
        }

    except Exception as e:
        reason = str(e)
        logger.warning(f"🚫 Output blocked: {reason}")
        return {
            "passed":   False,
            "reason":   reason,
            "response": response_text,
        }