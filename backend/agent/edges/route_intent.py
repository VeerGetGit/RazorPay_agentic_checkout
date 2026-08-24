# backend/agent/edges/route_intent.py

from agent.state import AgentState
import logging

logger = logging.getLogger(__name__)


def route_after_input_guard(state: AgentState) -> str:
    """Routes after input_guard node."""
    if state.get("input_blocked"):
        logger.info("🔀 Route: input blocked → respond")
        return "blocked"
    logger.info("🔀 Route: input passed → intent")
    return "intent"


def route_after_intent(state: AgentState) -> str:
    """Routes after intent node."""
    intent = state.get("intent", "unknown")
    logger.info(f"🔀 Route intent: {intent}")

    if intent == "browse":
        return "catalog"
    elif intent == "checkout":
        return "checkout"
    else:
        return "respond"