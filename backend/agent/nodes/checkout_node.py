# backend/agent/nodes/checkout_node.py

from agent.state import AgentState
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)


def checkout_node(state: AgentState) -> AgentState:
    """
    Handles checkout flow.
    Builds order summary from cart WITHOUT LLM call.
    Sets awaiting_consent = True.
    """

    logger.info("💳 Checkout node processing")

    cart       = state["cart"]
    cart_total = state["cart_total"]

    # Check cart not empty
    if not cart or len(cart) == 0:
        audit_entry = {
            "node":      "checkout_node",
            "action":    "blocked — cart empty",
            "detail":    "User tried to checkout with empty cart",
            "status":    "blocked",
            "timestamp": _now(),
        }
        return {
            **state,
            "final_response":   "Your cart is empty. Please add items before checking out.",
            "awaiting_consent": False,
            "audit_log":        state["audit_log"] + [audit_entry],
        }

    # Build order summary without LLM
    remaining  = state["spend_limit"] - state["spent_so_far"]
    cart_lines = "\n".join([
        f"• {item['name']} x{item['quantity']} = ₹{item['total']:,.0f}"
        for item in cart
    ])

    summary = (
        f"🛒 Your Order Summary:\n\n"
        f"{cart_lines}\n\n"
        f"Total:     ₹{cart_total:,.0f}\n"
        f"Limit:     ₹{state['spend_limit']:,.0f}\n"
        f"Remaining: ₹{remaining:,.0f}\n\n"
        f"Reply **Yes** to confirm payment or **No** to cancel."
    )

    audit_entry = {
        "node":      "checkout_node",
        "action":    f"order summary built — ₹{cart_total:,.0f}",
        "detail":    f"{len(cart)} item(s) in cart",
        "status":    "success",
        "timestamp": _now(),
    }

    return {
        **state,
        "messages":         state["messages"] + [AIMessage(content=summary)],
        "payment_amount":   cart_total,
        "final_response":   summary,
        "awaiting_consent": True,
        "consent_given":    False,
        "audit_log":        state["audit_log"] + [audit_entry],
    }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()