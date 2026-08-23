# backend/agent/nodes/checkout_node.py

from agent.state import AgentState
from agent.llm import llm
from langchain_core.messages import SystemMessage, AIMessage
import logging

logger = logging.getLogger(__name__)

CHECKOUT_SYSTEM_PROMPT = """
You are a checkout assistant for an online store.

Your job is to:
1. Summarize what is in the user's cart clearly
2. Show the total amount
3. Ask the user to confirm before payment
4. Be friendly and concise

Always show:
- Each item with name, quantity and price
- Total amount in Rs.
- Remaining spend limit
- A clear question asking if they want to proceed

Never:
- Process payment without explicit user confirmation
- Make up prices
- Add items user didn't ask for
"""


def checkout_node(state: AgentState) -> AgentState:
    """
    Handles checkout flow.
    Builds order summary from cart.
    Sets awaiting_consent = True to show ConsentReceipt modal.

    Flow:
    1. Check cart has items
    2. Build order summary
    3. Ask user to confirm
    4. Set awaiting_consent = True
    5. Route to spend_guard
    """

    logger.info("💳 Checkout node processing")

    cart       = state["cart"]
    cart_total = state["cart_total"]

    # ── Check cart is not empty ────────────────────────────────────────────
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
            "final_response":  "Your cart is empty. Please add items before checking out.",
            "awaiting_consent": False,
            "audit_log":       state["audit_log"] + [audit_entry],
        }

    # ── Build order summary ────────────────────────────────────────────────
    remaining = state["spend_limit"] - state["spent_so_far"]

    try:
        # Format cart for LLM
        cart_text = "\n".join([
            f"- {item['name']} x{item['quantity']} = Rs.{item['total']:,.0f}"
            for item in cart
        ])

        summary_prompt = f"""
Cart contents:
{cart_text}

Cart total:        Rs.{cart_total:,.0f}
Spend limit:       Rs.{state['spend_limit']:,.0f}
Already spent:     Rs.{state['spent_so_far']:,.0f}
Remaining limit:   Rs.{remaining:,.0f}

Generate a friendly checkout summary and ask the user
if they want to confirm the payment.
"""

        response = llm.invoke([
            SystemMessage(content=CHECKOUT_SYSTEM_PROMPT),
            *state["messages"],
            SystemMessage(content=summary_prompt),
        ])

        final_response = response.content

        # ── Log to audit ───────────────────────────────────────────────────
        audit_entry = {
            "node":      "checkout_node",
            "action":    f"order summary built — Rs.{cart_total:,.0f}",
            "detail":    f"{len(cart)} item(s) in cart",
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "messages":         state["messages"] + [AIMessage(content=final_response)],
            "payment_amount":   cart_total,
            "final_response":   final_response,
            "awaiting_consent": True,   # triggers ConsentReceipt modal
            "consent_given":    False,  # reset consent for this checkout
            "audit_log":        state["audit_log"] + [audit_entry],
        }

    except Exception as e:
        logger.error(f"❌ Checkout node error: {e}")

        audit_entry = {
            "node":      "checkout_node",
            "action":    "error",
            "detail":    str(e),
            "status":    "failed",
            "timestamp": _now(),
        }

        return {
            **state,
            "final_response": "Sorry I had trouble processing your cart. Please try again.",
            "audit_log":      state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()