# backend/api/audit.py

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import AuditLog
from db.session_store import verify_ownership
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/audit/{session_id}")
async def get_audit_log(
    session_id:      str,
    x_session_token: str = Header(...),
    db:              Session = Depends(get_db),
):
    """
    Returns audit log for a session.
    Session ownership verified — user A cannot see user B's logs.

    Headers required:
        X-Session-Token: <token>
    """

    # Verify ownership
    owns = verify_ownership(
        session_id = session_id,
        token      = x_session_token,
        db         = db,
    )

    if not owns:
        raise HTTPException(
            status_code = 403,
            detail      = {
                "error":   "access_denied",
                "message": "You don't have access to this session's audit log",
            }
        )

    # Fetch audit logs
    logs = db.query(AuditLog).filter_by(
        session_id = session_id
    ).order_by(AuditLog.timestamp.asc()).all()

    return {
        "session_id": session_id,
        "count":      len(logs),
        "logs": [
            {
                "id":        log.id,
                "node":      log.node,
                "action":    log.action,
                "detail":    log.detail,
                "status":    log.status,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in logs
        ]
    }