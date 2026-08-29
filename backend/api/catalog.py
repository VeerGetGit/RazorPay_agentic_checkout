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
            "merchant":   "Razorpay Demo Store",
            "currency":   "INR",
            "categories": categories,
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