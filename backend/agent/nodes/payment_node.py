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

            # ── Track merchant revenue analytics ───────────────────────
            try:
                from api.analytics import track_order
                # Use initial cart (before clearing)
                original_cart = state.get("cart", [])
                had_upsell    = len(original_cart) > 1
                upsell_item   = original_cart[1]["name"] if had_upsell else None
                upsell_amount  = original_cart[1]["total"] if had_upsell else 0.0
                track_order(
                    session_id  = state["session_id"],
                    amount      = amount,
                    items       = original_cart,   # ← use original not cleared
                    had_upsell  = had_upsell,
                    upsell_item = upsell_item,
                    upsell_amount = upsell_amount,
                )
            except Exception as e:
                logger.error(f"❌ Analytics error: {e}")

            # ── Post-payment budget suggestion ─────────────────────────
            remaining_after   = state["spend_limit"] - new_spent
            budget_suggestion = ""

            if 500 < remaining_after < state["spend_limit"]:
                try:
                    from db.database import SessionLocal as SDB
                    from db.models import Product as P
                    sdb       = SDB()
                    cart_cats = {item.get("category", "") for item in state["cart"]}
                    suggest   = sdb.query(P).filter(
                        P.price <= remaining_after,
                        P.stock > 0,
                        ~P.category.in_(cart_cats)
                    ).order_by(P.price.desc()).first()
                    sdb.close()

                    if suggest:
                        pct = (suggest.price / amount * 100)
                        budget_suggestion = (
                            f"\n\n💡 **Revenue Opportunity**\n"
                            f"You have ₹{remaining_after:,.0f} remaining.\n"
                            f"**{suggest.name}** at ₹{suggest.price:,.0f} "
                            f"complements your purchase.\n"
                            f"Adding it would increase order value by "
                            f"+{pct:.1f}%.\n"
                            f"Would you like to add it?"
                        )
                except Exception as e:
                    logger.error(f"❌ Suggestion error: {e}")

            return {
                **state,
                "payment_status":    "success",
                "razorpay_order_id": razorpay_order_id,
                "payment_amount":    amount,
                "payment_failed":    False,
                "spent_so_far":      new_spent,
                "remaining_limit":   state["spend_limit"] - new_spent,
                "cart":              [],
                "cart_total":        0.0,
                "final_response": (
                    f"Payment successful! 🎉\n\n"
                    f"Order ID: {razorpay_order_id}\n"
                    f"Amount:   Rs.{amount:,.0f}\n\n"
                    f"Your order has been placed successfully."
                    + budget_suggestion
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