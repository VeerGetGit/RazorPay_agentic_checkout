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
- "i want to buy X" where X is a product → browse
- "buy it" or "yes" alone → checkout
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
"what is my cart?"                  → status
"what is my order status"           → status
"write me an essay"                 → unknown
"Questions about songs, movies, general knowledge" → unknown
" 'what is dil dediya', 'who is modi'" → unknown
"""


def intent_node(state: AgentState) -> AgentState:
    """
    Classifies user intent from latest message.
    Uses keyword matching first, then LLM as fallback.
    """

    user_message = state["messages"][-1].content
    msg          = user_message.lower().strip()
    logger.info(f"🎯 Classifying intent for: '{user_message[:50]}'")

    def make_audit(intent, method="keyword"):
        return {
            "node":      "intent_node",
            "action":    f"classified as {intent} ({method})",
            "detail":    f"Message: '{user_message[:100]}'",
            "status":    "success",
            "timestamp": _now(),
        }

    # ── Fast keyword classification ────────────────────────────────────────

    # Checkout
    checkout_keywords = [
        "buy it", "yes confirm", "pay now", "confirm payment",
        "proceed to pay", "place order", "yes please pay",
        "haan", "confirm", "proceed","checkout karna",
        "khareed","purchase karna"
    ]
    if any(kw in msg for kw in checkout_keywords):
        logger.info("✅ Intent: checkout (keyword)")
        return {
            **state,
            "intent":    "checkout",
            "audit_log": state["audit_log"] + [make_audit("checkout")],
        }

    #status
    status_keywords = [
        "what is my cart", "show my cart", "my cart",
        "what is in my cart", "cart total", "order status",
        "show me my cart", "view cart", "what have i added",
        "what is my order", "remaining limit",
        "how much have i spent", "how much left",
        "budget left", "how much money",
        "kitna bacha", "how much do i have",
        "paisa kitna", "money left",
        "money do i have", "money i left",
        "how much i have", "i have left",
        "bacha hai", "kitna hai",
        "how much money i",      # ← add
        "money left with",       # ← add
        "kitna hai mera",        # ← add
        "how much remaining",    # ← add
        "now how much",          # ← add
        "what is my total",
        "what's my total",
        "my total"
    ]

    if any(kw in msg for kw in status_keywords):
        logger.info("✅ Intent: status (keyword)")
        return {
            **state,
            "intent":    "status",
            "audit_log": state["audit_log"] + [make_audit("status")],
        }

    # Browse — greetings and common phrases
    browse_keywords = [
        "hello", "hi ", "hey", "what can you do",
        "help me", "show me", "i want", "i need",
        "add ", "search", "looking for", "do you have",
        "do you sell", "what do you", "can you show",
        "recommend", "suggest", "explore", "browse",
        "what is trending", "what's good",
    ]
    if any(kw in msg for kw in browse_keywords):
        logger.info("✅ Intent: browse (keyword)")
        return {
            **state,
            "intent":    "browse",
            "audit_log": state["audit_log"] + [make_audit("browse")],
        }

    # Cancel
    cancel_keywords = ["cancel my order", "cancel order", "i want to cancel"]
    if any(kw in msg for kw in cancel_keywords):
        logger.info("✅ Intent: cancel (keyword)")
        return {
            **state,
            "intent":    "cancel",
            "audit_log": state["audit_log"] + [make_audit("cancel")],
        }

    # ── LLM fallback ───────────────────────────────────────────────────────
    try:
        response = llm.invoke([
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])

        intent = response.content.strip().lower()

        allowed_intents = ["browse", "checkout", "status", "cancel", "unknown"]
        if intent not in allowed_intents:
            logger.warning(f"⚠️ Unexpected intent: '{intent}' → defaulting to browse")
            intent = "browse"

        logger.info(f"✅ Intent classified: {intent} (LLM)")

        return {
            **state,
            "intent":    intent,
            "audit_log": state["audit_log"] + [make_audit(intent, "llm")],
        }

    except Exception as e:
        logger.error(f"❌ Intent classification error: {e}")
        return {
            **state,
            "intent":    "browse",
            "audit_log": state["audit_log"] + [{
                "node":      "intent_node",
                "action":    "error — defaulting to browse",
                "detail":    str(e),
                "status":    "failed",
                "timestamp": _now(),
            }],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()