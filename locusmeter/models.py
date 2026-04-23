"""Pydantic models for Drip."""

from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    """Request body for provisioning a new user."""
    user_id: str
    email: str
    topic: Optional[str] = None          # research-agent-specific
    metadata: dict = {}                  # generic, not research-specific
    plan: str = "consumption"            # NEW
    initial_balance: float = 0.0
    consumption_unit_cost: float = 0.01  # renamed from credit_rate
    credit_rate: Optional[float] = None  # alias for backward compat
    subscription_monthly_cost: float = 0.0
    subscription_included_units: int = 0
    plan_policy: str = "suggest_only"


class UserResponse(BaseModel):
    """User state returned by API."""
    user_id: str
    email: str
    metadata: Optional[dict] = None
    bwl_service_id: Optional[str] = None
    status: str = "provisioning"
    balance_usdc: float = 0.0
    initial_balance: float = 0.0
    credit_rate: float = 0.05
    plan: str = "consumption"
    subscription_monthly_cost: float = 0.0
    subscription_included_units: int = 0
    billing_period_units_consumed: int = 0
    created_at: Optional[int] = None


class LogEntry(BaseModel):
    """A single agent reasoning log entry."""
    id: Optional[int] = None
    ts: str
    user_id: Optional[str] = None
    message: str


class CheckoutSessionCreate(BaseModel):
    """Request body for creating a checkout session."""
    user_id: str
    amount: float


class CheckoutSessionResponse(BaseModel):
    """Checkout session info returned to caller."""
    session_id: str
    checkout_url: str
    webhook_secret: str


class DebitRequest(BaseModel):
    """Request body for internal debit (called by research container)."""
    user_id: str
    amount: float
    label: str = "research_cycle"
