# backend/health_check.py
# Run: python health_check.py
# Checks all imports and core functionality

import sys
import os
from dotenv import load_dotenv

load_dotenv('.env')

print("=" * 50)
print("RAZORPAY AGENTIC CHECKOUT — HEALTH CHECK")
print("=" * 50)

errors = []
passed = []

# ── Check 1: Environment Variables ────────────────────────────────────────
print("\n📋 Checking environment variables...")
required_env = [
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "GROQ_MODEL_MINI",
    "GROQ_MODEL_GUARD",
    "RAZORPAY_KEY_ID",
    "RAZORPAY_KEY_SECRET",
    "SPEND_LIMIT_DEFAULT",
    "SESSION_EXPIRY_MINUTES",
    "DATABASE_URL",
]
for key in required_env:
    val = os.getenv(key)
    if val:
        print(f"  ✅ {key} = {val[:10]}...")
        passed.append(key)
    else:
        print(f"  ❌ {key} = NOT SET")
        errors.append(f"Missing env: {key}")

# ── Check 2: Core imports ──────────────────────────────────────────────────
print("\n📦 Checking core imports...")
imports_to_check = [
    ("langgraph", "LangGraph"),
    ("langchain_groq", "LangChain Groq"),
    ("langchain_core", "LangChain Core"),
    ("fastapi", "FastAPI"),
    ("sqlalchemy", "SQLAlchemy"),
    ("razorpay", "Razorpay SDK"),
    ("groq", "Groq"),
    ("guardrails", "Guardrails AI"),
    ("dotenv", "Python Dotenv"),
    ("sse_starlette", "SSE Starlette"),
]
for module, name in imports_to_check:
    try:
        __import__(module)
        print(f"  ✅ {name}")
        passed.append(name)
    except ImportError as e:
        print(f"  ❌ {name}: {e}")
        errors.append(f"Missing module: {name}")

# ── Check 3: Database ──────────────────────────────────────────────────────
print("\n🗄️ Checking database...")
try:
    from db.database import init_db, SessionLocal
    from db.models import Product, Session, Order, AuditLog
    init_db()
    db = SessionLocal()
    product_count = db.query(Product).count()
    db.close()
    print(f"  ✅ Database connected")
    print(f"  ✅ Products in catalog: {product_count}")
    passed.append("Database")
except Exception as e:
    print(f"  ❌ Database error: {e}")
    errors.append(f"Database: {e}")

# ── Check 4: Seed data ─────────────────────────────────────────────────────
print("\n🌱 Checking seed data...")
try:
    from db.database import SessionLocal
    from db.models import Product
    db = SessionLocal()
    count = db.query(Product).count()
    db.close()
    if count == 0:
        print("  ⚠️  No products found — running seed...")
        from db.seed import seed_products
        seed_products()
        print("  ✅ Products seeded")
    else:
        print(f"  ✅ {count} products in catalog")
    passed.append("Seed data")
except Exception as e:
    print(f"  ❌ Seed error: {e}")
    errors.append(f"Seed: {e}")

# ── Check 5: LangGraph ─────────────────────────────────────────────────────
print("\n🤖 Checking LangGraph agent...")
try:
    from agent.graph import graph
    mermaid = graph.get_graph().draw_mermaid()
    node_count = mermaid.count("-->")
    print(f"  ✅ Graph compiled successfully")
    print(f"  ✅ {node_count} edges in graph")
    passed.append("LangGraph")
except Exception as e:
    print(f"  ❌ Graph error: {e}")
    errors.append(f"Graph: {e}")

# ── Check 6: Validators ────────────────────────────────────────────────────
print("\n🛡️ Checking validators...")
try:
    from validators.input_validators import validate_input
    from validators.output_validators import validate_output
    from validators.spend_validators import validate_spend
    print("  ✅ Input validators loaded")
    print("  ✅ Output validators loaded")
    print("  ✅ Spend validators loaded")
    passed.append("Validators")
except Exception as e:
    print(f"  ❌ Validators error: {e}")
    errors.append(f"Validators: {e}")

# ── Check 7: Rate limiter ──────────────────────────────────────────────────
print("\n⏱️ Checking rate limiter...")
try:
    from rate_limiter.groq_limiter import groq_limiter
    status = groq_limiter.get_status()
    print(f"  ✅ Rate limiter active")
    print(f"  ✅ RPM limit: {status['requests_limit']}")
    print(f"  ✅ TPM limit: {status['tokens_limit']}")
    passed.append("Rate limiter")
except Exception as e:
    print(f"  ❌ Rate limiter error: {e}")
    errors.append(f"Rate limiter: {e}")

# ── Check 8: Groq API ──────────────────────────────────────────────────────
print("\n🔑 Checking Groq API connection...")
try:
    from agent.llm import check_llm_health
    healthy = check_llm_health()
    if healthy:
        print("  ✅ Groq API reachable")
        passed.append("Groq API")
    else:
        print("  ⚠️  Groq API returned unexpected response")
except Exception as e:
    print(f"  ❌ Groq API error: {e}")
    errors.append(f"Groq API: {e}")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"✅ Passed: {len(passed)}")
print(f"❌ Failed: {len(errors)}")

if errors:
    print("\nErrors to fix:")
    for e in errors:
        print(f"  • {e}")
else:
    print("\n🎉 All checks passed! Ready to run.")
    print("\nNext step:")
    print("  uvicorn main:app --reload")