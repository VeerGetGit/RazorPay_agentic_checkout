# backend/agent/nodes/payment_node.py

from agent.state import AgentState
from agent.tools.razorpay_tools import create_razorpay_order
import json
import logging

logger = logging.getLogger(__name__)


def payment_node(state: AgentState) -> AgentState:
    """
    Executes the actual payment via Razorpay API.
    Only reached after:
    - spend_guard approved the amount
    - action_guard confirmed user consent

    Uses idempotency key to prevent duplicate charges.

    On success:
    - Sets payment_status = "success"
    - Sets razorpay_order_id
    - Updates spent_so_far
    - Routes to audit_logger

    On failure:
    - Sets payment_failed = True
    - Sets failure_reason
    - Routes to recovery_node
    """

    logger.info(
        f"💳 Payment node executing: "
        f"Rs.{state['payment_amount']:,.0f}"
    )

    try:
        # ── Create Razorpay order ──────────────────────────────────────────
        result_json = create_razorpay_order.invoke({
            "session_id": state["session_id"],
            "amount":     state["payment_amount"],
            "cart":       json.dumps(state["cart"]),
        })

        result = json.loads(result_json)

        # ── Handle duplicate order ─────────────────────────────────────────
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
                    f"You already have an order for this amount. "
                    f"Order ID: {result.get('razorpay_order_id')}. "
                    f"Please complete the payment."
                ),
                "audit_log": state["audit_log"] + [audit_entry],
            }

        # ── Handle successful order creation ───────────────────────────────
        if result["status"] == "created":
            razorpay_order_id = result["razorpay_order_id"]
            amount            = result["amount"]

            logger.info(f"✅ Razorpay order created: {razorpay_order_id}")

            audit_entry = {
                "node":      "payment_node",
                "action":    f"order created — Rs.{amount:,.0f}",
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
                "spent_so_far":      state["spent_so_far"] + amount,
                "remaining_limit":   state["spend_limit"] - (
                                        state["spent_so_far"] + amount
                                     ),
                "final_response":    (
                    f"Payment successful! 🎉\n\n"
                    f"Order ID: {razorpay_order_id}\n"
                    f"Amount:   Rs.{amount:,.0f}\n\n"
                    f"Your order has been placed successfully."
                ),
                "audit_log": state["audit_log"] + [audit_entry],
            }

        # ── Handle failed order creation ───────────────────────────────────
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