# backend/api/catalog.py

from fastapi import APIRouter
from db.database import SessionLocal
from db.models import Product

router = APIRouter()

@router.get("/api/catalog")
def get_catalog():
    """Machine-readable catalog for AI buyers."""
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        categories = {}
        for p in products:
            if p.category not in categories:
                categories[p.category] = []
            categories[p.category].append({
                "id":          p.id,
                "name":        p.name,
                "price":       p.price,
                "stock":       p.stock,
                "available":   p.stock > 0,
                "description": p.description,
            })
        return {
            "merchant":       "Razorpay Demo Store",
            "currency":       "INR",
            "categories":     categories,
            "total_products": len(products),
        }
    finally:
        db.close()


@router.get("/api/catalog/{category}")
def get_category(category: str):
    """Get products by category."""
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.category == category
        ).all()
        return {
            "category": category,
            "products": [
                {
                    "id":          p.id,
                    "name":        p.name,
                    "price":       p.price,
                    "stock":       p.stock,
                    "available":   p.stock > 0,
                    "description": p.description,
                }
                for p in products
            ]
        }
    finally:
        db.close()


@router.get("/api/catalog/agent/discover")
def agent_discover():
    """
    Structured catalog for AI buyers.
    Compatible with ACP/x402/NPCI-UAP agent commerce protocols.
    An AI buyer can read this endpoint to discover products and transact.
    """
    db = SessionLocal()
    try:
        products = db.query(Product).filter(
            Product.stock > 0
        ).all()
        return {
            "protocol":     "razorpay-agentic-v1",
            "merchant_id":  "demo-store",
            "currency":     "INR",
            "spend_limit":  100000,
            "price_integrity": {
                                "source":             "database",
                                "llm_controls_price": False,
                                "authoritative":      "backend-enforced",
                                "note":               "All prices enforced server-side from catalog DB. LLM never sets or modifies price.",
                               },
            "endpoints": {
                "session":  "POST /api/session/create",
                "checkout": "POST /api/chat",
                "catalog":  "GET /api/catalog",
                "orders":   "GET /api/orders",
            },
            "auth": {
                "type":   "session-token",
                "header": "X-Session-Token",
            },
            "capabilities": [
                "natural-language-purchase",
                "spend-limit-enforcement",
                "audit-trail",
                "multi-item-cart",
                "budget-aware-suggestions",
                "upsell-recommendations",
                "out-of-stock-handling",
            ],
            "how_to_buy": [
                "1. POST /api/session/create → get session_id + token",
                "2. POST /api/chat with message='add {product} to cart'",
                "3. POST /api/chat with message='buy it'",
                "4. Check order_data in response for confirmation",
            ],
            "products": [
                {
                    "id":          str(p.id),
                    "name":        p.name,
                    "price":       p.price,
                    "currency":    "INR",
                    "category":    p.category,
                    "available":   True,
                    "stock":       p.stock,
                    "description": p.description,
                    "buy_intent":  f"add {p.name} to cart",
                }
                for p in products
            ]
        }
    finally:
        db.close()