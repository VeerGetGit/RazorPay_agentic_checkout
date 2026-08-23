# backend/rate_limiter/middleware.py

from fastapi import Request
from fastapi.responses import JSONResponse
from rate_limiter.groq_limiter import groq_limiter
import logging

logger = logging.getLogger(__name__)


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware that:
    1. Exposes rate limit status on every response header
    2. Returns 429 if somehow limit is exceeded
       (backup — groq_limiter.wait_if_needed() should prevent this)

    Headers added to every response:
        X-RateLimit-Requests-Used
        X-RateLimit-Requests-Remaining
        X-RateLimit-Tokens-Used
        X-RateLimit-Tokens-Remaining
    """

    # Get current status before request
    status = groq_limiter.get_status()

    # If already at hard limit — return 429 immediately
    # This is a backup — wait_if_needed() handles normal throttling
    if status["requests_remaining"] <= 0:
        logger.warning("❌ Hard rate limit reached — returning 429")
        return JSONResponse(
            status_code = 429,
            content     = {
                "error":   "Rate limit exceeded",
                "message": "Too many requests. Please wait a moment.",
                "retry_after_seconds": 60,
            }
        )

    # Process the request normally
    response = await call_next(request)

    # Add rate limit headers to response
    response.headers["X-RateLimit-Requests-Used"]      = str(status["requests_used"])
    response.headers["X-RateLimit-Requests-Remaining"] = str(status["requests_remaining"])
    response.headers["X-RateLimit-Tokens-Used"]        = str(status["tokens_used"])
    response.headers["X-RateLimit-Tokens-Remaining"]   = str(status["tokens_remaining"])

    return response