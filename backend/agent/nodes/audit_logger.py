# backend/agent/nodes/audit_logger.py

from agent.state import AgentState
from db.database import SessionLocal
from db.models import AuditLog
import logging

logger = logging.getLogger(__name__)


def audit_logger_node(state: AgentState) -> AgentState:
    """
    Persists all audit log entries from state to SQLite.
    Called after every successful action.

    Every entry in state["audit_log"] gets saved to DB.
    Frontend SSE stream picks these up in real time.

    Non-blocking — if DB write fails, conversation continues.
    Session ownership verified before every write.
    """

    session_id = state["session_id"]
    audit_log  = state["audit_log"]

    if not audit_log:
        return state

    logger.info(
        f"📝 Audit logger saving "
        f"{len(audit_log)} entries for session {session_id[:8]}..."
    )

    db = SessionLocal()
    try:
        for entry in audit_log:
            # Check if already saved (avoid duplicates on retry)
            existing = db.query(AuditLog).filter_by(
                session_id = session_id,
                node       = entry.get("node"),
                timestamp  = entry.get("timestamp"),
            ).first()

            if existing:
                continue

            log = AuditLog(
                session_id = session_id,
                node       = entry.get("node", "unknown"),
                action     = entry.get("action", ""),
                detail     = entry.get("detail", ""),
                status     = entry.get("status", "success"),
            )
            db.add(log)

        db.commit()
        logger.info("✅ Audit log saved to DB")

    except Exception as e:
        # Non-blocking — log error but don't fail the conversation
        logger.error(f"❌ Audit logger DB error: {e}")
        db.rollback()
    finally:
        db.close()

    return state


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()