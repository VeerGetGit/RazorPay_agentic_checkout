# backend/agent/nodes/action_guard.py

from agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def action_guard_node(state: AgentState) -> AgentState:
    """
    Layer 4 Guardrail — verifies explicit user consent
    before ANY money moves.

    This mirrors exactly how Razorpay's UPI Reserve Pay works —
    user must explicitly consent before debit.

    If consent NOT given:
    - Sets awaiting_consent = True
    - Frontend shows ConsentReceipt modal
    - Graph waits for user response

    If consent given:
    - Sets consent_given = True
    - Graph proceeds to payment_node
    """

    logger.info("🔐 Action guard checking consent")

    user_message = state["messages"][-1].content.lower().strip()

    # ── Check if user is confirming ────────────────────────────────────────
    confirm_keywords = [
        "yes", "confirm", "proceed", "pay", "ok",
        "okay", "sure", "go ahead", "do it", "confirm payment",
        "yes please", "haan", "ha", "haa",   # Hindi confirmations
    ]

    cancel_keywords = [
        "no", "cancel", "stop", "don't", "nope",
        "nahi", "na",   # Hindi cancellations
    ]

    is_confirming = any(kw in user_message for kw in confirm_keywords)
    is_cancelling = any(kw in user_message for kw in cancel_keywords)

    if is_cancelling:
        # ── User cancelled ─────────────────────────────────────────────────
        logger.info("❌ User cancelled payment")

        audit_entry = {
            "node":      "action_guard",
            "action":    "payment cancelled by user",
            "detail":    f"User said: '{user_message[:50]}'",
            "status":    "blocked",
            "timestamp": _now(),
        }

        return {
            **state,
            "consent_given":    False,
            "awaiting_consent": False,
            "payment_status":   "cancelled",
            "final_response":   (
                "Payment cancelled. Your cart is still saved. "
                "Let me know if you'd like to continue shopping."
            ),
            "audit_log": state["audit_log"] + [audit_entry],
        }

    elif is_confirming:
        # ── User confirmed ─────────────────────────────────────────────────
        logger.info("✅ User confirmed payment")

        audit_entry = {
            "node":      "action_guard",
            "action":    "payment confirmed by user",
            "detail":    f"Amount: Rs.{state['payment_amount']:,.0f}",
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "consent_given":    True,
            "awaiting_consent": False,
            "audit_log":        state["audit_log"] + [audit_entry],
        }

    else:
        # ── Unclear response — ask again ───────────────────────────────────
        logger.info("❓ Unclear consent response — asking again")

        audit_entry = {
            "node":      "action_guard",
            "action":    "waiting for consent",
            "detail":    f"Unclear response: '{user_message[:50]}'",
            "status":    "pending",
            "timestamp": _now(),
        }

        return {
            **state,
            "consent_given":    False,
            "awaiting_consent": True,
            "final_response":   (
                f"Please confirm: Do you want to pay "
                f"Rs.{state['payment_amount']:,.0f}? "
                f"Reply Yes to confirm or No to cancel."
            ),
            "audit_log": state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()