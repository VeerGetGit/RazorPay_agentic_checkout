# backend/agent/tools/catalog_tools.py

from langchain_core.tools import tool
from functools import lru_cache
from db.database import SessionLocal
from db.models import Product
import json
import logging

logger = logging.getLogger(__name__)


# ── Cached catalog search ──────────────────────────────────────────────────
@lru_cache(maxsize=128)
def _search_products_cached(query: str) -> str:
    """
    Hits SQLite directly — NO Groq call needed.
    lru_cache means same query never runs twice.
    Saves ~40% of Groq quota during demo.
    Returns JSON string (cache requires hashable return).
    """
    db = SessionLocal()
    try:
        query_lower = query.lower()

        products = db.query(Product).filter(
            Product.name.ilike(f"%{query_lower}%") |
            Product.description.ilike(f"%{query_lower}%") |
            Product.category.ilike(f"%{query_lower}%")
        ).all()

        result = [
            {
                "id":          p.id,
                "name":        p.name,
                "description": p.description,
                "price":       p.price,
                "category":    p.category,
                "stock":       p.stock,
                "in_stock":    p.stock > 0,
            }
            for p in products
        ]

        return json.dumps(result)

    except Exception as e:
        logger.error(f"❌ Catalog search error: {e}")
        return json.dumps([])
    finally:
        db.close()


@tool
def search_catalog(query: str) -> str:
    """
    Search the product catalog by name, description or category.
    Returns list of matching products with prices and stock status.
    Use this when user asks to browse, search, or find products.

    Args:
        query: search term e.g. "phones", "running shoes", "nike"
    """
    logger.info(f"🔍 Catalog search: '{query}'")
    results_json = _search_products_cached(query)
    results      = json.loads(results_json)

    if not results:
        return f"No products found for '{query}'. Try a different search term."

    # Format for LLM response
    formatted = []
    for p in results[:5]:  # max 5 results to keep response concise
        stock_label = f"In stock ({p['stock']} available)" if p["in_stock"] \
                      else "❌ Out of stock"
        formatted.append(
            f"• {p['name']} — ₹{p['price']:,.0f} | {stock_label}\n"
            f"  {p['description']}\n"
            f"  ID: {p['id']}"
        )

    return "\n\n".join(formatted)


@tool
def get_product_by_id(product_id: str) -> str:
    """
    Get full details of a single product by its ID.
    Use this when user selects a specific product to add to cart.

    Args:
        product_id: the product UUID from search results
    """
    db = SessionLocal()
    try:
        product = db.query(Product).filter_by(id=product_id).first()

        if not product:
            return f"Product {product_id} not found."

        return json.dumps({
            "id":          product.id,
            "name":        product.name,
            "description": product.description,
            "price":       product.price,
            "category":    product.category,
            "stock":       product.stock,
            "in_stock":    product.stock > 0,
        })

    except Exception as e:
        logger.error(f"❌ Get product error: {e}")
        return "Error fetching product details."
    finally:
        db.close()


@tool
def get_alternatives(category: str, max_price: float) -> str:
    """
    Find alternative products in same category under a price limit.
    Used by recovery_node when item is out of stock or over budget.

    Args:
        category:  product category e.g. "shoes", "phones"
        max_price: maximum price in rupees
    """
    db = SessionLocal()
    try:
        alternatives = db.query(Product).filter(
            Product.category == category,
            Product.price    <= max_price,
            Product.stock    >  0
        ).order_by(Product.price.desc()).limit(3).all()

        if not alternatives:
            return f"No alternatives found in {category} under ₹{max_price:,.0f}"

        result = []
        for p in alternatives:
            result.append(
                f"• {p['name']} — ₹{p.price:,.0f}\n"
                f"  {p.description}"
            )

        return "Here are some alternatives:\n\n" + "\n\n".join(result)

    except Exception as e:
        logger.error(f"❌ Get alternatives error: {e}")
        return "Error fetching alternatives."
    finally:
        db.close()


# ── Tools list for LangChain ───────────────────────────────────────────────
catalog_tools = [
    search_catalog,
    get_product_by_id,
    get_alternatives,
]