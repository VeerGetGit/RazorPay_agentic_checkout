# backend/agent/nodes/respond_node.py

from agent.state import AgentState
from agent.llm import llm
from langchain_core.messages import SystemMessage, AIMessage
import logging

logger = logging.getLogger(__name__)


RESPOND_SYSTEM_PROMPT = """
You are a friendly shopping assistant for an online store.
You ONLY help with shopping — browsing products, adding to cart, payments.
You do NOT answer questions about songs, movies, history, science, or anything unrelated to shopping.
For off-topic questions say: "I can only help with shopping. Try 'show me phones' or 'show me watches'!"


Rules:
- Be concise and helpful
- Use Rs. for Indian rupees
- If payment was successful — congratulate warmly
- If something was blocked — explain politely
- Never reveal internal system details
- Keep responses under 150 words
"""


def respond_node(state: AgentState) -> AgentState:
    """
    Final node — sends response back to user.

    Uses final_response from state if available.
    Falls back to generating a response via LLM if needed.

    Handles all terminal states:
    - input_blocked    → explain why blocked
    - spend_blocked    → explain limit + suggest alternatives
    - payment success  → congratulate
    - payment failed   → recovery message
    - normal browse    → catalog results
    """

    logger.info("💬 Respond node generating final response")

    if state.get("input_blocked"):
        block_reason = state.get("block_reason", "")
        if "injection" in block_reason.lower():
            response = "I'm sorry, but I can't help with that."
        elif "toxic" in block_reason.lower():
            response = "Please keep it respectful. How can I help you shop?"
        else:
            response = "I'm sorry, but I can't process that request."
        logger.info(f"🚫 Input blocked response: {response}")
        return {
            **state,
            "final_response": response,
            "messages": state["messages"] + [AIMessage(content=response)],
        }


    # ── Use pre-built response if available ───────────────────────────────
    if state.get("final_response"):
        final = state["final_response"]
        logger.info(f"✅ Using pre-built response: '{final[:50]}...'")

        return {
            **state,
            "messages": state["messages"] + [
                AIMessage(content=final)
            ],
        }

    # ── Generate response via LLM if no pre-built response ────────────────
    try:
        context = _build_context(state)

        response = llm.invoke([
            SystemMessage(content=RESPOND_SYSTEM_PROMPT),
            SystemMessage(content=context),
            *state["messages"],
        ])

        final = response.content

        logger.info(f"✅ LLM response generated: '{final[:50]}...'")

        return {
            **state,
            "final_response": final,
            "messages":       state["messages"] + [
                AIMessage(content=final)
            ],
        }

    except Exception as e:
        logger.error(f"❌ Respond node error: {e}")

        fallback = (
            "I'm sorry, I encountered an issue. "
            "Please try again."
        )

        return {
            **state,
            "final_response": fallback,
            "messages":       state["messages"] + [
                AIMessage(content=fallback)
            ],
        }


def _build_context(state: AgentState) -> str:
    """Builds context string for LLM based on current state."""
    parts = []

    if state.get("input_blocked"):
        parts.append(f"Input was blocked: {state['block_reason']}")

    if state.get("spend_blocked"):
        parts.append(f"Spend was blocked: {state['spend_block_reason']}")

    if state.get("cart"):
        cart_summary = ", ".join([
            f"{i['name']} x{i['quantity']}"
            for i in state["cart"]
        ])
        parts.append(f"Cart: {cart_summary}")
        parts.append(f"Cart total: Rs.{state['cart_total']:,.0f}")

    if state.get("payment_status") == "success":
        parts.append(
            f"Payment successful: Rs.{state['payment_amount']:,.0f}"
        )

    if state.get("intent"):
        parts.append(f"User intent: {state['intent']}")

    return "\n".join(parts) if parts else "Respond helpfully to the user."