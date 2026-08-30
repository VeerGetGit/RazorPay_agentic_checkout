# backend/api/analytics.py
# Merchant Revenue Analytics — DB persisted

from fastapi import APIRouter
from db.database import SessionLocal
from db.models import RevenueLog
from datetime import datetime, timezone
import logging
import json

logger = logging.getLogger(__name__)
router  = APIRouter()


def track_order(
    session_id:    str,
    amount:        float,
    items:         list,
    had_upsell:    bool  = False,
    upsell_item:   str   = None,
    upsell_amount: float = 0.0,
    merchant_id:   str   = "demo-store",
):
    """Save order to DB — persists across server restarts."""
    db = SessionLocal()
    try:
        log = RevenueLog(
            session_id    = session_id,
            merchant_id   = merchant_id,
            amount        = amount,
            items         = json.dumps([i.get("name") for i in items]),
            had_upsell    = had_upsell,
            upsell_item   = upsell_item or "",
            upsell_amount = upsell_amount,
            timestamp     = datetime.now(timezone.utc).isoformat(),
        )
        db.add(log)
        db.commit()
        logger.info(f"📈 Revenue saved: ₹{amount:,.0f} | merchant: {merchant_id}")
    except Exception as e:
        logger.error(f"❌ Revenue save error: {e}")
        db.rollback()
    finally:
        db.close()


@router.get("/api/analytics/revenue")
def get_revenue(merchant: str = "demo-store"):
    """
    Merchant revenue dashboard.
    Reads from DB — persists across restarts.
    Filter by merchant_id for multi-merchant support.
    """
    db = SessionLocal()
    try:
        logs = db.query(RevenueLog).filter(
            RevenueLog.merchant_id == merchant
        ).all()

        total_revenue  = sum(l.amount for l in logs)
        total_orders   = len(logs)
        upsell_logs    = [l for l in logs if l.had_upsell]
        upsell_revenue = sum(l.upsell_amount for l in upsell_logs)
        aov            = total_revenue / total_orders if total_orders > 0 else 0
        upsell_rate    = len(upsell_logs) / total_orders * 100 if total_orders > 0 else 0
        agent_pct      = upsell_revenue / total_revenue * 100 if total_revenue > 0 else 0

        recent = []
        for l in logs[-10:]:
            recent.append({
                "session_id":  l.session_id,
                "amount":      l.amount,
                "items":       json.loads(l.items),
                "had_upsell":  l.had_upsell,
                "upsell_item": l.upsell_item,
                "timestamp":   l.timestamp,
            })

        return {
            "merchant":  merchant,
            "currency":  "INR",
            "summary": {
                "total_revenue":     round(total_revenue, 2),
                "total_orders":      total_orders,
                "avg_order_value":   round(aov, 2),
                "agent_revenue":     round(upsell_revenue, 2),
                "agent_revenue_pct": f"{agent_pct:.1f}%",
                "upsell_rate":       f"{upsell_rate:.1f}%",
            },
            "recent_orders": recent,
        }
    finally:
        db.close()


@router.get("/api/analytics/aov")
def get_aov(merchant: str = "demo-store"):
    """Quick AOV for frontend widget."""
    db = SessionLocal()
    try:
        logs          = db.query(RevenueLog).filter(
            RevenueLog.merchant_id == merchant
        ).all()
        total         = len(logs)
        total_revenue = sum(l.amount for l in logs)
        aov           = total_revenue / total if total > 0 else 0
        upsell_orders = len([l for l in logs if l.had_upsell])
        upsell_rate   = upsell_orders / total * 100 if total > 0 else 0

        return {
            "avg_order_value": round(aov, 2),
            "total_orders":    total,
            "total_revenue":   round(total_revenue, 2),
            "upsell_rate":     f"{upsell_rate:.1f}%",
            "agent_revenue_pct": f"{(sum(l.upsell_amount for l in logs if l.had_upsell) / total_revenue * 100) if total_revenue > 0 else 0:.1f}%",
        }
    finally:
        db.close()