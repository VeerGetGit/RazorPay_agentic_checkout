# backend/db/session_store.py

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from db.models import Session as SessionModel
import secrets
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SESSION_EXPIRY_MINUTES = int(os.getenv("SESSION_EXPIRY_MINUTES", 30))
SPEND_LIMIT_DEFAULT    = float(os.getenv("SPEND_LIMIT_DEFAULT", 100000.0))


# ── Create Session ─────────────────────────────────────────────────────────
def create_session(db: Session) -> dict:
    """
    Creates a new session with:
    - Secure random token (64 hex chars)
    - Spend limit set ONCE from .env (never reset)
    - Expiry set to now + 30 minutes

    Returns token to frontend.
    Frontend stores in React memory ONLY — not localStorage.
    """
    token      = secrets.token_hex(32)   # 64 char secure random string
    now        = datetime.now(timezone.utc).replace(tzinfo=None)
    expires_at = now + timedelta(minutes=SESSION_EXPIRY_MINUTES)

    session = SessionModel(
        token        = token,
        spend_limit  = SPEND_LIMIT_DEFAULT,
        spent_so_far = 0.0,
        last_active  = now,
        expires_at   = expires_at,
        created_at   = now,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(f"✅ Session created: {session.id[:8]}...")

    return {
        "session_id":   session.id,
        "token":        token,
        "spend_limit":  session.spend_limit,
        "spent_so_far": session.spent_so_far,
        "expires_at":   expires_at.isoformat(),
    }


# ── Validate Session ───────────────────────────────────────────────────────
def validate_session(token: str, db: Session) -> dict:
    """
    Called on every API request.
    Checks:
    1. Token exists in DB
    2. Session not expired
    3. Resets idle timer (last_active + 30 min)

    Returns session data if valid.
    Returns error dict if invalid.
    """
    session = db.query(SessionModel).filter_by(token=token).first()

    # Token not found
    if not session:
        logger.warning("❌ Session not found for token")
        return {
            "valid":  False,
            "reason": "Session not found"
        }

    # Session expired
    if session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        logger.warning(f"❌ Session expired: {session.id[:8]}...")
        return {
            "valid":  False,
            "reason": "Session expired"
        }

    # Valid — reset idle timer
    session.last_active = datetime.now(timezone.utc).replace(tzinfo=None)
    session.expires_at  = (datetime.now(timezone.utc) + timedelta(
                            minutes=SESSION_EXPIRY_MINUTES)).replace(tzinfo=None)
    db.commit()

    return {
        "valid":        True,
        "session_id":   session.id,
        "token":        session.token,
        "spend_limit":  session.spend_limit,
        "spent_so_far": session.spent_so_far,
        "expires_at":   session.expires_at.isoformat(),
    }


# ── Verify Session Ownership ───────────────────────────────────────────────
def verify_ownership(session_id: str, token: str, db: Session) -> bool:
    """
    Checks that the token belongs to this session_id.
    Used in /audit and /orders routes.
    Prevents user A reading user B's data.
    """
    session = db.query(SessionModel).filter_by(
        id    = session_id,
        token = token
    ).first()

    return session is not None


# ── Update Spent Amount ────────────────────────────────────────────────────
def update_spent(session_id: str, amount: float, db: Session) -> dict:
    """
    Called after successful payment.
    Adds amount to spent_so_far.
    Returns updated spend status.
    """
    session = db.query(SessionModel).filter_by(id=session_id).first()

    if not session:
        return {"success": False, "reason": "Session not found"}

    session.spent_so_far += amount
    db.commit()

    logger.info(
        f"💰 Spend updated: {session.id[:8]}... "
        f"₹{session.spent_so_far} / ₹{session.spend_limit}"
    )

    return {
        "success":      True,
        "spent_so_far": session.spent_so_far,
        "spend_limit":  session.spend_limit,
        "remaining":    session.spend_limit - session.spent_so_far,
    }


# ── Get Session by ID ──────────────────────────────────────────────────────
def get_session(session_id: str, db: Session) -> dict | None:
    """
    Returns session data by ID.
    Used by spend_guard to check current spend.
    """
    session = db.query(SessionModel).filter_by(id=session_id).first()

    if not session:
        return None

    return {
        "session_id":   session.id,
        "spend_limit":  session.spend_limit,
        "spent_so_far": session.spent_so_far,
        "remaining":    session.spend_limit - session.spent_so_far,
        "expires_at":   session.expires_at.isoformat(),
    }