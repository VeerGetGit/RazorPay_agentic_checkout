# backend/agent/nodes/catalog_node.py

from agent.state import AgentState
from langchain_core.messages import AIMessage
from db.database import SessionLocal
from db.models import Product
import logging
import re

logger = logging.getLogger(__name__)


def _is_add_to_cart(message: str) -> bool:
    keywords = ["add", "cart", "want", "take", "get me", "buy", "purchase"]
    return any(kw in message.lower() for kw in keywords)


def _extract_product_name(message: str) -> str:
    """
    Extracts product name from add-to-cart messages.
    'add the Pixel 8 to cart' → 'Pixel 8'
    'add Puma RS-X to cart'   → 'Puma RS-X'
    """
    result = message.strip()
    patterns = [
        r'^add\s+the\s+',
        r'^add\s+',
        r'\s+to\s+my\s+cart$',
        r'\s+to\s+cart$',
        r'^i\s+want\s+',
        r'^get\s+me\s+',
        r'^buy\s+the\s+',
        r'^buy\s+',
        r'^purchase\s+',
    ]
    for p in patterns:
        result = re.sub(p, '', result, flags=re.IGNORECASE)
    return result.strip()


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def catalog_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    logger.info(f"🛍️ Catalog node: '{user_message[:50]}'")

    try:
        # Extract clean search term
        search_term = user_message
        if _is_add_to_cart(user_message):
            search_term = _extract_product_name(user_message)
            logger.info(f"🔍 Extracted search term: '{search_term}'")

        db = SessionLocal()

        # Search catalog directly
        products = db.query(Product).filter(
            Product.name.ilike(f"%{search_term}%") |
            Product.category.ilike(f"%{search_term}%") |
            Product.description.ilike(f"%{search_term}%")
        ).limit(5).all()

        # Broader keyword search if nothing found
        if not products:
            keyword_map = {
                "phone":      "phones",
                "mobile":     "phones",
                "shoe":       "shoes",
                "sneaker":    "shoes",
                "boot":       "shoes",
                "bag":        "bags",
                "backpack":   "bags",
                "watch":      "watches",
                "smartwatch": "watches",
            }
            for kw, cat in keyword_map.items():
                if kw in search_term.lower():
                    products = db.query(Product).filter(
                        Product.category == cat
                    ).limit(5).all()
                    break

        db.close()

        # Build cart
        cart = list(state["cart"])
        cart_total = state["cart_total"]

        # ── Add to cart ────────────────────────────────────────────────────
        if _is_add_to_cart(user_message) and products:
            in_stock = [p for p in products if p.stock > 0]

            if in_stock:
                product = in_stock[0]
                found = False
                for item in cart:
                    if item["product_id"] == str(product.id):
                        item["quantity"] += 1
                        item["total"] = item["price"] * item["quantity"]
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

                cart_total = sum(item["total"] for item in cart)
                response = (
                    f"✅ Added {product.name} to cart!\n"
                    f"Price: ₹{product.price:,.0f}\n"
                    f"Cart total: ₹{cart_total:,.0f}\n\n"
                    f"Say 'buy it' to checkout."
                )

            else:
                # Out of stock — find alternatives
                db2 = SessionLocal()
                alts = db2.query(Product).filter(
                    Product.category == products[0].category,
                    Product.stock > 0
                ).limit(3).all()
                db2.close()

                alt_lines = "\n".join([
                    f"• {p.name} — ₹{p.price:,.0f}"
                    for p in alts
                ])
                response = (
                    f"❌ {products[0].name} is out of stock.\n\n"
                    f"Here are some alternatives:\n{alt_lines}"
                )

        # ── Browse / Search ────────────────────────────────────────────────
        else:
            if products:
                lines = []
                for p in products:
                    stock = f"In stock ({p.stock})" if p.stock > 0 else "❌ Out of stock"
                    lines.append(
                        f"• {p.name} — ₹{p.price:,.0f} | {stock}\n"
                        f"  {p.description}\n"
                        f"  ID: {p.id}"
                    )
                response = (
                    "Here are products from our catalog:\n\n"
                    + "\n\n".join(lines)
                )
            else:
                response = (
                    "No products found matching your search. "
                    "Try searching for: phones, shoes, bags, or watches."
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
        fallback = "Sorry, I had trouble searching the catalog. Please try again."
        return {
            **state,
            "messages":       state["messages"] + [AIMessage(content=fallback)],
            "final_response": fallback,
        }