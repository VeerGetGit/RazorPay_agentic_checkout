# backend/api/orders.py

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Order
from db.session_store import verify_ownership
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/orders/{session_id}")
async def get_orders(
    session_id:      str,
    x_session_token: str = Header(...),
    db:              Session = Depends(get_db),
):
    """
    Returns all orders for a session.
    Session ownership verified.
    """

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
                "message": "You don't have access to this session's orders",
            }
        )

    orders = db.query(Order).filter_by(
        session_id = session_id
    ).order_by(Order.created_at.desc()).all()

    return {
        "session_id": session_id,
        "count":      len(orders),
        "orders": [
            {
                "id":                 order.id,
                "razorpay_order_id":  order.razorpay_order_id,
                "amount":             order.amount,
                "currency":           order.currency,
                "status":             order.status,
                "items":              json.loads(order.items) if order.items else [],
                "created_at":         order.created_at.isoformat(),
            }
            for order in orders
        ]
    }