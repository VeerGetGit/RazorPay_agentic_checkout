# backend/agent/nodes/catalog_node.py

from agent.state import AgentState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from db.database import SessionLocal
from db.models import Product
import logging
import re

logger = logging.getLogger(__name__)


def _is_add_to_cart(message: str) -> bool:
    keywords = ["add", "cart", "take", "get me", "purchase", "want", "i'll take", "give me"]
    return any(kw in message.lower() for kw in keywords)


def _extract_product_name(message: str) -> str:
    result = message.strip()
    patterns = [
        r'^add\s+the\s+', r'^add\s+', r'\s+to\s+my\s+cart$',
        r'\s+to\s+cart$', r'^i\s+want\s+', r'^get\s+me\s+',
        r'^buy\s+the\s+', r'^buy\s+', r'^purchase\s+',
        r'^i\'ll\s+take\s+', r'^give\s+me\s+',
    ]
    for p in patterns:
        result = re.sub(p, '', result, flags=re.IGNORECASE)
    return result.strip()


def _extract_search_keyword(message: str) -> str:
    from agent.llm import llm_mini
    try:
        response = llm_mini.invoke([
            SystemMessage(content=(
                "You are a product search keyword extractor for a shopping store.\n"
                "The store sells: phones, shoes, bags, watches.\n"
                "Brands: iPhone, Samsung, Pixel, OnePlus, Redmi (phones), "
                "Nike, Adidas, Puma, Skechers, New Balance (shoes), "
                "Safari, Wildcraft, Lavine, Skybags (bags), "
                "Apple Watch, Samsung Watch, Titan, Fastrack, Noise (watches).\n\n"
                "Extract ONLY the product name or category.\n"
                "Reply with ONE of: phones, shoes, bags, watches, "
                "or the exact product/brand name.\n"
                "Reply 'all' if user wants everything.\n"
                "Reply 'cart' if asking about cart.\n\n"
                "Examples:\n"
                "'show me phones' → phones\n"
                "'I want Titan Edge Ceramic' → Titan Edge Ceramic\n"
                "'add Titan to cart' → Titan\n"
                "'I need a budget phone' → phones\n"
                "'what do you have' → all\n"
                "'show me watches' → watches\n"
                "'what is my cart' → cart\n"
                "'show me something nice' → all\n"
                "ONLY reply with the keyword. Nothing else."
            )),
            HumanMessage(content=message)
        ])
        keyword = response.content.strip().lower()
        logger.info(f"🔍 Extracted keyword: '{keyword}'")
        return keyword
    except Exception as e:
        logger.error(f"❌ Keyword extraction error: {e}")
        return message


def _is_cart_query(message: str) -> bool:
    keywords = [
        "what is my cart", "show my cart", "view cart",
        "cart items", "what's in my cart", "my cart",
        "show cart", "cart total", "what have i added"
    ]
    return any(kw in message.lower() for kw in keywords)


def _get_cart_response(state: AgentState) -> str:
    cart = state["cart"]
    if cart:
        lines = "\n".join([
            f"• {i['name']} x{i['quantity']} = ₹{i['total']:,.0f}"
            for i in cart
        ])
        return (
            f"🛒 Your cart:\n\n{lines}\n\n"
            f"Total: ₹{state['cart_total']:,.0f}\n\n"
            f"Say 'buy it' to checkout."
        )
    return (
        "Your cart is empty. 🛒\n\n"
        "Try: 'show me phones' or 'show me shoes'"
    )


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def catalog_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    logger.info(f"🛍️ Catalog node: '{user_message[:50]}'")

    try:
        # ── Cart query ─────────────────────────────────────────────────────
        if _is_cart_query(user_message):
            response = _get_cart_response(state)
            return {
                **state,
                "messages":       state["messages"] + [AIMessage(content=response)],
                "final_response": response,
            }

        # ── Determine search term ──────────────────────────────────────────
        if _is_add_to_cart(user_message):
            search_term = _extract_product_name(user_message)
            is_adding   = True
        else:
            extracted   = _extract_search_keyword(user_message)
            is_adding   = False

            if extracted in ["all", "everything", "anything"]:
                response = (
                    "Welcome! Here's what we have:\n\n"
                    "• 📱 **Phones** — say 'show me phones'\n"
                    "• 👟 **Shoes** — say 'show me shoes'\n"
                    "• 👜 **Bags** — say 'show me bags'\n"
                    "• ⌚ **Watches** — say 'show me watches'\n\n"
                    "What would you like to explore?"
                )
                return {
                    **state,
                    "messages":       state["messages"] + [AIMessage(content=response)],
                    "final_response": response,
                }

            if extracted == "cart":
                response = _get_cart_response(state)
                return {
                    **state,
                    "messages":       state["messages"] + [AIMessage(content=response)],
                    "final_response": response,
                }

            search_term = extracted

        logger.info(f"🔍 Searching: '{search_term}' | adding: {is_adding}")

        # ── Search DB ──────────────────────────────────────────────────────
        db = SessionLocal()
        products = db.query(Product).filter(
            Product.name.ilike(f"%{search_term}%") |
            Product.category.ilike(f"%{search_term}%") |
            Product.description.ilike(f"%{search_term}%")
        ).limit(5).all()

        if not products:
            keyword_map = {
                "phone": "phones", "mobile": "phones",
                "shoe": "shoes", "sneaker": "shoes", "boot": "shoes",
                "bag": "bags", "backpack": "bags",
                "watch": "watches", "smartwatch": "watches",
            }
            for kw, cat in keyword_map.items():
                if kw in search_term.lower():
                    products = db.query(Product).filter(
                        Product.category == cat
                    ).limit(5).all()
                    break
        db.close()

        cart       = list(state["cart"])
        cart_total = state["cart_total"]

        # ── Add to cart ────────────────────────────────────────────────────
        if is_adding and products:
            in_stock = [p for p in products if p.stock > 0]
            if in_stock:
                product = in_stock[0]
                found   = False
                for item in cart:
                    if item["product_id"] == str(product.id):
                        item["quantity"] += 1
                        item["total"]     = item["price"] * item["quantity"]
                        found = True
                        break
                if not found:
                    cart.append({
                        "product_id": str(product.id),
                        "name":       product.name,
                        "price":      product.price,
                        "quantity":   1,
                        "total":      product.price,
                    })
                cart_total = sum(i["total"] for i in cart)
                response = (
                    f"✅ Added {product.name} to cart!\n"
                    f"Price: ₹{product.price:,.0f}\n"
                    f"Cart total: ₹{cart_total:,.0f}\n\n"
                    f"Say 'buy it' to checkout."
                )
            else:
                db2  = SessionLocal()
                alts = db2.query(Product).filter(
                    Product.category == products[0].category,
                    Product.stock    >  0
                ).limit(3).all()
                db2.close()
                alt_lines = "\n".join([f"• {p.name} — ₹{p.price:,.0f}" for p in alts])
                response = (
                    f"❌ {products[0].name} is out of stock.\n\n"
                    f"Alternatives:\n{alt_lines}"
                )

        # ── Browse ─────────────────────────────────────────────────────────
        else:
            if products:
                lines = []
                for p in products:
                    stock = f"In stock ({p.stock})" if p.stock > 0 else "❌ Out of stock"
                    lines.append(
                        f"• {p.name} — ₹{p.price:,.0f} | {stock}\n"
                        f"  {p.description}"
                    )
                response = "Here are products from our catalog:\n\n" + "\n\n".join(lines)
            else:
                response = (
                    "I couldn't find that. We have:\n"
                    "• 📱 Phones — 'show me phones'\n"
                    "• 👟 Shoes — 'show me shoes'\n"
                    "• 👜 Bags — 'show me bags'\n"
                    "• ⌚ Watches — 'show me watches'\n\n"
                    "What would you like?"
                )

        audit_entry = {
            "node":      "catalog_node",
            "action":    f"searched '{search_term}' — {len(products)} results",
            "detail":    user_message[:100],
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "messages":       state["messages"] + [AIMessage(content=response)],
            "cart":           cart,
            "cart_total":     cart_total,
            "final_response": response,
            "audit_log":      state["audit_log"] + [audit_entry],
        }

    except Exception as e:
        logger.error(f"❌ Catalog node error: {e}")
        fallback = "I had trouble with that. We have phones, shoes, bags and watches. What would you like?"
        return {
            **state,
            "messages":       state["messages"] + [AIMessage(content=fallback)],
            "final_response": fallback,
        }