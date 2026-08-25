# backend/agent/nodes/intent_node.py

from agent.state import AgentState
from agent.llm import llm_mini as llm
from langchain_core.messages import SystemMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a shopping assistant.

Classify the user message into EXACTLY one of these intents:
- browse    : user wants to search, view, explore products, ask what's available, or add items to cart
- checkout  : user wants to buy, pay, purchase, or confirm payment
- status    : user wants to know order status or what's in their cart
- cancel    : user wants to cancel an order
- unknown   : completely unrelated to shopping

Rules:
- Reply with ONLY the intent word in lowercase
- Be generous — when in doubt → browse
- Greetings like "hey", "hi", "hello" → browse
- "what do you have", "what can I buy" → browse
- i want to buy 'X' where X is a product → browse
- buy it' or 'yes' alone → checkout
- "what is my cart", "show my cart" → status
- "buy it", "yes confirm", "pay now" → checkout
- Math homework, coding questions → unknown

Examples:
"show me phones"                    → browse
"hey what products do you have?"    → browse
"can you show me something nice?"   → browse
"what's available?"                 → browse
"add the Pixel 8 to cart"           → browse
"I need a budget phone"             → browse
"i want to buy a watch as a gift"   → browse
"i want to buy something"           → browse
"i want to shop"                    → browse
"buy it"                            → checkout
"yes confirm"                       → checkout
"buy it"                            → checkout
"yes confirm"                       → checkout
"what is my cart?"                  → status
"what is my order status"           → status
"write me an essay"                 → unknown
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