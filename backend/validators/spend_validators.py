# backend/guardrails/spend_validators.py

from db.database import SessionLocal
from db.models import Order
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


# ── Check 1: Amount validity ───────────────────────────────────────────────
def check_amount(amount: float) -> dict:
    """Zero, negative, or unreasonably large amounts."""

    if amount <= 0:
        return {
            "passed": False,
            "reason": f"Invalid amount ₹{amount}. Amount must be greater than 0."
        }

    if amount > 500000:
        return {
            "passed": False,
            "reason": f"Amount ₹{amount:,.0f} exceeds maximum single transaction limit."
        }

    return {"passed": True, "reason": None}


# ── Check 2: Spend limit ───────────────────────────────────────────────────
def check_spend_limit(
    amount:       float,
    spend_limit:  float,
    spent_so_far: float
) -> dict:
    """
    Checks if amount fits within remaining spend limit.
    spend_limit is read from DB session — cannot be reset by user.
    """
    remaining = spend_limit - spent_so_far

    if amount > remaining:
        return {
            "passed":    False,
            "reason":    (
                f"Cart total ₹{amount:,.0f} exceeds your "
                f"remaining limit of ₹{remaining:,.0f}. "
                f"(Limit: ₹{spend_limit:,.0f}, "
                f"Used: ₹{spent_so_far:,.0f})"
            ),
            "remaining": remaining,
        }

    return {
        "passed":    True,
        "reason":    None,
        "remaining": remaining,
    }


# ── Check 3: Duplicate order ───────────────────────────────────────────────
def check_duplicate_order(
    session_id: str,
    amount:     float
) -> dict:
    """
    Prevents double-charge if user taps Buy twice in 60 seconds.
    Checks for same session + same amount within last 60 seconds.
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)

        recent_order = db.query(Order).filter(
            Order.session_id  == session_id,
            Order.amount      == amount,
            Order.created_at  >= cutoff,
            Order.status      != "failed",
        ).first()

        if recent_order:
            logger.warning(
                f"⚠️ Duplicate order detected: "
                f"session {session_id[:8]}... "
                f"₹{amount:,.0f}"
            )
            return {
                "passed":  False,
                "reason":  (
                    "Duplicate order detected. "
                    "You already placed this order less than 60 seconds ago."
                ),
                "existing_order_id": recent_order.razorpay_order_id,
            }

        return {"passed": True, "reason": None}

    except Exception as e:
        logger.error(f"❌ Duplicate check error: {e}")
        return {"passed": True, "reason": None}  # fail open
    finally:
        db.close()


# ── Check 4: Cart not empty ────────────────────────────────────────────────
def check_cart_not_empty(cart: list) -> dict:
    """Cart must have at least one item before checkout."""

    if not cart or len(cart) == 0:
        return {
            "passed": False,
            "reason": "Your cart is empty. Add items before checking out."
        }

    return {"passed": True, "reason": None}


# ── Master spend validator ─────────────────────────────────────────────────
def validate_spend(
    amount:       float,
    spend_limit:  float,
    spent_so_far: float,
    session_id:   str,
    cart:         list,
) -> dict:
    """
    Runs all 4 spend checks in order. Stops at first failure.

    Order:
    1. Cart not empty (free)
    2. Amount validity (free)
    3. Spend limit check (free — reads from state)
    4. Duplicate order check (SQLite query)

    Returns:
        {"passed": True, "reason": None}
        {"passed": False, "reason": "human readable reason"}
    """

    # Check 1 — cart not empty
    cart_check = check_cart_not_empty(cart)
    if not cart_check["passed"]:
        return cart_check

    # Check 2 — amount validity
    amount_check = check_amount(amount)
    if not amount_check["passed"]:
        return amount_check

    # Check 3 — spend limit
    limit_check = check_spend_limit(amount, spend_limit, spent_so_far)
    if not limit_check["passed"]:
        return limit_check

    # Check 4 — duplicate order
    duplicate_check = check_duplicate_order(session_id, amount)
    if not duplicate_check["passed"]:
        return duplicate_check

    return {"passed": True, "reason": None}