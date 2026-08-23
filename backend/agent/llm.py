# backend/agent/llm.py

from langchain_groq import ChatGroq
from rate_limiter.groq_limiter import groq_limiter
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ── Rate Limited ChatGroq Wrapper ──────────────────────────────────────────
class RateLimitedChatGroq(ChatGroq):
    """
    Wraps ChatGroq to automatically call groq_limiter
    before EVERY invoke call.

    This means NO node needs to manually call the rate limiter.
    Just import llm or llm_mini and call .invoke() normally.
    Rate limiting happens automatically under the hood.
    """

    def invoke(self, *args, **kwargs):
        groq_limiter.wait_if_needed(estimated_tokens=400)
        logger.debug("🤖 LLM invoke called")
        return super().invoke(*args, **kwargs)

    async def ainvoke(self, *args, **kwargs):
        groq_limiter.wait_if_needed(estimated_tokens=400)
        logger.debug("🤖 LLM async invoke called")
        return await super().ainvoke(*args, **kwargs)


# ── Main Agent LLM ─────────────────────────────────────────────────────────
# Used by: intent_node, catalog_node, checkout_node,
#          recovery_node, respond_node
llm = RateLimitedChatGroq(
    model       = os.getenv("GROQ_MODEL", "compound"),
    api_key     = os.getenv("GROQ_API_KEY"),
    temperature = 0,       # deterministic — payments must be predictable
    max_tokens  = 1024,
)


# ── Mini LLM ───────────────────────────────────────────────────────────────
# Used by: ShoppingTopicGuard in input_validators.py
# Faster and cheaper for simple classification tasks
llm_mini = RateLimitedChatGroq(
    model       = os.getenv("GROQ_MODEL_MINI", "compound-mini"),
    api_key     = os.getenv("GROQ_API_KEY"),
    temperature = 0,
    max_tokens  = 64,      # classification only needs short response
)


# ── Health Check ───────────────────────────────────────────────────────────
def check_llm_health() -> bool:
    """
    Quick check that Groq API is reachable.
    Called on FastAPI startup.
    Returns True if healthy, False if not.
    """
    try:
        response = llm_mini.invoke("Reply with only the word: OK")
        is_healthy = "OK" in response.content.upper()
        if is_healthy:
            logger.info("✅ Groq API health check passed")
        else:
            logger.warning("⚠️ Groq API returned unexpected response")
        return is_healthy
    except Exception as e:
        logger.error(f"❌ Groq API health check failed: {e}")
        return False