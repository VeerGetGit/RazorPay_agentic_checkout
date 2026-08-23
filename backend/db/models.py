# backend/db/models.py

from sqlalchemy import (
    Column, String, Float, DateTime,
    Integer, Boolean, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime , timezone
from uuid import uuid4

Base = declarative_base()


# ── Session Table ──────────────────────────────────────────────────────────
class Session(Base):
    """
    One row per user conversation.
    Spend limit is set ONCE on creation — never reset.
    Token stored in React memory only (not localStorage).
    """
    __tablename__ = "sessions"

    id           = Column(String, primary_key=True,
                          default=lambda: str(uuid4()))
    token        = Column(String, unique=True, nullable=False)
    spend_limit  = Column(Float, default=100000.0)   # set once, never reset
    spent_so_far = Column(Float, default=0.0)        # running total
    last_active  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at   = Column(DateTime, nullable=False)  # last_active + 30 min
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    orders    = relationship("Order",    back_populates="session",
                             cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="session",
                              cascade="all, delete-orphan")


# ── Product Table ──────────────────────────────────────────────────────────
class Product(Base):
    """
    Merchant catalog. Seeded by db/seed.py.
    20 products across 4 categories.
    """
    __tablename__ = "products"

    id          = Column(String, primary_key=True,
                         default=lambda: str(uuid4()))
    name        = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price       = Column(Float, nullable=False)
    category    = Column(String, nullable=False)   # phones/shoes/bags/watches
    stock       = Column(Integer, default=10)
    image_url   = Column(String, nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ── Order Table ────────────────────────────────────────────────────────────
class Order(Base):
    """
    One row per Razorpay order created.
    idempotency_key prevents duplicate charges on double-tap.
    """
    __tablename__ = "orders"

    id                = Column(String, primary_key=True,
                               default=lambda: str(uuid4()))
    session_id        = Column(String, ForeignKey("sessions.id"),
                               nullable=False)
    razorpay_order_id = Column(String, nullable=True)   # from Razorpay API
    amount            = Column(Float, nullable=False)
    currency          = Column(String, default="INR")
    status            = Column(String, default="pending")
                                # pending / success / failed / cancelled
    idempotency_key   = Column(String, unique=True, nullable=False)
    items             = Column(Text, nullable=False)    # JSON string of cart
    created_at        = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at        = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("Session", back_populates="orders")


# ── AuditLog Table ────────────────────────────────────────────────────────
class AuditLog(Base):
    """
    Every agent action logged here.
    session_id is verified before reads — user A cannot see user B's logs.
    Streamed to frontend via SSE in real time.
    """
    __tablename__ = "audit_logs"

    id         = Column(String, primary_key=True,
                        default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"),
                        nullable=False)
    node       = Column(String, nullable=False)   # which graph node
    action     = Column(String, nullable=False)   # what it did
    detail     = Column(Text, nullable=True)      # extra info
    status     = Column(String, default="success")
                         # success / blocked / failed
    timestamp  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("Session", back_populates="audit_logs")