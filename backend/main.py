# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from db.database import init_db, start_expiry_job
from db.seed import seed_products
from db.session_store import create_session
from rate_limiter.middleware import rate_limit_middleware
from agent.llm import check_llm_health
from api.chat import router as chat_router
from api.audit import router as audit_router
from api.orders import router as orders_router
from api.stream import router as stream_router
from sqlalchemy.orm import Session
from db.database import SessionLocal
import logging
import os
from dotenv import load_dotenv

load_dotenv('.env')

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


# ── Startup / Shutdown ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""

    # ── Startup ────────────────────────────────────────────────────────────
    logger.info("🚀 Starting Razorpay Agentic Checkout...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # Seed catalog
    seed_products()
    logger.info("✅ Product catalog seeded")

    # Start session expiry background job
    start_expiry_job()
    logger.info("✅ Session expiry job started")

    # Check Groq API
    healthy = check_llm_health()
    if healthy:
        logger.info("✅ Groq API connected")
    else:
        logger.warning("⚠️  Groq API health check failed")

    logger.info("✅ Server ready")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("👋 Shutting down...")


# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Razorpay Agentic Checkout",
    description = "AI agent for conversational UPI checkout",
    version     = "1.0.0",
    lifespan    = lifespan,
)


# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://localhost:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Rate Limit Middleware ──────────────────────────────────────────────────
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(chat_router,   prefix="/api", tags=["Chat"])
app.include_router(audit_router,  prefix="/api", tags=["Audit"])
app.include_router(orders_router, prefix="/api", tags=["Orders"])
app.include_router(stream_router, prefix="/api", tags=["Stream"])


# ── Session endpoints ──────────────────────────────────────────────────────
@app.post("/api/session/create")
async def create_new_session(db: Session = None):
    """Creates a new session. Called by frontend on app load."""
    if db is None:
        db = SessionLocal()
    try:
        session = create_session(db)
        logger.info(f"✅ New session created: {session['session_id'][:8]}...")
        return session
    finally:
        db.close()


# ── Health endpoint ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Quick health check endpoint."""
    return {
        "status":  "ok",
        "version": "1.0.0",
        "service": "razorpay-agentic-checkout",
    }


# ── Root ───────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Razorpay Agentic Checkout API",
        "docs":    "/docs",
        "health":  "/health",
    }