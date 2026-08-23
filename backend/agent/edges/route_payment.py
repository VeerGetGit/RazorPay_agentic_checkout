# backend/agent/edges/route_payment.py

from agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def route_payment(state: AgentState) -> str:
    """
    Conditional edge after payment_node.
    Routes based on payment success or failure.

    Returns:
        "success"  → audit_logger → output_guard → respond
        "failed"   → recovery_node → respond
    """

    if state.get("payment_failed"):
        retry_count = state.get("retry_count", 0)
        logger.info(
            f"🔀 Route: payment failed "
            f"(attempt {retry_count}) → recovery"
        )
        return "failed"

    if state.get("payment_status") == "success":
        logger.info("🔀 Route: payment success → audit_logger")
        return "success"

    # Default to failed if status unclear
    logger.warning("⚠️ Route: unclear payment status → recovery")
    return "failed"