# backend/api/stream.py

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from db.database import get_db, SessionLocal
from db.models import AuditLog
from db.session_store import verify_ownership
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stream/{session_id}")
async def stream_audit(
    session_id:      str,
    x_session_token: str = Header(...),
    db:              Session = Depends(get_db),
):
    """
    SSE endpoint — streams audit log entries in real time.
    Frontend connects once and receives events as agent acts.

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
            detail      = "Access denied"
        )

    async def event_generator():
        last_id    = 0
        retry_count = 0
        max_retries = 300  # 5 minutes at 1 second intervals

        while retry_count < max_retries:
            try:
                stream_db = SessionLocal()

                # Fetch new entries since last_id
                new_logs = stream_db.query(AuditLog).filter(
                    AuditLog.session_id == session_id,
                    AuditLog.id > last_id
                ).order_by(AuditLog.timestamp.asc()).all()

                for log in new_logs:
                    data = {
                        "id":        log.id,
                        "node":      log.node,
                        "action":    log.action,
                        "detail":    log.detail,
                        "status":    log.status,
                        "timestamp": log.timestamp.isoformat(),
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    last_id = log.id

                stream_db.close()

            except Exception as e:
                logger.error(f"❌ SSE stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            await asyncio.sleep(1)  # poll every 1 second
            retry_count += 1

        yield f"data: {json.dumps({'event': 'stream_ended'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type = "text/event-stream",
        headers    = {
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        }
    )