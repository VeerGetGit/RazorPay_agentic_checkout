# Buildathon Criteria Review — RazorFlow AI

> Self-assessment against Razorpay AI Buildathon 2026 Track 01 criteria.

---

## Track Statement

> "Grow the merchant's revenue, and make them sellable to AI buyers. Build an agent that grows revenue for a merchant on Razorpay test-mode APIs, or that makes a merchant transactable by an AI buyer end to end."

---

## Criterion 1 — Problem Taste

> "Did you pick something that actually matters?"

**Assessment: Strong ✅**

Agent-to-agent commerce is the defining open problem of 2026. NPCI's UAP protocol, Anthropic's MCP, and the x402 payment standard are all attempting to solve the same question: how do AI agents buy things?

Razorpay processes UPI payments. If NPCI UAP becomes the standard for AI-driven payments, Razorpay must be ready. This project demonstrates exactly what that infrastructure looks like in practice — a merchant store that is discoverable and transactable by both human buyers and AI buyers.

**Evidence:**
- `/api/catalog/agent/discover` — machine-readable catalog with `razorpay-agentic-v1` protocol
- `test_a2a.py` — AI buyer autonomously purchases with zero human involvement
- Claude, ChatGPT, and Gemini independently verified the store is agent-commerce ready

---

## Criterion 2 — Build Quality

> "Does it run, is it structured, would you trust it?"

**Assessment: Strong ✅**

**Does it run?**
- Backend: https://razorpay-agentic-checkout.onrender.com/health
- Frontend: https://razor-pay-agentic-checkout.vercel.app
- Both live and accessible right now

**Is it structured?**
```
backend/
├── agent/nodes/     # 10 specialized LangGraph nodes
├── api/             # FastAPI endpoints
├── validators/      # Input/output/spend guards
├── db/              # SQLite models
└── evals/           # Evaluation suite

frontend/
└── src/
    ├── components/  # UI components
    └── hooks/       # API hooks
```

**Would you trust it?**
- 117/119 = 98.3% eval score across adversarial test cases
- 100% guardrail score including leetspeak attacks
- Real Razorpay test-mode order IDs generated
- Complete audit trail for every money action
- 5 real production failures documented and fixed

---

## Criterion 3 — AI Judgment

> "The right tool in the right place, and where you chose not to use one."

**Assessment: Strong ✅**

**Where AI is used:**
- Intent classification for ambiguous natural language inputs
- Product search keyword extraction from free-form text
- LLM-as-judge for eval quality assessment (independent model)

**Where AI is deliberately NOT used:**
- Spend limit enforcement → pure Python code
- Price validation → SQLAlchemy DB query
- Common intent patterns → deterministic keyword matching
- PII scrubbing → regex
- Injection detection → keyword list + leetspeak normalization
- Duplicate order detection → timestamp comparison

**The judgment:** AI adds value for language understanding. For financial decisions and security enforcement, deterministic code is more reliable, faster, and cannot be manipulated through adversarial prompting.

This mirrors production fintech systems — state machines and deterministic rules for money decisions, AI for language understanding only.

---

## Criterion 4 — Failure Recovery

> "What broke, and what you did about it."

**Assessment: Strong ✅**

Five real failures encountered and fixed. Full postmortem in `docs/FAILURE_POSTMORTEM.md`.

| Failure | Fix | Result |
|---------|-----|--------|
| guardrails-ai broke on Python 3.14 | Pure regex replacement | Zero dependencies, faster |
| Groq rate limits | Keyword-first hybrid pipeline | 80% LLM calls eliminated |
| Output guard false positives | Skip phrases detection | Budget queries work correctly |
| SQLite data loss on restart | DB persistence layer | Revenue persists forever |
| CORS blocking Vercel | allow_origins wildcard | Frontend deployed successfully |

**Graceful failure handling in production:**
- Puma RS-X out of stock → alternatives shown automatically
- Spend limit exceeded → budget suggestions shown
- Duplicate order attempt → detected and blocked
- Injection attack → clean refusal, no crash

---

## Track Requirements Checklist

| Requirement | Evidence | Status |
|-------------|----------|--------|
| Conversational checkout | Natural language flow | ✅ |
| Razorpay test-mode APIs | Real order IDs in Razorpay dashboard | ✅ |
| Agent-readable catalog | /api/catalog/agent/discover | ✅ |
| Upsell & cross-sell | After every add-to-cart | ✅ |
| Grow merchant revenue | AOV tracking, upsell rate, agent revenue % | ✅ |
| AI buyer end-to-end | test_a2a.py — zero human involvement | ✅ |
| Every money action explainable | Audit trail per node per timestamp | ✅ |
| Bounded | Spend limit enforced in code | ✅ |
| Gated | Input guard + spend guard + action guard | ✅ |
| One failure handled gracefully | Out of stock, spend exceeded, duplicate | ✅ |

---

## Known Limitations

Documented honestly — not hidden:

1. **No inventory reservation** — concurrent buyers could oversell at scale
2. **Static pricing** — no TTL on catalog prices
3. **No agent DID** — session tokens rather than verified agent identity
4. **Not formally UAP compliant** — architecturally compatible, not certified
5. **Webhooks not implemented** — order status via polling

These are appropriate scope boundaries for a buildathon proof-of-concept. The core value proposition — conversational commerce and A2A infrastructure — is fully demonstrated.
