# backend/agent/nodes/catalog_node.py

from agent.state import AgentState
from agent.llm import llm
from agent.tools.catalog_tools import (
    search_catalog,
    get_product_by_id,
    get_alternatives,
    catalog_tools,
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json
import logging

logger = logging.getLogger(__name__)

CATALOG_SYSTEM_PROMPT = """
You are a helpful shopping assistant for an online store.

You have access to these tools:
- search_catalog(query): search products by name, category or description
- get_product_by_id(product_id): get full details of a specific product
- get_alternatives(category, max_price): find similar products

Rules:
- Always search catalog before recommending products
- Show maximum 5 products at a time
- Always mention the price clearly with Rs. symbol
- If item is out of stock mention it clearly
- Suggest alternatives for out of stock items
- Be concise and friendly
- Never make up prices — only use prices from search results
"""

# Bind tools to LLM
llm_with_tools = llm.bind_tools(catalog_tools)


def catalog_node(state: AgentState) -> AgentState:
    """
    Handles all browse/search requests.
    Uses tool-calling to search the catalog.
    Updates cart when user adds items.

    Flow:
    1. LLM decides which tool to call
    2. Tool executes (hits SQLite — no Groq call)
    3. LLM formats the response
    4. State updated with new messages + cart
    """

    user_message = state["messages"][-1].content
    logger.info(f"🛍️ Catalog node processing: '{user_message[:50]}...'")

    try:
        # Step 1 — LLM decides which tool to call
        messages = [
            SystemMessage(content=CATALOG_SYSTEM_PROMPT),
            *state["messages"],
        ]

        response = llm_with_tools.invoke(messages)

        # Step 2 — Execute tool calls if any
        tool_results = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"🔧 Tool called: {tool_name}({tool_args})")

                # Execute the right tool
                if tool_name == "search_catalog":
                    result = search_catalog.invoke(tool_args)
                elif tool_name == "get_product_by_id":
                    result = get_product_by_id.invoke(tool_args)
                elif tool_name == "get_alternatives":
                    result = get_alternatives.invoke(tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"

                tool_results.append({
                    "tool":   tool_name,
                    "args":   tool_args,
                    "result": result,
                })

                # Log to audit
                logger.info(f"✅ Tool result: {str(result)[:100]}...")

        # Step 3 — Check if user is adding to cart
        cart = state["cart"]
        cart_total = state["cart_total"]

        if _is_add_to_cart(user_message) and tool_results:
            # Try to extract product from tool results
            product_data = _extract_product(tool_results)
            if product_data and product_data.get("in_stock", True):
                cart, cart_total = _add_to_cart(
                    cart, cart_total, product_data
                )
                logger.info(
                    f"🛒 Added to cart: {product_data.get('name')} "
                    f"₹{product_data.get('price')}"
                )

        # Step 4 — Format final response
        final_response = response.content or _format_tool_results(tool_results)

        # Audit entry
        audit_entry = {
            "node":      "catalog_node",
            "action":    f"searched catalog — {len(tool_results)} tool(s) called",
            "detail":    str([t["tool"] for t in tool_results]),
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "messages":      state["messages"] + [AIMessage(content=final_response)],
            "cart":          cart,
            "cart_total":    cart_total,
            "final_response": final_response,
            "audit_log":     state["audit_log"] + [audit_entry],
        }

    except Exception as e:
        logger.error(f"❌ Catalog node error: {e}")

        audit_entry = {
            "node":      "catalog_node",
            "action":    "error",
            "detail":    str(e),
            "status":    "failed",
            "timestamp": _now(),
        }

        return {
            **state,
            "final_response": "Sorry, I had trouble searching the catalog. Please try again.",
            "audit_log":      state["audit_log"] + [audit_entry],
        }


# ── Helper functions ───────────────────────────────────────────────────────

def _is_add_to_cart(message: str) -> bool:
    """Check if user wants to add something to cart."""
    keywords = ["add", "cart", "want", "take", "get", "buy", "purchase"]
    return any(kw in message.lower() for kw in keywords)


def _extract_product(tool_results: list) -> dict | None:
    """Extract product data from tool results."""
    for result in tool_results:
        if result["tool"] == "get_product_by_id":
            try:
                return json.loads(result["result"])
            except Exception:
                pass
    return None


def _add_to_cart(
    cart:       list,
    cart_total: float,
    product:    dict,
    quantity:   int = 1
) -> tuple:
    """Add product to cart and recalculate total."""

    # Check if already in cart
    for item in cart:
        if item["product_id"] == product["id"]:
            item["quantity"] += quantity
            item["total"]     = item["price"] * item["quantity"]
            cart_total        = sum(i["total"] for i in cart)
            return cart, cart_total

    # Add new item
    cart.append({
        "product_id": product["id"],
        "name":       product["name"],
        "price":      product["price"],
        "quantity":   quantity,
        "total":      product["price"] * quantity,
    })

    cart_total = sum(i["total"] for i in cart)
    return cart, cart_total


def _format_tool_results(tool_results: list) -> str:
    """Format tool results into readable response."""
    if not tool_results:
        return "I couldn't find any products. Please try a different search."

    parts = []
    for result in tool_results:
        parts.append(result["result"])

    return "\n\n".join(parts)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()