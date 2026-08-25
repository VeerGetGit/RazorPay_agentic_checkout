# backend/agent/nodes/spend_guard.py

from agent.state import AgentState
from validators.spend_validators import validate_spend
import logging

logger = logging.getLogger(__name__)


def spend_guard_node(state: AgentState) -> AgentState:
    """
    Layer 2 Guardrail — enforces spend cap.

    Runs 4 checks:
    1. Cart not empty
    2. Amount validity (not zero/negative)
    3. Amount within remaining spend limit
    4. Not a duplicate order

    spend_limit is READ FROM DB SESSION — cannot be reset by user.
    Enforced at CODE level — not just in the prompt.

    If blocked:
    - Sets spend_blocked = True
    - Sets spend_block_reason
    - Graph routes to respond_node with explanation
    - Suggests cheaper alternatives

    If allowed:
    - Sets spend_blocked = False
    - Graph continues to action_guard
    """

    logger.info(
        f"💰 Spend guard checking: "
        f"Rs.{state['payment_amount']:,.0f} vs "
        f"limit Rs.{state['spend_limit']:,.0f}"
    )

    result = validate_spend(
        amount       = state["payment_amount"],
        spend_limit  = state["spend_limit"],
        spent_so_far = state["spent_so_far"],
        session_id   = state["session_id"],
        cart         = state["cart"],
    )

    if not result["passed"]:
        # ── Spend blocked ──────────────────────────────────────────────────
        logger.warning(f"🚫 Spend blocked: {result['reason']}")

        audit_entry = {
            "node":      "spend_guard",
            "action":    "blocked",
            "detail":    result["reason"],
            "status":    "blocked",
            "timestamp": _now(),
        }

        # Build helpful response
        remaining = state["spend_limit"] - state["spent_so_far"]
        block_response = (
            f"{result['reason']}\n\n"
            f"Your remaining limit is Rs.{remaining:,.0f}. "
            f"Would you like to see products under this budget?"
        )

        remaining = state["spend_limit"] - state["spent_so_far"]
        block_response = (
            f"{result['reason']}\n\n"
            f"Your remaining limit is ₹{remaining:,.0f}.\n\n"
            f"Here are some products within your budget:"
        )

        # Find products under remaining limit
        from db.database import SessionLocal
        from db.models import Product
        db = SessionLocal()
        budget_products = db.query(Product).filter(
            Product.price <= remaining,
            Product.stock > 0
        ).order_by(Product.price.desc()).limit(3).all()
        db.close()

        if budget_products:
            lines = "\n".join([
                f"• {p.name} — ₹{p.price:,.0f}"
                for p in budget_products
            ])
            block_response += f"\n\n{lines}"
        return {
            **state,
            "spend_blocked":       True,
            "spend_block_reason":  result["reason"],
            "final_response":      block_response,
            "audit_log":           state["audit_log"] + [audit_entry],
        }

    else:
        # ── Spend allowed ──────────────────────────────────────────────────
        logger.info(
            f"✅ Spend approved: "
            f"Rs.{state['payment_amount']:,.0f}"
        )

        audit_entry = {
            "node":      "spend_guard",
            "action":    f"approved Rs.{state['payment_amount']:,.0f}",
            "detail":    (
                f"Limit: Rs.{state['spend_limit']:,.0f} | "
                f"Used: Rs.{state['spent_so_far']:,.0f} | "
                f"Remaining: Rs.{state['spend_limit'] - state['spent_so_far']:,.0f}"
            ),
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "spend_blocked":      False,
            "spend_block_reason": "",
            "remaining_limit":    state["spend_limit"] - state["spent_so_far"],
            "audit_log":          state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()