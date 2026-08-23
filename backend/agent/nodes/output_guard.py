# backend/agent/nodes/output_guard.py

from agent.state import AgentState
from validators.output_validators import validate_output
import logging

logger = logging.getLogger(__name__)


def output_guard_node(state: AgentState) -> AgentState:
    """
    Layer 3 Guardrail — cleans every response before
    it reaches the user.

    Checks:
    1. PII detection + scrubbing (API keys, emails, phones)
    2. Price hallucination guard (prices must exist in DB)

    If hallucinated price detected:
    - Blocks response
    - Returns safe fallback message
    - Logs to audit

    If PII detected:
    - Scrubs it automatically (replaces with [REDACTED])
    - Continues with cleaned response
    """

    final_response = state["final_response"]
    logger.info("🔍 Output guard checking response")

    if not final_response:
        return state

    result = validate_output(final_response)

    if result["passed"]:
        # ── Output clean ───────────────────────────────────────────────────
        logger.info("✅ Output guard passed")

        audit_entry = {
            "node":      "output_guard",
            "action":    "passed",
            "detail":    "No PII or hallucination detected",
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "final_response": result["response"],  # may be PII-scrubbed
            "output_blocked": False,
            "audit_log":      state["audit_log"] + [audit_entry],
        }

    else:
        # ── Output blocked ─────────────────────────────────────────────────
        logger.warning(f"🚫 Output blocked: {result['reason']}")

        audit_entry = {
            "node":      "output_guard",
            "action":    "blocked",
            "detail":    result["reason"],
            "status":    "blocked",
            "timestamp": _now(),
        }

        # Safe fallback response
        safe_response = (
            "I found some products for you. "
            "Please search again for accurate pricing information."
        )

        return {
            **state,
            "final_response": safe_response,
            "output_blocked": True,
            "audit_log":      state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()