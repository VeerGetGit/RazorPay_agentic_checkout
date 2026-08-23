# backend/agent/nodes/recovery_node.py

from agent.state import AgentState
from agent.llm import llm
from langchain_core.messages import SystemMessage
import logging

logger = logging.getLogger(__name__)

RECOVERY_SYSTEM_PROMPT = """
You are a helpful shopping assistant handling a payment failure.

Your job is to:
1. Acknowledge the failure clearly but calmly
2. Explain what went wrong in simple terms
3. Offer a clear next step

Be empathetic, brief and helpful.
Never blame the user.
Always offer at least one concrete next step.

If retry count is less than 3 — offer to retry.
If retry count is 3 or more — suggest contacting support.
"""


def recovery_node(state: AgentState) -> AgentState:
    """
    Handles ALL payment failures gracefully.
    This is Failure Scenario 1 from our demo.

    Failure types handled:
    - Razorpay API timeout
    - Payment gateway error
    - Network error
    - Any other exception from payment_node

    Recovery options offered:
    - Retry payment (if retry_count < 3)
    - Try different method
    - Contact support (if retry_count >= 3)

    Always returns a helpful message — never crashes.
    """

    failure_reason = state["failure_reason"]
    retry_count    = state["retry_count"]

    logger.info(
        f"🔄 Recovery node handling failure: "
        f"{failure_reason} (attempt {retry_count})"
    )

    try:
        # ── Build recovery context ─────────────────────────────────────────
        recovery_context = f"""
Payment failure details:
- Reason:       {failure_reason}
- Amount:       Rs.{state['payment_amount']:,.0f}
- Retry count:  {retry_count} of 3

Generate a helpful recovery message.
"""

        response = llm.invoke([
            SystemMessage(content=RECOVERY_SYSTEM_PROMPT),
            SystemMessage(content=recovery_context),
        ])

        recovery_message = response.content

        # ── Add retry option if under limit ───────────────────────────────
        if retry_count < 3:
            recovery_message += (
                "\n\nWould you like me to try again? "
                "Reply **Retry** to attempt payment again."
            )
        else:
            recovery_message += (
                "\n\nPlease contact Razorpay support at "
                "support@razorpay.com for assistance."
            )

        # ── Audit entry ────────────────────────────────────────────────────
        audit_entry = {
            "node":      "recovery_node",
            "action":    f"handled failure — attempt {retry_count}",
            "detail":    failure_reason,
            "status":    "recovered",
            "timestamp": _now(),
        }

        return {
            **state,
            "payment_failed":  False,   # reset for next attempt
            "final_response":  recovery_message,
            "audit_log":       state["audit_log"] + [audit_entry],
        }

    except Exception as e:
        # Even recovery failed — return hardcoded safe message
        logger.error(f"❌ Recovery node error: {e}")

        audit_entry = {
            "node":      "recovery_node",
            "action":    "recovery failed — using fallback",
            "detail":    str(e),
            "status":    "failed",
            "timestamp": _now(),
        }

        return {
            **state,
            "payment_failed": False,
            "final_response": (
                "We encountered an issue processing your payment. "
                "Please try again in a moment or contact support."
            ),
            "audit_log": state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()