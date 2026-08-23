# backend/db/seed.py

from db.database import SessionLocal, init_db
from db.models import Product
import logging

logger = logging.getLogger(__name__)

PRODUCTS = [

    # ── Category 1: Phones (5 products) ───────────────────────────────────
    {
        "name":        "iPhone 15",
        "description": "Apple iPhone 15 with 48MP camera, A16 Bionic chip, 128GB storage",
        "price":       79999.0,
        "category":    "phones",
        "stock":       10,
    },
    {
        "name":        "Samsung Galaxy S24",
        "description": "Samsung Galaxy S24 with Snapdragon 8 Gen 3, 256GB, 50MP camera",
        "price":       74999.0,
        "category":    "phones",
        "stock":       8,
    },
    {
        "name":        "Google Pixel 8",
        "description": "Google Pixel 8 with Tensor G3 chip, 7 years of updates, 128GB",
        "price":       62999.0,
        "category":    "phones",
        "stock":       5,
    },
    {
        "name":        "OnePlus 12",
        "description": "OnePlus 12 with Snapdragon 8 Gen 3, 256GB, 100W fast charging",
        "price":       64999.0,
        "category":    "phones",
        "stock":       12,
    },
    {
        "name":        "Redmi Note 13 Pro",
        "description": "Redmi Note 13 Pro with 200MP camera, 5000mAh battery, 256GB",
        "price":       26999.0,
        "category":    "phones",
        "stock":       20,
    },

    # ── Category 2: Shoes (5 products) ────────────────────────────────────
    {
        "name":        "Nike Air Max 270",
        "description": "Nike Air Max 270 running shoes with full-length Air unit, size 8-11",
        "price":       12995.0,
        "category":    "shoes",
        "stock":       15,
    },
    {
        "name":        "Adidas Ultraboost 23",
        "description": "Adidas Ultraboost 23 with Boost midsole, Primeknit upper",
        "price":       16999.0,
        "category":    "shoes",
        "stock":       8,
    },
    {
        "name":        "Puma RS-X",
        "description": "Puma RS-X retro running shoes with chunky sole, multiple colorways",
        "price":       8999.0,
        "category":    "shoes",
        "stock":       0,   # ← out of stock — tests failure scenario 3
    },
    {
        "name":        "New Balance 574",
        "description": "New Balance 574 classic sneaker with ENCAP midsole technology",
        "price":       7499.0,
        "category":    "shoes",
        "stock":       18,
    },
    {
        "name":        "Skechers Go Walk 6",
        "description": "Skechers Go Walk 6 with Air Cooled Goga Mat insole, slip-on style",
        "price":       4999.0,
        "category":    "shoes",
        "stock":       25,
    },

    # ── Category 3: Bags (5 products) ─────────────────────────────────────
    {
        "name":        "Safari Trolley Bag 28 inch",
        "description": "Safari hard shell trolley 28 inch, 4 spinner wheels, TSA lock",
        "price":       4599.0,
        "category":    "bags",
        "stock":       10,
    },
    {
        "name":        "American Tourister Backpack",
        "description": "American Tourister 32L laptop backpack with USB charging port",
        "price":       3299.0,
        "category":    "bags",
        "stock":       14,
    },
    {
        "name":        "Wildcraft Trailblazer 45L",
        "description": "Wildcraft 45L hiking backpack with rain cover, multiple compartments",
        "price":       2799.0,
        "category":    "bags",
        "stock":       7,
    },
    {
        "name":        "Lavie Women Tote Bag",
        "description": "Lavie large tote bag with zip closure, faux leather, multiple pockets",
        "price":       1999.0,
        "category":    "bags",
        "stock":       20,
    },
    {
        "name":        "Skybags Chest Bag",
        "description": "Skybags crossbody chest bag with adjustable strap, 5L capacity",
        "price":       999.0,
        "category":    "bags",
        "stock":       30,
    },

    # ── Category 4: Watches (5 products) ──────────────────────────────────
    {
        "name":        "Apple Watch Series 9",
        "description": "Apple Watch Series 9 with S9 chip, Always-On display, 41mm",
        "price":       41900.0,
        "category":    "watches",
        "stock":       6,
    },
    {
        "name":        "Samsung Galaxy Watch 6",
        "description": "Samsung Galaxy Watch 6 with health tracking, 44mm, Wear OS",
        "price":       29999.0,
        "category":    "watches",
        "stock":       9,
    },
    {
        "name":        "Fastrack Reflex Beat",
        "description": "Fastrack Reflex Beat smartwatch with SpO2, heart rate, 7 day battery",
        "price":       2995.0,
        "category":    "watches",
        "stock":       40,
    },
    {
        "name":        "Titan Edge Ceramic",
        "description": "Titan Edge Ceramic ultra-slim analog watch with sapphire crystal",
        "price":       15995.0,
        "category":    "watches",
        "stock":       5,
    },
    {
        "name":        "Noise ColorFit Pro 5",
        "description": "Noise ColorFit Pro 5 with AMOLED display, Bluetooth calling, 7 day battery",
        "price":       4499.0,
        "category":    "watches",
        "stock":       50,
    },
]


def seed_products():
    """
    Seeds all 20 products into DB.
    Skips if products already exist (safe to run multiple times).
    """
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(Product).count()
        if existing > 0:
            logger.info(f"⏭️  Skipping seed — {existing} products already exist")
            return

        # Insert all products
        for p in PRODUCTS:
            product = Product(**p)
            db.add(product)

        db.commit()
        logger.info(f"✅ Seeded {len(PRODUCTS)} products across 4 categories")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Run directly: python -m db.seed
    logging.basicConfig(level=logging.INFO)
    init_db()
    seed_products()
    print("✅ Database seeded successfully")