# backend/agent/state.py

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages
from datetime import datetime


class CartItem(TypedDict):
    """Single item in the cart."""
    product_id:   str
    name:         str
    price:        float
    quantity:     int
    total:        float


class AuditEntry(TypedDict):
    """Single audit log entry — every agent action logged."""
    node:      str        # which graph node took the action
    action:    str        # what it did
    detail:    str        # extra context
    status:    str        # success / blocked / failed
    timestamp: str        # ISO format datetime string


class AgentState(TypedDict):
    """
    The single source of truth for the entire agent.
    Flows through every node in the LangGraph.
    Every node reads this, updates what it needs, returns it.

    NEVER modify state directly — always return updated copy from node.
    """

    # ── Conversation ───────────────────────────────────────────────────────
    messages: Annotated[list, add_messages]
    # Full conversation history
    # add_messages = new messages are appended, not replaced

    # ── Session ────────────────────────────────────────────────────────────
    session_id:    str
    # DB session ID — links to Session table

    session_token: str
    # X-Session-Token from request header
    # Verified before every audit read/write

    # ── Cart ───────────────────────────────────────────────────────────────
    cart: list[CartItem]
    # List of CartItem dicts
    # Updated by catalog_node when user adds items

    cart_total: float
    # Sum of all cart item totals
    # Recalculated on every cart update

    # ── Spend Tracking ─────────────────────────────────────────────────────
    spend_limit:  float
    # From DB session — set ONCE on session creation
    # Never changes during the conversation

    spent_so_far: float
    # Total amount successfully paid in this session
    # Updated after every successful payment

    remaining_limit: float
    # spend_limit - spent_so_far
    # Recalculated by spend_guard on every check

    # ── Intent ─────────────────────────────────────────────────────────────
    intent: str
    # Classified by intent_node
    # Values: "browse" / "checkout" / "status" / "cancel" / "unknown"

    # ── Input Guard ────────────────────────────────────────────────────────
    input_blocked: bool
    # Set to True by input_guard if any check fails
    # Routes graph to reject node

    block_reason: str
    # Human-readable reason for block
    # Shown to user by respond_node

    # ── Spend Guard ────────────────────────────────────────────────────────
    spend_blocked: bool
    # Set to True by spend_guard if amount exceeds limit
    # Routes graph to explain node

    spend_block_reason: str
    # e.g. "Cart total ₹15,000 exceeds remaining limit ₹8,000"

    # ── Consent / Action Guard ─────────────────────────────────────────────
    consent_given: bool
    # Set to True when user explicitly confirms payment
    # action_guard checks this before allowing payment_node

    awaiting_consent: bool
    # Set to True when agent is waiting for user confirmation
    # Frontend shows ConsentReceipt modal when this is True

    # ── Payment ────────────────────────────────────────────────────────────
    razorpay_order_id: Optional[str]
    # Returned by Razorpay create_order API
    # Stored in Order table

    payment_status: str
    # "pending" / "success" / "failed" / "cancelled"

    idempotency_key: Optional[str]
    # Prevents duplicate Razorpay orders on double-tap
    # Format: {session_id}_{cart_hash}_{minute}

    payment_amount: float
    # Final amount sent to Razorpay
    # Must match cart_total after spend_guard approves

    # ── Recovery ───────────────────────────────────────────────────────────
    payment_failed: bool
    # Set to True by payment_node on failure
    # Routes graph to recovery_node

    failure_reason: str
    # e.g. "Payment gateway timeout"
    # Used by recovery_node to craft response

    retry_count: int
    # How many times payment has been attempted
    # recovery_node stops retrying after 3 attempts

    # ── Output ─────────────────────────────────────────────────────────────
    final_response: str
    # The message respond_node sends back to user
    # Cleaned by output_guard before sending

    output_blocked: bool
    # Set to True by output_guard if response is unsafe
    # Triggers re-fetch from DB

    # ── Audit ──────────────────────────────────────────────────────────────
    audit_log: list[AuditEntry]
    # Every agent action appended here during the conversation
    # Persisted to DB by audit_logger node
    # Streamed to frontend via SSE


def get_initial_state(
    session_id:    str,
    session_token: str,
    spend_limit:   float,
    spent_so_far:  float,
    user_message:  str,
) -> AgentState:
    """
    Creates the initial state for a new conversation turn.
    Called by api/chat.py before invoking the graph.
    """
    return AgentState(
        # Conversation
        messages         = [{"role": "user", "content": user_message}],

        # Session
        session_id       = session_id,
        session_token    = session_token,

        # Cart (loaded from DB or empty for first message)
        cart             = [],
        cart_total       = 0.0,

        # Spend
        spend_limit      = spend_limit,
        spent_so_far     = spent_so_far,
        remaining_limit  = spend_limit - spent_so_far,

        # Intent
        intent           = "unknown",

        # Input guard
        input_blocked    = False,
        block_reason     = "",

        # Spend guard
        spend_blocked       = False,
        spend_block_reason  = "",

        # Consent
        consent_given    = False,
        awaiting_consent = False,

        # Payment
        razorpay_order_id = None,
        payment_status    = "pending",
        idempotency_key   = None,
        payment_amount    = 0.0,

        # Recovery
        payment_failed   = False,
        failure_reason   = "",
        retry_count      = 0,

        # Output
        final_response   = "",
        output_blocked   = False,

        # Audit
        audit_log        = [],
    )