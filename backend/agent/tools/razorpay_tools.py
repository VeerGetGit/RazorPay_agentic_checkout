# backend/agent/tools/razorpay_tools.py

from langchain_core.tools import tool
from db.database import SessionLocal
from db.models import Order
import razorpay
import hashlib
import json
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

# ── Razorpay Client ────────────────────────────────────────────────────────
razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)


def _generate_idempotency_key(
    session_id: str,
    cart: list,
    amount: float
) -> str:
    """
    Generates a unique idempotency key per order attempt.
    Same session + same cart + same minute = same key.
    Prevents duplicate Razorpay orders on double-tap.
    """
    cart_str   = json.dumps(cart, sort_keys=True)
    minute_str = datetime.utcnow().strftime("%Y%m%d%H%M")
    raw        = f"{session_id}_{cart_str}_{amount}_{minute_str}"
    return hashlib.md5(raw.encode()).hexdigest()


@tool
def create_razorpay_order(
    session_id: str,
    amount:     float,
    cart:       str,
) -> str:
    """
    Creates a Razorpay order in test mode.
    Uses idempotency key to prevent duplicate charges.
    Stores order in local DB.

    Args:
        session_id: current session ID
        amount:     total amount in rupees
        cart:       JSON string of cart items
    """
    db = SessionLocal()
    try:
        cart_items       = json.loads(cart)
        idempotency_key  = _generate_idempotency_key(
                            session_id, cart_items, amount)

        # Check if order already exists (duplicate tap protection)
        existing = db.query(Order).filter_by(
            idempotency_key=idempotency_key
        ).first()

        if existing:
            logger.warning(
                f"⚠️ Duplicate order detected for session {session_id[:8]}..."
            )
            return json.dumps({
                "status":           "duplicate",
                "razorpay_order_id": existing.razorpay_order_id,
                "amount":           existing.amount,
                "message":          "Order already created. Returning existing order.",
            })

        # Create Razorpay order
        razorpay_response = razorpay_client.order.create({
            "amount":   int(amount * 100),  # Razorpay uses paise
            "currency": "INR",
            "receipt":  idempotency_key,
            "notes":    {
                "session_id": session_id,
                "items":      cart[:200],  # truncate for Razorpay notes limit
            }
        })

        razorpay_order_id = razorpay_response["id"]

        # Save to local DB
        order = Order(
            session_id        = session_id,
            razorpay_order_id = razorpay_order_id,
            amount            = amount,
            status            = "pending",
            idempotency_key   = idempotency_key,
            items             = cart,
        )
        db.add(order)
        db.commit()

        logger.info(
            f"✅ Razorpay order created: {razorpay_order_id} "
            f"₹{amount:,.0f}"
        )

        return json.dumps({
            "status":            "created",
            "razorpay_order_id": razorpay_order_id,
            "amount":            amount,
            "currency":          "INR",
            "idempotency_key":   idempotency_key,
        })

    except Exception as e:
        logger.error(f"❌ Razorpay order creation failed: {e}")
        return json.dumps({
            "status":  "failed",
            "error":   str(e),
            "message": "Payment gateway error. Please try again.",
        })
    finally:
        db.close()


@tool
def verify_payment(razorpay_order_id: str) -> str:
    """
    Verifies payment status with Razorpay API.
    Called after user completes payment on frontend.

    Args:
        razorpay_order_id: the Razorpay order ID to verify
    """
    db = SessionLocal()
    try:
        # Fetch from Razorpay
        payments = razorpay_client.order.payments(razorpay_order_id)

        if not payments or not payments.get("items"):
            return json.dumps({
                "status":  "pending",
                "message": "Payment not yet completed.",
            })

        latest_payment = payments["items"][0]
        payment_status = latest_payment.get("status", "pending")

        # Update local DB
        order = db.query(Order).filter_by(
            razorpay_order_id=razorpay_order_id
        ).first()

        if order:
            order.status     = payment_status
            order.updated_at = datetime.utcnow()
            db.commit()

        logger.info(
            f"💳 Payment verified: {razorpay_order_id} → {payment_status}"
        )

        return json.dumps({
            "status":            payment_status,
            "razorpay_order_id": razorpay_order_id,
            "amount":            latest_payment.get("amount", 0) / 100,
            "method":            latest_payment.get("method", "unknown"),
        })

    except Exception as e:
        logger.error(f"❌ Payment verification failed: {e}")
        return json.dumps({
            "status":  "error",
            "error":   str(e),
            "message": "Could not verify payment. Please try again.",
        })
    finally:
        db.close()


@tool
def get_order_status(session_id: str) -> str:
    """
    Gets the latest order status for a session.
    Called when user asks 'what is my order status?'

    Args:
        session_id: current session ID
    """
    db = SessionLocal()
    try:
        orders = db.query(Order).filter_by(
            session_id=session_id
        ).order_by(Order.created_at.desc()).limit(3).all()

        if not orders:
            return "No orders found for this session."

        result = []
        for o in orders:
            result.append({
                "order_id":  o.razorpay_order_id or o.id,
                "amount":    o.amount,
                "status":    o.status,
                "created":   o.created_at.isoformat(),
                "items":     json.loads(o.items) if o.items else [],
            })

        return json.dumps(result)

    except Exception as e:
        logger.error(f"❌ Get order status error: {e}")
        return "Error fetching order status."
    finally:
        db.close()


# ── Tools list for LangChain ───────────────────────────────────────────────
razorpay_tools = [
    create_razorpay_order,
    verify_payment,
    get_order_status,
]