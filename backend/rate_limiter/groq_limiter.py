# backend/rate_limiter/groq_limiter.py

import time
import threading
from collections import deque
import logging

logger = logging.getLogger(__name__)


class GroqRateLimiter:
    """
    Token bucket rate limiter for Groq API.

    Enforces:
    - Max 25 RPM  (Groq free tier = 30 RPM  — we stay under)
    - Max 5500 TPM (Groq free tier = 6000 TPM — we stay under)

    Thread-safe — works with FastAPI's concurrent requests.
    Auto-sleeps when limit approached — never crashes on 429.

    One user message = max 5 Groq calls
    5 calls × 5 messages/minute = 25 RPM ✅
    """

    def __init__(self, rpm: int = 25, tpm: int = 5500):
        self.rpm  = rpm
        self.tpm  = tpm

        # Rolling window tracking
        self.requests    = deque()   # timestamps of recent requests
        self.tokens_used = deque()   # (timestamp, token_count) pairs

        # Thread safety
        self.lock = threading.Lock()

    def wait_if_needed(self, estimated_tokens: int = 300):
        """
        Called before every Groq API call.
        If under limit → returns immediately.
        If at limit    → sleeps until window clears.
        Never raises an exception.
        """
        with self.lock:
            now    = time.time()
            window = 60  # 1 minute rolling window

            # ── Clean old entries ──────────────────────────────────────────
            while self.requests and now - self.requests[0] > window:
                self.requests.popleft()

            while self.tokens_used and now - self.tokens_used[0][0] > window:
                self.tokens_used.popleft()

            # ── Check RPM limit ────────────────────────────────────────────
            if len(self.requests) >= self.rpm:
                sleep_time = window - (now - self.requests[0]) + 0.5
                logger.warning(
                    f"⏳ RPM limit reached ({self.rpm}/min). "
                    f"Sleeping {sleep_time:.1f}s"
                )
                time.sleep(sleep_time)
                now = time.time()

                # Clean again after sleep
                while self.requests and now - self.requests[0] > window:
                    self.requests.popleft()

            # ── Check TPM limit ────────────────────────────────────────────
            total_tokens = sum(t for _, t in self.tokens_used)

            if total_tokens + estimated_tokens > self.tpm:
                sleep_time = window - (now - self.tokens_used[0][0]) + 0.5
                logger.warning(
                    f"⏳ TPM limit reached ({total_tokens}/{self.tpm}). "
                    f"Sleeping {sleep_time:.1f}s"
                )
                time.sleep(sleep_time)
                now = time.time()

                # Clean again after sleep
                while self.tokens_used and now - self.tokens_used[0][0] > window:
                    self.tokens_used.popleft()

            # ── Record this request ────────────────────────────────────────
            self.requests.append(now)
            self.tokens_used.append((now, estimated_tokens))

    def get_status(self) -> dict:
        """
        Returns current rate limit status.
        Used by middleware to expose /health endpoint.
        """
        with self.lock:
            now    = time.time()
            window = 60

            recent_requests = [r for r in self.requests
                               if now - r <= window]
            recent_tokens   = sum(t for ts, t in self.tokens_used
                                  if now - ts <= window)

            return {
                "requests_used":    len(recent_requests),
                "requests_limit":   self.rpm,
                "tokens_used":      recent_tokens,
                "tokens_limit":     self.tpm,
                "requests_remaining": self.rpm - len(recent_requests),
                "tokens_remaining":   self.tpm - recent_tokens,
            }


# ── Single shared instance ─────────────────────────────────────────────────
# Imported by llm.py — every node uses this automatically
groq_limiter = GroqRateLimiter(rpm=25, tpm=13000)