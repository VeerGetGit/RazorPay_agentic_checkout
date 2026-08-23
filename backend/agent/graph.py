# backend/agent/graph.py

from langgraph.graph import StateGraph, END
from agent.state import AgentState

# ── Import all nodes ───────────────────────────────────────────────────────
from agent.nodes.input_guard    import input_guard_node
from agent.nodes.intent_node    import intent_node
from agent.nodes.catalog_node   import catalog_node
from agent.nodes.checkout_node  import checkout_node
from agent.nodes.spend_guard    import spend_guard_node
from agent.nodes.action_guard   import action_guard_node
from agent.nodes.payment_node   import payment_node
from agent.nodes.recovery_node  import recovery_node
from agent.nodes.output_guard   import output_guard_node
from agent.nodes.audit_logger   import audit_logger_node
from agent.nodes.respond_node   import respond_node

# ── Import all edges ───────────────────────────────────────────────────────
from agent.edges.route_intent  import route_intent
from agent.edges.route_spend   import route_spend, route_consent
from agent.edges.route_payment import route_payment

import logging

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph agent.

    Full flow:
    START
      │
      ▼
    INPUT GUARD ──── blocked ──────────────────────────────→ RESPOND → END
      │ passes
      ▼
    INTENT NODE
      │
      ├── browse  ──→ CATALOG NODE ──→ OUTPUT GUARD ──→ RESPOND → END
      │
      └── checkout ─→ CHECKOUT NODE
                           │
                           ▼
                      SPEND GUARD ──── blocked ──→ RESPOND → END
                           │ allowed
                           ▼
                      ACTION GUARD ─── cancelled/waiting ──→ RESPOND → END
                           │ confirmed
                           ▼
                      PAYMENT NODE
                           │
                           ├── success ──→ AUDIT LOGGER ──→ OUTPUT GUARD ──→ RESPOND → END
                           │
                           └── failed ───→ RECOVERY NODE ──→ RESPOND → END
    """

    builder = StateGraph(AgentState)

    # ── Add all nodes ──────────────────────────────────────────────────────
    builder.add_node("input_guard",    input_guard_node)
    builder.add_node("intent",         intent_node)
    builder.add_node("catalog",        catalog_node)
    builder.add_node("checkout",       checkout_node)
    builder.add_node("spend_guard",    spend_guard_node)
    builder.add_node("action_guard",   action_guard_node)
    builder.add_node("payment",        payment_node)
    builder.add_node("recovery",       recovery_node)
    builder.add_node("output_guard",   output_guard_node)
    builder.add_node("audit_logger",   audit_logger_node)
    builder.add_node("respond",        respond_node)

    # ── Set entry point ────────────────────────────────────────────────────
    builder.set_entry_point("input_guard")

    # ── Add edges ──────────────────────────────────────────────────────────

    # Input guard → intent or respond (if blocked)
    builder.add_conditional_edges(
        "input_guard",
        route_intent,
        {
            "catalog":  "intent",
            "checkout": "intent",
            "respond":  "respond",
            "blocked":  "respond",
        }
    )

    # Intent → catalog or checkout or respond
    builder.add_conditional_edges(
        "intent",
        route_intent,
        {
            "catalog":  "catalog",
            "checkout": "checkout",
            "respond":  "respond",
            "blocked":  "respond",
        }
    )

    # Catalog → output_guard → respond
    builder.add_edge("catalog",      "output_guard")
    builder.add_edge("output_guard", "respond")

    # Checkout → spend_guard
    builder.add_edge("checkout", "spend_guard")

    # Spend guard → action_guard or respond
    builder.add_conditional_edges(
        "spend_guard",
        route_spend,
        {
            "allowed": "action_guard",
            "blocked": "respond",
        }
    )

    # Action guard → payment or respond
    builder.add_conditional_edges(
        "action_guard",
        route_consent,
        {
            "confirmed": "payment",
            "cancelled": "respond",
            "waiting":   "respond",
        }
    )

    # Payment → audit_logger or recovery
    builder.add_conditional_edges(
        "payment",
        route_payment,
        {
            "success": "audit_logger",
            "failed":  "recovery",
        }
    )

    # Audit logger → output_guard → respond
    builder.add_edge("audit_logger", "output_guard")

    # Recovery → respond
    builder.add_edge("recovery", "respond")

    # Respond → END
    builder.add_edge("respond", END)

    # ── Compile ────────────────────────────────────────────────────────────
    graph = builder.compile()
    logger.info("✅ LangGraph agent compiled successfully")

    return graph


# ── Single shared graph instance ──────────────────────────────────────────
graph = build_graph()

# ── Visualize graph (run this once to see the diagram) ────────────────────
if __name__ == "__main__":
    from IPython.display import Image, display
    import os

    # Option 1 — Print Mermaid code (paste at mermaid.live)
    print("=== MERMAID DIAGRAM CODE ===")
    print(graph.get_graph().draw_mermaid())

    # Option 2 — Save as PNG image
    png_data = graph.get_graph().draw_mermaid_png()
    with open("graph_diagram.png", "wb") as f:
        f.write(png_data)
    print("✅ Graph saved as graph_diagram.png")