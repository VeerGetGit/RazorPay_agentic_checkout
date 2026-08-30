# backend/api/chat.py

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db
from db.session_store import validate_session, get_session
from agent.graph import graph
from agent.state import get_initial_state
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cart store (persists during server session)
_cart_store = {}

# ── Request / Response models ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message:    str
    session_id: str


class ChatResponse(BaseModel):
    response:         str
    session_id:       str
    intent:           str
    cart:             list
    cart_total:       float
    spend_limit:      float
    spent_so_far:     float
    remaining_limit:  float
    payment_status:   str
    awaiting_consent: bool
    audit_log:        list
    order_data:       dict = {}


# ── POST /chat ─────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request:         ChatRequest,
    x_session_token: str = Header(...),
    db:              Session = Depends(get_db),
):
    """
    Main chat endpoint.
    Every message passes through the full LangGraph agent.

    Headers required:
        X-Session-Token: <token from /session/create>

    Flow:
    1. Validate session token
    2. Check session not expired
    3. Load current session state (spend limit, spent so far)
    4. Run LangGraph agent
    5. Return response + updated state
    """

    # ── Step 1: Validate session ───────────────────────────────────────────
    session_check = validate_session(
        token = x_session_token,
        db    = db,
    )

    if not session_check["valid"]:
        raise HTTPException(
            status_code = 410,
            detail      = {
                "error":   "session_expired",
                "message": session_check["reason"],
            }
        )

    # Verify session_id matches token
    if session_check["session_id"] != request.session_id:
        raise HTTPException(
            status_code = 403,
            detail      = {
                "error":   "session_mismatch",
                "message": "Session ID does not match token",
            }
        )

    # ── Step 2: Build initial state ────────────────────────────────────────
    initial_state = get_initial_state(
        session_id    = request.session_id,
        session_token = x_session_token,
        spend_limit   = session_check["spend_limit"],
        spent_so_far  = session_check["spent_so_far"],
        user_message  = request.message,
    )
    # Load saved cart for this session
    saved_cart = _cart_store.get(request.session_id, [])
    initial_state["cart"] = saved_cart
    initial_state["cart_total"] = sum(item["total"] for item in saved_cart)

    logger.info(
        f"💬 Chat request: session={request.session_id[:8]}... "
        f"message='{request.message[:50]}'"
    )

    # ── Step 3: Run LangGraph agent ────────────────────────────────────────
    try:
        result = graph.invoke(initial_state)

        # Save cart back to memory
        if result.get("payment_status") == "success":
            _cart_store[request.session_id] = []  # clear cart after payment
        else:
            _cart_store[request.session_id] = result.get("cart", [])

        logger.info(
            f"✅ Chat response: intent={result.get('intent')} "
            f"payment_status={result.get('payment_status')}"
        )

        # Save audit log to DB
        from db.database import SessionLocal as AuditDB
        from db.models import AuditLog
        audit_entries = result.get("audit_log", [])
        if audit_entries:
            audit_db = AuditDB()
            try:
                for entry in audit_entries:
                    log = AuditLog(
                        session_id = request.session_id,
                        node       = entry.get("node", "unknown"),
                        action     = entry.get("action", ""),
                        detail     = entry.get("detail", ""),
                        status     = entry.get("status", "success"),
                    )
                    audit_db.add(log)
                audit_db.commit()
            except Exception as e:
                logger.error(f"❌ Audit save error: {e}")
                audit_db.rollback()
            finally:
                audit_db.close()


                # Structured order data for AI buyers
        order_data = {}
        if result.get("payment_status") == "success":
            order_data = {
                "protocol":  "razorpay-agentic-v1",
                "status":    "success",
                "order_id":  result.get("razorpay_order_id", ""),
                "amount":    result.get("payment_amount", 0),
                "currency":  "INR",
                "merchant":  "demo-store",
                "items":     initial_state.get("cart", []),
            }

        return ChatResponse(
            response         = result.get("final_response", ""),
            session_id       = request.session_id,
            intent           = result.get("intent", "unknown"),
            cart             = result.get("cart", []),
            cart_total       = result.get("cart_total", 0.0),
            spend_limit      = result.get("spend_limit", 0.0),
            spent_so_far     = result.get("spent_so_far", 0.0),
            remaining_limit  = result.get("remaining_limit", 0.0),
            payment_status   = result.get("payment_status", "pending"),
            awaiting_consent = result.get("awaiting_consent", False),
            audit_log        = result.get("audit_log", []),
            order_data       = order_data,
        )

    except Exception as e:
        logger.error(f"❌ Chat error: {e}")
        raise HTTPException(
            status_code = 500,
            detail      = {
                "error":   "agent_error",
                "message": "Something went wrong. Please try again.",
            }
        )