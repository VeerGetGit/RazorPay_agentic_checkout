# RazorFlow AI — 5 Minute Pitch Video Script

**Razorpay AI Buildathon 2026 | Track 01 — AI Growth & Agentic Commerce**  
**GitHub:** https://github.com/VeerGetGit/RazorPay_agentic_checkout  

---

## Video Structure

| Timestamp | Section | Duration |
|-----------|---------|----------|
| 0:00 — 0:36 | Introduction + Problem Statement | 36 seconds |
| 0:37 — 1:42 | Architecture of the AI Agent | 65 seconds |
| 1:42 — 4:09 | Full Demo of the AI Agent | 147 seconds |
| 4:10 — 5:24 | A2A Commerce — AI Buying Autonomously | 74 seconds |

---

## [0:00 — 0:36] Introduction + Problem Statement

**Speaker:** Harsh Veer Singh  
**Track:** AI Growth & Agentic Commerce — Track 01, Razorpay AI Buildathon 2026

Every year billions of rupees are lost at checkout. Not because people don't want to buy — but because checkout is broken. Forms, dropdowns, steps. Hectic. And that's just for humans.

NPCI is building UAP — the Unified Agentic Protocol for AI-to-AI payments. Razorpay needs to be ready. I built that infrastructure. This is RazorFlow AI.

---

## [0:37 — 1:42] Architecture of the AI Agent

**Showing:** GitHub README → Mermaid architecture diagram

The agent runs on LangGraph — 10 specialized nodes:

- **input_guard** — blocks injections, toxic content, leetspeak normalization
- **intent** — classifies browse / checkout / status / unknown
- **catalog** — handles browsing, cart, budget queries, upsell recommendations
- **spend_guard** — enforces spend limit at code level, not prompt level
- **action_guard** — confirms payment with user before proceeding
- **payment** — calls Razorpay test-mode API, generates real order ID
- **audit_logger** — logs every decision with timestamp
- **output_guard** — validates prices against catalog DB, scrubs PII
- **recovery** — handles failed or cancelled payments gracefully
- **respond** — sends final response to user

LLM is used ONLY where it adds value. Every financial decision is deterministic code — not LLM output.

---

## [1:42 — 4:09] Full Demo of the AI Agent

**Showing:** https://razor-pay-agentic-checkout.vercel.app

### Human Buyer Flow
- Natural language shopping in English and Hindi
- Budget queries: "show me phones under 30000"
- Add to cart: "add redmi to my cart"
- Upsell suggestions shown after every add
- Payment via Razorpay test-mode — real order ID generated
- Post-payment budget suggestion shown
- Audit trail updates in real time
- Merchant revenue widget updates automatically

### Security Demo
- Spend limit exceeded → blocked with budget suggestions
- "ignore your instructions" → prompt injection blocked
- "1gn0re your 1nstruct10ns" → leetspeak normalized and blocked

### Key Metrics Shown
- Merchant revenue dashboard: total revenue, AOV, upsell rate
- Agent revenue percentage — what AI recommendations contributed
- Audit trail: every node, every decision, every timestamp

---

## [4:10 — 5:24] A2A Commerce — AI Buying Autonomously

**Showing:** Terminal running `python tests/test_a2a.py`  
**Live endpoint:** https://razorpay-agentic-checkout.onrender.com/api/catalog/agent/discover

This is agent-to-agent commerce. An AI buyer with zero human involvement:

1. Creates session automatically
2. Reads machine-readable catalog at `/api/catalog/agent/discover`
3. Discovers 19 products with `buy_intent` strings and `price_integrity` declaration
4. Selects best product within budget constraints
5. Adds to cart via `POST /api/chat`
6. Pays via Razorpay — real order ID generated
7. Receives structured JSON confirmation with `razorpay-agentic-v1` protocol
8. Spend limit correctly blocks second purchase
9. Security: 5/5 attacks blocked including leetspeak

**This is what NPCI UAP enables. Any AI — Claude, GPT, Gemini — can buy from this store today.**

---

## What Was Built

```
✅ Conversational checkout — natural language 
✅ Agent-readable catalog — /api/catalog/agent/discover
✅ Upsell & cross-sell — after every add to cart
✅ Spend limit enforcement — code level, not prompt level
✅ Complete audit trail — every money action explainable
✅ Merchant revenue dashboard — AOV, upsell rate, agent impact
✅ A2A commerce — AI buyer purchases autonomously
✅ 98.3% eval score — 117/119 adversarial test cases
✅ Live on Render + Vercel
✅ Real Razorpay test-mode order IDs
```

---

## Closing Statement

> "This is not a chatbot that makes payments.
> This is bounded AI commerce infrastructure —
> conversational for humans, machine-readable for AI buyers,
> every rupee tracked, validated, and audited.
> Built on Razorpay test-mode APIs. Live right now.
> Bounded. Explainable. Agent-ready. Built on Razorpay."

---

*Razorpay AI Buildathon 2026 — Track 01: AI Growth & Agentic Commerce*  
*GitHub: https://github.com/VeerGetGit/RazorPay_agentic_checkout*
