# backend/agent/edges/route_intent.py

from agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def route_intent(state: AgentState) -> str:
    """
    Conditional edge after intent_node.
    Routes to the correct node based on classified intent.

    Returns:
        "catalog"   → catalog_node   (browse/search)
        "checkout"  → checkout_node  (buy/purchase)
        "respond"   → respond_node   (status/cancel/unknown)
        "blocked"   → respond_node   (input was blocked)
    """

    # First check if input was blocked
    if state.get("input_blocked"):
        logger.info("🔀 Route: input_blocked → respond")
        return "blocked"

    intent = state.get("intent", "unknown")
    logger.info(f"🔀 Route intent: {intent}")

    if intent == "browse":
        return "catalog"

    elif intent == "checkout":
        return "checkout"

    elif intent in ["status", "cancel", "unknown"]:
        return "respond"

    else:
        # Default to browse for anything unexpected
        logger.warning(f"⚠️ Unknown intent '{intent}' → defaulting to catalog")
        return "catalog"