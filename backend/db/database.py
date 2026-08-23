# backend/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base
from datetime import datetime, timezone
import threading
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Database Connection ────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "./db/razorpay_agent.db")

engine = create_engine(
    f"sqlite:///{DATABASE_URL}",
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ── Create All Tables ──────────────────────────────────────────────────────
def init_db():
    """
    Creates all tables if they don't exist.
    Called once on FastAPI startup.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")


# ── Dependency for FastAPI routes ──────────────────────────────────────────
def get_db():
    """
    FastAPI dependency — provides a DB session per request.
    Always closes the session after the request finishes.

    Usage in routes:
        def my_route(db = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Background Session Expiry Job ──────────────────────────────────────────
def _expiry_job():
    """
    Runs every 60 seconds.
    Deletes sessions where expires_at < now.
    Cascade delete removes audit_logs and orders too.
    """
    while True:
        try:
            db = SessionLocal()
            now = datetime.now(timezone.utc)

            # Find expired sessions
            from db.models import Session as SessionModel
            expired = db.query(SessionModel).filter(
                SessionModel.expires_at < now
            ).all()

            count = len(expired)

            for session in expired:
                db.delete(session)

            db.commit()

            if count > 0:
                logger.info(f"🧹 Cleaned up {count} expired session(s)")

        except Exception as e:
            logger.error(f"❌ Session expiry job error: {e}")
        finally:
            db.close()

        # Wait 60 seconds before next run
        threading.Event().wait(60)


def start_expiry_job():
    """
    Starts the background expiry job in a daemon thread.
    Called once on FastAPI startup.
    Daemon thread = dies automatically when app stops.
    """
    thread = threading.Thread(
        target=_expiry_job,
        daemon=True,
        name="session-expiry-job"
    )
    thread.start()
    logger.info("✅ Session expiry background job started")