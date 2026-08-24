# backend/agent/nodes/action_guard.py

from agent.state import AgentState
from langchain_core.messages import HumanMessage
import logging

logger = logging.getLogger(__name__)


def action_guard_node(state: AgentState) -> AgentState:
    """
    Layer 4 Guardrail — verifies explicit user consent
    before ANY money moves.
    """

    logger.info("🔐 Action guard checking consent")

    
    human_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    user_message   = human_messages[-1].content.lower().strip() if human_messages else ""
    logger.info(f"🔐 User message: '{user_message}'")

    confirm_keywords = [
        "yes", "confirm", "proceed", "pay", "ok",
        "okay", "sure", "go ahead", "do it",
        "confirm payment", "buy it", "buy",
        "purchase", "yes please", "haan", "ha",
    ]

    cancel_keywords = [
        "cancel", "stop", "nope", "nahi",
        "don't proceed", "do not", "abort",
    ]

    is_confirming = any(kw in user_message for kw in confirm_keywords)
    is_cancelling = any(kw in user_message for kw in cancel_keywords)

    # User says "no" alone — only cancel if EXACTLY "no"
    if user_message.strip() in ["no", "nope", "nahi", "na"]:
        is_cancelling = True
        is_confirming = False

    logger.info(f"🔐 Confirming: {is_confirming} | Cancelling: {is_cancelling}")

    if is_confirming and not is_cancelling:
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

    elif is_cancelling:
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

    else:
        # ── Unclear — ask again ────────────────────────────────────────────
        logger.info("❓ Unclear consent — asking again")

        audit_entry = {
            "node":      "action_guard",
            "action":    "waiting for consent",
            "detail":    f"Unclear: '{user_message[:50]}'",
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