# backend/agent/nodes/payment_node.py

from agent.state import AgentState
from agent.tools.razorpay_tools import create_razorpay_order
import json
import logging

logger = logging.getLogger(__name__)


def payment_node(state: AgentState) -> AgentState:
    """
    Executes the actual payment via Razorpay API.
    Only reached after spend_guard and action_guard approved.
    """

    logger.info(f"💳 Payment node: ₹{state['payment_amount']:,.0f}")

    try:
        result_json = create_razorpay_order.invoke({
            "session_id": state["session_id"],
            "amount":     state["payment_amount"],
            "cart":       json.dumps(state["cart"]),
        })

        result = json.loads(result_json)

        # ── Duplicate order ────────────────────────────────────────────────
        if result["status"] == "duplicate":
            logger.warning("⚠️ Duplicate order detected")

            audit_entry = {
                "node":      "payment_node",
                "action":    "duplicate order returned",
                "detail":    f"Existing order: {result.get('razorpay_order_id')}",
                "status":    "success",
                "timestamp": _now(),
            }

            return {
                **state,
                "payment_status":    "success",
                "razorpay_order_id": result.get("razorpay_order_id"),
                "payment_failed":    False,
                "final_response":    (
                    f"Duplicate order detected. "
                    f"You already placed this order less than 60 seconds ago."
                ),
                "audit_log": state["audit_log"] + [audit_entry],
            }

        # ── Success ────────────────────────────────────────────────────────
        if result["status"] == "created":
            razorpay_order_id = result["razorpay_order_id"]
            amount            = result["amount"]

            # Update spent_so_far in DB
            from db.session_store import update_spent
            from db.database import SessionLocal
            db = SessionLocal()
            try:
                update_spent(state["session_id"], amount, db)
            except Exception as e:
                logger.error(f"❌ Spend update error: {e}")
            finally:
                db.close()

            new_spent = state["spent_so_far"] + amount

            logger.info(f"✅ Order created: {razorpay_order_id} | ₹{amount:,.0f}")

            audit_entry = {
                "node":      "payment_node",
                "action":    f"order created — ₹{amount:,.0f}",
                "detail":    f"Razorpay Order ID: {razorpay_order_id}",
                "status":    "success",
                "timestamp": _now(),
            }

            return {
                **state,
                "payment_status":    "success",
                "razorpay_order_id": razorpay_order_id,
                "payment_amount":    amount,
                "payment_failed":    False,
                "spent_so_far":      new_spent,
                "remaining_limit":   state["spend_limit"] - new_spent,
                "cart":              [],      # clear cart after payment
                "cart_total":        0.0,     # reset cart total
                "final_response": (
                    f"Payment successful! 🎉\n\n"
                    f"Order ID: {razorpay_order_id}\n"
                    f"Amount:   Rs.{amount:,.0f}\n\n"
                    f"Your order has been placed successfully."
                ),
                "audit_log": state["audit_log"] + [audit_entry],
            }

        # ── Failed ─────────────────────────────────────────────────────────
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"❌ Payment failed: {error}")

            audit_entry = {
                "node":      "payment_node",
                "action":    "payment failed",
                "detail":    error,
                "status":    "failed",
                "timestamp": _now(),
            }

            return {
                **state,
                "payment_status": "failed",
                "payment_failed": True,
                "failure_reason": error,
                "retry_count":    state["retry_count"] + 1,
                "audit_log":      state["audit_log"] + [audit_entry],
            }

    except Exception as e:
        logger.error(f"❌ Payment node exception: {e}")

        audit_entry = {
            "node":      "payment_node",
            "action":    "exception",
            "detail":    str(e),
            "status":    "failed",
            "timestamp": _now(),
        }

        return {
            **state,
            "payment_status": "failed",
            "payment_failed": True,
            "failure_reason": str(e),
            "retry_count":    state["retry_count"] + 1,
            "audit_log":      state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()