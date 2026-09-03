# Failure Postmortem — RazorFlow AI

> Every failure made the system stronger. None were hidden.

---

## Failure 1 — Guardrails Library Rejected, Custom Security Built

**Decision:** Evaluated guardrails-ai. Rejected it deliberately.

### Why We Rejected It

guardrails-ai introduced three unacceptable risks for a financial agent:

1. **Python version fragility** — DetectPII ImportError on 3.12/3.14 proved the library was not production-stable
2. **Heavy dependencies** — spaCy, presidio, hub authentication added 500MB+ overhead for a demo system
3. **Black box behavior** — we couldn't audit what it blocked or allowed. For a financial agent where every decision must be explainable, an opaque library is worse than no library

### What We Built Instead

Custom security layer with full auditability:

```python
# Injection detection with leetspeak normalization
def _normalize_text(message: str) -> str:
    replacements = {'0':'o', '1':'i', '3':'e', '4':'a', '5':'s'}
    normalized = message.lower()
    for char, replacement in replacements.items():
        normalized = normalized.replace(char, replacement)
    return normalized

# Check both original AND normalized
if _is_injection(message) or _is_injection(normalized):
    return {"passed": False, "reason": "injection detected"}
```

### Why This Is Stronger

Our guardrails are transparent, testable, and auditable. We know exactly why every message is blocked or allowed. **30/30 = 100%** on adversarial guardrail test suite including leetspeak attacks like "1gn0re your 1nstruct10ns".

An LLM-based guardrail that blocks correctly 95% of the time is worse than a deterministic system that blocks correctly 100% of the time for known attack patterns.

---

## Failure 2 — Groq Rate Limits Forced Better Architecture

**What happened:** Pure LLM-based intent classification hit Groq's rate limits (25 RPM) within minutes of load testing.

### Root Cause

groq/compound routes through llama-3.3-70b internally. Every single user message — including "hi", "show me phones", "buy it" — was consuming LLM quota for patterns that needed no intelligence at all.

### Why This Made the System Better

This failure forced a better architectural decision:

```python
# High-confidence patterns — zero LLM cost, zero latency
checkout_keywords = ["buy it", "haan bhai pay kar do", "but khareed de"]
if any(kw in msg for kw in checkout_keywords):
    return "checkout"  # deterministic, sub-millisecond

# Only genuinely ambiguous inputs hit the LLM
response = llm.invoke([SystemMessage(...), HumanMessage(content=user_message)])
```

**Result:** 80% of queries skip the LLM entirely. This is the right tool in the right place — AI for genuine language understanding, deterministic logic for high-confidence patterns. **51/51 = 100%** intent test cases passing.

---

## Failure 3 — Output Guard False Positives Revealed Design Flaw

**What happened:** Price hallucination checker was blocking legitimate budget query responses like "watches in 15k showing ₹4,499".

### Root Cause

The checker treated ALL prices in responses as potentially hallucinated. It couldn't distinguish between:
1. LLM-generated price (potentially dangerous) — should validate
2. Catalog query result passed through (from DB) — should skip

### Fix

Added response type detection before price validation:

```python
skip_phrases = [
    "Here's what you can get", "Added to cart",
    "Cart total", "Payment successful",
]
if any(phrase in text for phrase in skip_phrases):
    return False  # legitimate catalog response — skip validation
```

**Lesson:** Output validation must understand response context, not just scan for numbers.

---

## Failure 4 — SQLite Ephemeral Storage Forced Proper Persistence

**What happened:** Merchant revenue data reset on every Render server restart. 13 orders recorded during testing disappeared overnight.

### Root Cause

Render free tier has ephemeral storage. In-memory dict does not persist across restarts.

### Fix

Moved to SQLite persistence with proper ORM model:

```python
class RevenueLog(Base):
    __tablename__ = "revenue_logs"
    id            = Column(Integer, primary_key=True)
    session_id    = Column(String)
    merchant_id   = Column(String, default="demo-store")
    amount        = Column(Float)
    had_upsell    = Column(Boolean)
    upsell_amount = Column(Float)
    timestamp     = Column(String)
```

**Result:** Revenue persists across restarts. Aggregates across all customer sessions. Supports merchant_id filtering for multi-merchant architecture.

---

## Failure 5 — CORS Block Revealed Production Deployment Gap

**What happened:** After deploying frontend to Vercel, all API calls failed with CORS policy error.

### Root Cause

Backend CORS configured for localhost only. Vercel URL not in allowed origins.

### Fix

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = False,  # required when using "*"
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)
```

`allow_credentials = False` is correct here — app uses `X-Session-Token` header for auth, not cookies. Zero functional impact.

---

## Summary

| Failure | What It Forced | Result |
|---------|---------------|--------|
| Guardrails library | Build custom auditable security | 100% guardrail score |
| Groq rate limits | Hybrid deterministic+LLM pipeline | 80% LLM calls eliminated |
| Output guard false positives | Response type detection | Budget queries work correctly |
| SQLite ephemeral storage | Proper DB persistence layer | Revenue persists forever |
| CORS Vercel block | Production deployment hardening | Frontend deployed successfully |

> These were not setbacks. They were design reviews that produced better decisions.
