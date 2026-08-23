# backend/agent/nodes/input_guard.py

from agent.state import AgentState
from validators.input_validators import validate_input
import logging

logger = logging.getLogger(__name__)


def input_guard_node(state: AgentState) -> AgentState:
    """
    Layer 1 Guardrail — first node every message hits.

    Runs 4 checks in order:
    1. Malformed input    (pure Python)
    2. Toxic language     (Guardrails AI)
    3. Prompt injection   (Llama Prompt Guard 2 86M)
    4. Off-topic request  (compound-mini)

    If ANY check fails:
    - Sets input_blocked = True
    - Sets block_reason
    - Logs to audit_log
    - Graph routes to respond_node directly
      (skips all other nodes)

    If ALL checks pass:
    - Sets input_blocked = False
    - Graph continues to intent_node
    """

    # Get latest user message
    user_message = state["messages"][-1].content
    logger.info(f"🛡️ Input guard checking: '{user_message[:50]}...'")

    # Run all 4 validators
    result = validate_input(user_message)

    if not result["passed"]:
        # ── Input blocked ──────────────────────────────────────────────
        logger.warning(f"🚫 Input blocked: {result['reason']}")

        # Add to audit log
        audit_entry = {
            "node":      "input_guard",
            "action":    "blocked",
            "detail":    result["reason"],
            "status":    "blocked",
            "timestamp": _now(),
        }

        return {
            **state,
            "input_blocked": True,
            "block_reason":  result["reason"],
            "audit_log":     state["audit_log"] + [audit_entry],
        }

    else:
        # ── Input passed ───────────────────────────────────────────────
        logger.info("✅ Input guard passed")

        audit_entry = {
            "node":      "input_guard",
            "action":    "passed",
            "detail":    "All 4 checks passed",
            "status":    "success",
            "timestamp": _now(),
        }

        return {
            **state,
            "input_blocked": False,
            "block_reason":  "",
            "audit_log":     state["audit_log"] + [audit_entry],
        }


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()