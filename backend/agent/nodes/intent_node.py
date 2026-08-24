# backend/agent/nodes/intent_node.py

from agent.state import AgentState
from agent.llm import llm_mini as llm
from langchain_core.messages import SystemMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a shopping assistant.

Classify the user message into EXACTLY one of these intents:
- browse    : user wants to search, view, or add items to cart
- checkout  : user wants to buy, pay, or purchase something
- status    : user wants order status
- cancel    : user wants to cancel
- unknown   : doesn't fit any category

Rules:
- Reply with ONLY the intent word in lowercase
- "add to cart" → browse
- "buy it", "buy everything", "purchase", "checkout", "pay" → checkout
- When in doubt → browse

Examples:
"show me phones"              → browse
"add the iPhone to cart"      → browse
"buy it"                      → checkout
"buy everything"              → checkout
"I want to purchase"          → checkout
"what is my order status"     → status
"write me a poem"             → unknown
"""


def intent_node(state: AgentState) -> AgentState:
    """
    Classifies user intent from latest message.
    Uses groq/compound for accurate classification.

    Sets state["intent"] to one of:
    browse / checkout / status / cancel / unknown

    Routes:
    browse   → catalog_node
    checkout → checkout_node
    status   → respond_node (with order status)
    cancel   → respond_node (with cancel info)
    unknown  → respond_node (with redirect message)
    """

    user_message = state["messages"][-1].content
    logger.info(f"🎯 Classifying intent for: '{user_message[:50]}...'")

    try:
        response = llm.invoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])

        intent = response.content.strip().lower()

        # Validate intent is one of allowed values
        allowed_intents = ["browse", "checkout", "status", "cancel", "unknown"]
        if intent not in allowed_intents:
            logger.warning(f"⚠️ Unexpected intent: '{intent}' → defaulting to browse")
            intent = "browse"

        logger.info(f"✅ Intent classified: {intent}")

        # Add to audit log
        audit_entry = {
            "node":      "intent_node",
            "action":    f"classified as {intent}",
            "detail":    f"Message: '{user_message[:100]}'",
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "intent":    intent,
            "audit_log": state["audit_log"] + [audit_entry],
        }

    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")

        # Default to browse on error — safest fallback
        audit_entry = {
            "node":      "intent_node",
            "action":    "error — defaulting to browse",
            "detail":    str(e),
            "status":    "failed",
            "timestamp": _now(),
        }

        return {
            **state,
            "intent":    "browse",
            "audit_log": state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()