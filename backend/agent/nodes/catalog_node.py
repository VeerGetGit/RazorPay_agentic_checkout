# backend/agent/nodes/catalog_node.py

from agent.state import AgentState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from db.database import SessionLocal
from db.models import Product
import logging
import re

logger = logging.getLogger(__name__)


def _is_add_to_cart(message: str) -> bool:
    msg = message.lower().strip()

    explicit = [
        r'\badd\b', r'\bpurchase\b',
        r'\bgive\s+me\b', r'\bget\s+me\b',
        r"i'll\s+take\b",
    ]
    if any(re.search(p, msg) for p in explicit):
        return True

    if re.search(r'\bbuy\s+\w+', msg) and "buy it" not in msg:
        if re.search(r'\bbuy\s+with\b', msg):
            return False
        if re.search(r'\bcan\s+i\s+buy\b', msg):
            return False
        if re.search(r'\bto\s+buy\b', msg):
            return False
        if re.search(r'\bbuy\s+a\b', msg):
            return False
        return True

    vague_words = [
        "to see", "to browse", "to show", "to check",
        "to do", "to explore", "to find", "to look",
        "to shop", "to know", "to understand",
        "something", "anything", "everything",
        "to get", "help", "assistance",
    ]

    if re.search(r'\bi\s+want\b', msg):
        if any(vague in msg for vague in vague_words):
            return False
        after_want = re.sub(r'.*i\s+want\s+', '', msg).strip()
        if len(after_want) > 2:
            return True

    if re.search(r'\bi\s+need\b', msg):
        if any(vague in msg for vague in vague_words):
            return False
        after_need = re.sub(r'.*i\s+need\s+', '', msg).strip()
        if len(after_need) > 2:
            return True

    return False


def _is_remove_from_cart(message: str) -> bool:
    keywords = ["remove", "delete from cart", "take out", "don't want", "dont want", "remove the expensive", "remove expensive",  # ← add
        "remove the cheapest", "remove cheapest","actually no", "no remove", "don't add", "cancel that"]
    return any(kw in message.lower() for kw in keywords)


def _is_cart_query(message: str) -> bool:
    keywords = [
        "what is my cart", "show my cart", "view cart",
        "what's in my cart", "what is in my cart",
        "show me my cart", "cart total", "what have i added",
        "what is in my cart now", "what is my cart now",
        "show me cart","show me cart", "what is my total",    # ← add
        "what's my total", "my total",          # ← add
        "cart mein kya", "kitna total", 
    ]
    msg = message.lower()
    if any(add in msg for add in ["add", "buy", "put", "remove"]):
        return False
    return any(kw in msg for kw in keywords)


def _extract_product_name(message: str) -> str:
    result = message.strip()
    patterns = [
        r'^add\s+the\s+', r'^add\s+', r'\s+to\s+my\s+cart$',
        r'\s+to\s+cart$', r'^i\s+want\s+', r'^i\s+need\s+',
        r'^i\'d\s+like\s+', r'^i\s+would\s+like\s+',
        r'^get\s+me\s+', r'^get\s+the\s+',
        r'^buy\s+the\s+', r'^buy\s+', r'^purchase\s+',
        r'^i\'ll\s+take\s+', r'^give\s+me\s+',
        r'\s+i\s+want\s+that$', r'\s+i\s+loved\s+it$',
        r'\s+i\s+love\s+it$', r'\s+please$', r'\s+for\s+me$',
        r'^also\s+add\s+', r'^also\s+',
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
                "Brands:\n"
                "- Phones: iPhone, Samsung Galaxy, Google Pixel, OnePlus, Redmi\n"
                "- Shoes: Nike Air Max, Adidas Ultraboost, Puma RS-X, New Balance, Skechers\n"
                "- Bags: Safari, American Tourister, Wildcraft, Lavie, Skybags\n"
                "- Watches: Apple Watch, Samsung Galaxy Watch, Fastrack, Titan Edge, Noise ColorFit\n\n"
                "Extract ONLY the product name or category.\n"
                "Reply with: phones, shoes, bags, watches, brand/product name, 'all', or 'cart'.\n\n"
                "Examples:\n"
                "'show me phones' → phones\n"
                "'budget watch' → watches\n"
                "'what do you have' → all\n"
                "'hello' → all\n"
                "'i am looking for a gift' → all\n"
                "'recommend something' → all\n"
                "ONLY the keyword. Nothing else."
            )),
            HumanMessage(content=message)
        ])
        keyword = response.content.strip().lower()
        logger.info(f"🔍 Extracted keyword: '{keyword}'")
        return keyword
    except Exception as e:
        logger.error(f"❌ Keyword extraction error: {e}")
        return "all"


def _search_products(search_term: str) -> list:
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.name.ilike(f"%{search_term}%") |
            Product.category.ilike(f"%{search_term}%") |
            Product.description.ilike(f"%{search_term}%")
        ).limit(5).all()

        if not products:
            keyword_map = {
                "phone": "phones", "mobile": "phones", "smartphone": "phones",
                "shoe": "shoes", "sneaker": "shoes", "boot": "shoes",
                "bag": "bags", "backpack": "bags", "luggage": "bags",
                "watch": "watches", "smartwatch": "watches",
            }
            for kw, cat in keyword_map.items():
                if kw in search_term.lower():
                    products = db.query(Product).filter(
                        Product.category == cat
                    ).limit(5).all()
                    if products:
                        break

        if not products:
            words = [w for w in search_term.split() if len(w) > 2]
            for word in words:
                products = db.query(Product).filter(
                    Product.name.ilike(f"%{word}%") |
                    Product.description.ilike(f"%{word}%")
                ).limit(5).all()
                if products:
                    break

        if not products and "-" in search_term:
            clean = search_term.replace("-", " ")
            brand = search_term.split("-")[0].strip().split()[-1] 
            products = db.query(Product).filter(
                Product.name.ilike(f"%{clean}%") |
                Product.name.ilike(f"%{brand}%")
            ).limit(5).all()


        if not products:
            brand_map = {
                "puma": "Puma",
                "nike": "Nike",
                "adidas": "Adidas",
                "apple": "Apple",
                "samsung": "Samsung",
                "fastrack": "Fastrack",
                "titan": "Titan",
                "noise": "Noise",
                "redmi": "Redmi",
                "oneplus": "OnePlus",
                "pixel": "Pixel",
                "iphone": "iPhone",
                "safari": "Safari",
                "wildcraft": "Wildcraft",
                "skybags": "Skybags",
                "lavie": "Lavie",
                "skechers": "Skechers",
            }
            for brand_key, brand_name in brand_map.items():
                if brand_key in search_term.lower():
                    products = db.query(Product).filter(
                        Product.name.ilike(f"%{brand_name}%")
                    ).limit(5).all()
                    if products:
                        break

        return products
    finally:
        db.close()


def _get_cart_response(state: AgentState) -> str:
    cart = state["cart"]
    if cart:
        lines = "\n".join([
            f"• {i['name']} × {i['quantity']} = ₹{i['total']:,.0f}"
            for i in cart
        ])
        return (
            f"🛒 Your cart:\n\n{lines}\n\n"
            f"**Total: ₹{state['cart_total']:,.0f}**\n\n"
            f"Say 'buy it' to checkout or keep shopping!"
        )
    return (
        "Your cart is empty. 🛒\n\n"
        "Try:\n• 'show me phones'\n• 'show me shoes'\n• 'show me watches'"
    )


def _add_product_to_cart(cart: list, cart_total: float, product) -> tuple:
    found = False
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
    return cart, cart_total


def _remove_from_cart(cart: list, search_term: str) -> tuple:
    new_cart = [
        item for item in cart
        if search_term.lower() not in item["name"].lower()
    ]
    removed  = len(cart) - len(new_cart)
    total    = sum(i["total"] for i in new_cart)
    return new_cart, total, removed


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def catalog_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    logger.info(f"🛍️ Catalog node: '{user_message[:50]}'")

    try:
        cart       = list(state["cart"])
        cart_total = state["cart_total"]

        # ── Cart query ─────────────────────────────────────────────────────
        if _is_cart_query(user_message):
            response = _get_cart_response(state)
            return {
                **state,
                "messages":       state["messages"] + [AIMessage(content=response)],
                "final_response": response,
            }

        # ── Remaining limit query ──────────────────────────────────────────
        limit_keywords = [
            "remaining limit", "how much left", "spend left",
            "budget left", "how much can i spend", "how much do i have",
            "remaining budget", "how much remaining",
            "how much money",        
            "money i left",          
            "money left",            
            "kitna bacha",           
            "kitna hai",             
            "how much i have",       
            "i have left",           
            "bacha hai",             
            "left with",             
        ]
        if any(kw in user_message.lower() for kw in limit_keywords):
            remaining = state["spend_limit"] - state["spent_so_far"]
            response = (
                f"💰 Your spend summary:\n\n"
                f"Total limit:  ₹{state['spend_limit']:,.0f}\n"
                f"Spent:        ₹{state['spent_so_far']:,.0f}\n"
                f"Remaining:    ₹{remaining:,.0f}\n\n"
                f"Products within your budget:"
            )
            db = SessionLocal()
            budget_products = db.query(Product).filter(
                Product.price <= remaining,
                Product.stock > 0
            ).order_by(Product.price.desc()).limit(3).all()
            db.close()
            if budget_products:
                lines = "\n".join([
                    f"• {p.name} — ₹{p.price:,.0f}" for p in budget_products
                ])
                response += f"\n\n{lines}"
            return {
                **state,
                "messages":       state["messages"] + [AIMessage(content=response)],
                "final_response": response,
            }

                    # ── Budget category query ──────────────────────────────────────────
        budget_words = ["decent", "affordable", "cheap", "budget", "inexpensive", "not too expensive"]
        category_map = {
            "watch": "watches", "watches": "watches", "smartwatch": "watches",
            "phone": "phones", "phones": "phones", "mobile": "phones",
            "shoe": "shoes", "shoes": "shoes", "sneaker": "shoes",
            "bag": "bags", "bags": "bags", "backpack": "bags",
        }

        if any(w in user_message.lower() for w in budget_words):
            detected_category = None
            for keyword, category in category_map.items():
                if keyword in user_message.lower():
                    detected_category = category
                    break

            if detected_category:
                # Set price cap based on category
                price_cap = {
                    "watches": 20000,
                    "phones":  40000,
                    "shoes":   10000,
                    "bags":    5000,
                }.get(detected_category, 20000)

                db = SessionLocal()
                budget_products = db.query(Product).filter(
                    Product.category == detected_category,
                    Product.price <= price_cap,
                    Product.stock > 0
                ).order_by(Product.price.asc()).limit(5).all()
                db.close()

                if budget_products:
                    lines = []
                    for p in budget_products:
                        lines.append(
                            f"• **{p.name}** — ₹{p.price:,.0f} | In stock ({p.stock})\n"
                            f"  {p.description}"
                        )
                    response = (
                        f"Here are some affordable {detected_category}:\n\n"
                        + "\n\n".join(lines)
                        + "\n\nSay 'I want [product name]' to add to cart."
                    )
                    return {
                        **state,
                        "messages":       state["messages"] + [AIMessage(content=response)],
                        "final_response": response,
                    }


        # ── Remove from cart ───────────────────────────────────────────────
        if _is_remove_from_cart(user_message):
            clean = (user_message.lower()
                .replace("remove", "").replace("delete", "")
                .replace("from cart", "").replace("from my cart", "")
                .replace("don't want", "").replace("dont want", "")
                .replace("the ", "")
                .strip())
            search_term = _extract_product_name(clean) if clean else ""
            
             # Handle "expensive" and "cheapest" context
            if "expensive" in user_message.lower() and cart:
                most_expensive = max(cart, key=lambda x: x["total"])
                search_term = most_expensive["name"]

            if "cheapest" in user_message.lower() and cart:
                cheapest = min(cart, key=lambda x: x["total"])
                search_term = cheapest["name"]
            new_cart, new_total, removed = _remove_from_cart(cart, search_term)

            if removed > 0:
                response = (
                    f"✅ Removed from cart!\n"
                    f"Cart total: ₹{new_total:,.0f}\n\n"
                    f"Say 'buy it' to checkout or keep shopping."
                )
                cart       = new_cart
                cart_total = new_total
            else:
                response = f"I couldn't find '{search_term}' in your cart."

            return {
                **state,
                "messages":       state["messages"] + [AIMessage(content=response)],
                "cart":           cart,
                "cart_total":     cart_total,
                "final_response": response,
            }

        # ── Budget query ───────────────────────────────────────────────────
        # Handle "5k" = 5000
        k_match = re.search(r'(\d+)\s*k\b', user_message.lower())
        if k_match:
            budget = float(k_match.group(1)) * 1000
            is_budget_query = True
        else:
            budget_num = re.search(r'(\d+)', user_message)
            budget = float(budget_num.group(1)) if budget_num else 0
            is_budget_query = budget >= 100 and any(
                w in user_message.lower() for w in
                ["with", "under", "below", "within", "budget", "worth",
                 "in ", "something", "show me something", "kuch"]
            )

        if is_budget_query and budget >= 100:
            # Check if category mentioned
            category_filter = None
            if any(w in user_message.lower() for w in ["watch", "watches", "smartwatch"]):
                category_filter = "watches"
            elif any(w in user_message.lower() for w in ["phone", "phones", "mobile"]):
                category_filter = "phones"
            elif any(w in user_message.lower() for w in ["shoe", "shoes", "sneaker", "running"]):
                category_filter = "shoes"
            elif any(w in user_message.lower() for w in ["bag", "bags", "backpack"]):
                category_filter = "bags"

            db = SessionLocal()
            query = db.query(Product).filter(
                Product.price <= budget,
                Product.stock > 0
            )
            if category_filter:
                query = query.filter(Product.category == category_filter)
            budget_products = query.order_by(Product.price.desc()).limit(5).all()
            db.close()

            if budget_products:
                cat_text = f" in {category_filter}" if category_filter else ""
                lines = "\n".join([
                    f"• {p.name} — ₹{p.price:,.0f}"
                    for p in budget_products
                ])
                response = (
                    f"Here's what you can get{cat_text} under ₹{budget:,.0f}:\n\n"
                    f"{lines}\n\n"
                    f"Say 'I want [product name]' to add to cart."
                )
            else:
                response = f"Nothing available under ₹{budget:,.0f} right now."

            return {
                **state,
                "messages":       state["messages"] + [AIMessage(content=response)],
                "final_response": response,
            }


        # ── Add to cart ────────────────────────────────────────────────────
        if _is_add_to_cart(user_message):
            raw          = _extract_product_name(user_message)
            items_to_add = [
                i.strip() for i in re.split(r'\band\b|,|&', raw, flags=re.IGNORECASE)
                if i.strip()
            ]

            added     = []
            not_found = []

            for search_term in items_to_add:
                products = _search_products(search_term)
                if products:
                    in_stock = [p for p in products if p.stock > 0]
                    if in_stock:
                        product          = in_stock[0]
                        cart, cart_total = _add_product_to_cart(cart, cart_total, product)
                        added.append(product.name)
                    else:
                        not_found.append(f"{products[0].name} (❌ out of stock)")
                else:
                    not_found.append(search_term)

            if added:
                added_text = "\n".join([f"✅ {name}" for name in added])
                response = (
                    f"Added to cart:\n{added_text}\n\n"
                    f"Cart total: ₹{cart_total:,.0f}\n\n"
                    f"Say 'buy it' to checkout."
                )
                if not_found:
                    response += f"\n\nCouldn't add: {', '.join(not_found)}"
            else:
                if not_found:
                    response = "Sorry, couldn't add these items:\n"
                    response += "\n".join([f"• {item}" for item in not_found])

                    # Show alternatives if out of stock
                    if "out of stock" in " ".join(not_found):
                        out_of_stock_product = not_found[0].split(" (")[0]
                        db2 = SessionLocal()
                        out_p = db2.query(Product).filter(
                            Product.name.ilike(f"%{out_of_stock_product.split()[0]}%")
                        ).first()
                        if out_p:
                            alts = db2.query(Product).filter(
                                Product.category == out_p.category,
                                Product.stock > 0
                            ).limit(3).all()
                            if alts:
                                alt_lines = "\n".join([
                                    f"• {p.name} — ₹{p.price:,.0f}" for p in alts
                                ])
                                response += f"\n\nAvailable alternatives:\n{alt_lines}"
                        db2.close()
                else:
                    response = (
                        "I couldn't find those products.\n\n"
                        "We have phones, shoes, bags and watches.\n"
                        "Try being more specific."
                    )

        # ── Browse / Search ────────────────────────────────────────────────
        else:
            extracted = _extract_search_keyword(user_message)

            if extracted in ["all", "everything", "anything"]:
                response = (
                    "Welcome! Here's what we carry:\n\n"
                    "• 📱 **Phones** — iPhones, Samsung, Pixel, OnePlus, Redmi\n"
                    "• 👟 **Shoes** — Nike, Adidas, Puma, Skechers, New Balance\n"
                    "• 👜 **Bags** — Safari, Wildcraft, American Tourister, Lavie\n"
                    "• ⌚ **Watches** — Apple Watch, Samsung, Titan, Fastrack, Noise\n\n"
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

            products = _search_products(extracted)

            if products:
                lines = []
                for p in products:
                    stock = f"In stock ({p.stock})" if p.stock > 0 else "❌ Out of stock"
                    lines.append(
                        f"• **{p.name}** — ₹{p.price:,.0f} | {stock}\n"
                        f"  {p.description}"
                    )
                response = (
                    "Here are products from our catalog:\n\n"
                    + "\n\n".join(lines)
                    + "\n\nSay 'I want [product name]' to add to cart."
                )
            else:
                response = (
                    "I couldn't find that. 🔍\n\n"
                    "We have:\n"
                    "• 📱 Phones — say 'show me phones'\n"
                    "• 👟 Shoes — say 'show me shoes'\n"
                    "• 👜 Bags — say 'show me bags'\n"
                    "• ⌚ Watches — say 'show me watches'\n\n"
                    "What would you like?"
                )

        # ── Audit + Return ─────────────────────────────────────────────────
        audit_entry = {
            "node":      "catalog_node",
            "action":    f"processed: '{user_message[:50]}'",
            "detail":    f"cart items: {len(cart)}",
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
        fallback = "I had a small hiccup. We have phones, shoes, bags and watches. What would you like?"
        return {
            **state,
            "messages":       state["messages"] + [AIMessage(content=fallback)],
            "final_response": fallback,
        }