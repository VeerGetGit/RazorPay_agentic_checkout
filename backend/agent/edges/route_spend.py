# backend/agent/edges/route_spend.py

from agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def route_spend(state: AgentState) -> str:
    """
    Conditional edge after spend_guard_node.
    Routes based on whether spend was approved or blocked.

    Returns:
        "allowed"  → action_guard_node
        "blocked"  → respond_node
    """

    if state.get("spend_blocked"):
        logger.info("🔀 Route: spend blocked → respond")
        return "blocked"

    logger.info("🔀 Route: spend allowed → action_guard")
    return "allowed"


def route_consent(state: AgentState) -> str:
    """
    Conditional edge after action_guard_node.
    Routes based on whether user gave consent.

    Returns:
        "confirmed"  → payment_node
        "cancelled"  → respond_node
        "waiting"    → respond_node (show consent modal again)
    """

    if state.get("payment_status") == "cancelled":
        logger.info("🔀 Route: payment cancelled → respond")
        return "cancelled"

    if state.get("consent_given"):
        logger.info("🔀 Route: consent given → payment")
        return "confirmed"

    # Still waiting for consent
    logger.info("🔀 Route: awaiting consent → respond")
    return "waiting"