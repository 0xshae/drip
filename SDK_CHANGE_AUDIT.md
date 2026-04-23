# SDK & Codebase Change Audit: Repositioning Drip as B2B2C Middleware

## Summary

The existing codebase is technically sound and closer to the new vision than it looks. The core metering, container lifecycle, and agent polling loop are all correct. What needs to change is:

1. **The mental model baked into the API**: Currently the SDK is designed for a "single app deployed on BWL" pattern. The new vision is "middleware a SaaS company integrates into their existing app." This changes some API surface, naming, and configuration.
2. **The hybrid billing model**: The current SDK only does pure consumption (`@meter` deducts credits). It has no concept of a subscription tier or plan-switching logic.
3. **The agent's intelligence scope**: The current polling loop only monitors credit balance. The new vision requires the agent to compare the customer's actual consumption cost against subscription cost and suggest/switch plans.
4. **Closed-source repositioning**: Several internal implementation details are currently visible in the public README and docs. These should be abstracted.

---

## File-by-File Change Notes

### `sdk/locus_drip/client.py`

**Current state:** `DripClient` takes `locus_api_key`, `bwl_api_key`, `agentmail_inbox`. The config is infrastructure-specific (exposing BWL and PWL as required config).

**Problem:** SaaS companies integrating Drip should not need to configure BWL or PWL directly. Those are Drip's infrastructure, not the customer's. Exposing them in `DripConfig` leaks the IP and creates unnecessary setup friction.

**Proposed change:**
```python
# Current
@dataclass
class DripConfig:
    locus_api_key: str
    bwl_api_key: str
    agentmail_inbox: str
    locus_api_base: str = "https://beta-api.paywithlocus.com/api"
    bwl_api_base: str = "https://beta-api.buildwithlocus.com"
    poll_interval_seconds: int = 60
    mock_drain: bool = False

# Should become
@dataclass
class DripConfig:
    api_key: str                                  # Single Drip API key — hides BWL/PWL from customer
    drip_api_base: str = "https://api.drip.so"   # Drip's own endpoint that proxies to BWL/PWL
    poll_interval_seconds: int = 60
    mock_drain: bool = False
```

This means building a thin Drip API layer that proxies to BWL/PWL using Drip's own keys, so SaaS customers only configure one thing. This is the **biggest structural change** and should be prioritized.

---

**Proposed: Add billing plan support to `provision_user`:**
```python
# Current signature
async def provision_user(
    self,
    user_id: str,
    email: str,
    initial_balance: float = 0.0,
    ...
)

# Proposed signature
async def provision_user(
    self,
    user_id: str,
    email: str,
    plan: str = "consumption",         # NEW: "consumption", "subscription", "hybrid"
    initial_balance: float = 0.0,
    subscription_monthly_cost: float = 0.0,  # NEW: what the SaaS charges for subscription tier
    subscription_included_units: int = 0,    # NEW: how many units the subscription covers
    ...
)
```

**Proposed: Add `DripSubscriptionConfig` for hybrid plan support:**
```python
@dataclass
class DripSubscriptionConfig:
    monthly_cost_usdc: float      # e.g., 20.0
    included_units: int           # e.g., 1000
    overage_cost_per_unit: float  # e.g., 0.007
    cycle_day: int = 1            # which day of month billing resets
```

---

### `sdk/locus_drip/meter.py` (the `@meter` decorator)

**Current state:** Works correctly. Single decorator that debits a fixed cost per call.

**No breaking changes needed.** The decorator interface is correct and should stay.

**Minor additions needed:**
1. Add `unit: int = 1` parameter — allows metering N units per call (e.g., 1,000 tokens = 1 unit)
2. Add `label: Optional[str] = None` — overrides `event` in the UI display (separate machine-readable event from human-readable label)
3. Add `dry_run: bool = False` — allows testing without debiting (useful for SaaS dev environments)

```python
# Current
def meter(self, cost: float, event: str, user_id_param: str = "user_id"):

# Proposed
def meter(
    self,
    cost: float,
    event: str,
    user_id_param: str = "user_id",
    unit: int = 1,
    label: Optional[str] = None,
    dry_run: bool = False,
):
```

---

### `sdk/locus_drip/client.py` — `start_polling` (the agent loop)

**Current state:** The agent only checks balance and triggers hibernate/warn. It has no awareness of subscription plans or plan optimization.

**Proposed additions to the polling loop:**

```python
# NEW: Plan optimization logic (conceptual — not implementing yet)
# For each user, at each polling cycle:
#   1. Compute actual consumption cost so far this billing period
#   2. If user is on consumption plan AND consumption_cost_this_period >= subscription_monthly_cost:
#      → agent suggests switching to subscription (cheaper for this user)
#   3. If user is on subscription plan AND projected_usage < (subscription_monthly_cost / per_unit_cost):
#      → agent suggests switching to consumption (cheaper for this user)
#   4. Based on user's configured policy (suggest_only, auto_switch, silent):
#      → send AgentMail suggestion OR auto-switch plan OR just log

# New state field needed in users table:
#   billing_period_start (timestamp)
#   billing_period_units_consumed (int)
#   plan (text: 'consumption' | 'subscription' | 'hybrid')
#   plan_policy (text: 'suggest_only' | 'auto_switch' | 'silent')
#   subscription_monthly_cost (real)
#   subscription_included_units (int)
```

This is the **agent intelligence feature** from the design prompt — "I noticed you're using this heavily this week, it would be $5 cheaper to switch to monthly." The logic is simple cost comparison; the clever part is the agent acting on it.

---

### `sdk/locus_drip/notifications.py`

**Current state:** Three templates: `low_credit`, `paused`, `restored`. All framed from a "research agent" perspective (mentions "container" and "context").

**Problems:**
1. Templates are too specific to the research agent demo use case
2. Language is infrastructure-level, not user-friendly
3. Missing the key new template: plan optimization suggestion

**Proposed changes:**

1. Make templates configurable by the SaaS company (they should be able to pass custom templates or at least custom `app_name` and `support_url`)
2. Add plan suggestion template:
```python
"plan_suggestion": {
    "subject": "You could save money this month — want me to handle it?",
    "body": (
        f"Hi {user_first_name},\n\n"
        f"I've been watching your usage of {app_name} this week.\n\n"
        f"At your current pace, you'll spend {consumption_cost_projected:.2f} "
        f"on pay-as-you-go billing.\n"
        f"Your monthly subscription is {subscription_cost:.2f}.\n\n"
        f"Switching to monthly for this period would save you "
        f"{savings:.2f}. Should I handle that?\n\n"
        f"Reply YES and I'll switch your plan automatically.\n"
        f"Reply NO or ignore this to stay on pay-as-you-go.\n\n"
        f"— Drip Agent"
    )
}
```
3. Rename "container" language to service-level language. SaaS customers don't know or care about containers. "Your service has been paused" is correct. "Your container has been hibernated" is not customer-facing language.

---

### `sdk/locus_drip/state.py`

**Current state:** `users` table schema needs additions for hybrid billing.

**Proposed schema additions:**
```sql
ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'consumption';
ALTER TABLE users ADD COLUMN plan_policy TEXT DEFAULT 'suggest_only';
ALTER TABLE users ADD COLUMN subscription_monthly_cost REAL DEFAULT 0.0;
ALTER TABLE users ADD COLUMN subscription_included_units INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN billing_period_start INTEGER;
ALTER TABLE users ADD COLUMN billing_period_units_consumed INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN overage_cost_per_unit REAL DEFAULT 0.0;
```

No changes to existing fields — backward compatible.

**New query needed:**
```python
async def get_billing_period_usage(user_id: str) -> dict:
    """Return usage stats for current billing period."""
    ...

async def increment_units(user_id: str, units: int = 1):
    """Track unit consumption (for subscription tier usage)."""
    ...

async def reset_billing_period(user_id: str):
    """Reset period counters at billing cycle boundary."""
    ...
```

---

### `sdk/locus_drip/exceptions.py`

**Current state:** `DripInsufficientCredits`, `DripUserNotFound`. Fine.

**Add:**
```python
class DripPlanLimitReached(DripException):
    """Raised when a user on a subscription plan hits their included unit cap."""
    pass

class DripPlanSwitchFailed(DripException):
    """Raised when an agent-driven plan switch cannot complete."""
    pass
```

---

### `sdk/locus_drip/lifecycle.py`

**Current state:** Directly calls BWL API using BWL credentials configured by the SDK user.

**Problem:** In the new model, SaaS companies should not have BWL API keys. Drip should own the container infrastructure. BWL calls should go through Drip's own API, not directly from the customer's SDK.

**Proposed change:** This file should remain internally but not be exposed to SDK consumers. The `lifecycle` functions should be called only by Drip's own backend (the `locusmeter` service), not directly by customer code. The SDK should make REST calls to Drip's API (`api.drip.so/provision`, `api.drip.so/hibernate`, etc.) and Drip's backend makes the BWL calls.

This is the **most important architectural change** for the closed-source repositioning. Customer SDK should never touch BWL or PWL APIs directly.

---

### `sdk/locus_drip/wallet.py`

**Current state:** Checks master PayWithLocus wallet balance.

**Problem:** This exposes the PWL API and the concept of a "master wallet" to SDK consumers. In the new model, wallet management is entirely internal to Drip.

**Proposed change:** Remove from public SDK. Keep as internal server-side logic in `locusmeter/`. The SDK has no business knowing about the master wallet.

---

### `locusmeter/main.py`

**Current state:** Contains the full Drip server with all demo, dashboard, and API endpoints.

**Problems:**
1. Demo endpoints (`/demo/drain`, `/demo/topup`, `/demo/reset`) are good for the live demo but must be protected (or removed) in production
2. `/debug/env` is a security risk — exposes API keys in a JSON response
3. The `client` object created at module level uses `bwl_api_key` and `locus_api_key` directly — in the new model the server is Drip's infrastructure, so this is correct, but the naming should reflect that ("drip internal keys", not "customer-facing keys")
4. Model field `topic` in `UserCreate` is research-agent-specific — should be replaced with a generic `metadata: dict = {}` field

**Proposed changes:**
1. Remove or gate `/debug/env` behind auth
2. Rename `topic` field in `UserCreate` to `metadata: dict = {}` 
3. Add auth to demo endpoints (even simple bearer token)
4. Add a `POST /users/{user_id}/plan` endpoint for plan switching

---

### `locusmeter/models.py`

**Current state:**
```python
class UserCreate(BaseModel):
    user_id: str
    email: str
    topic: str                          # research-agent-specific
    initial_balance: float = 1.0
    credit_rate: float = 0.05           # named "credit_rate" — unclear
```

**Proposed:**
```python
class UserCreate(BaseModel):
    user_id: str
    email: str
    metadata: dict = {}                 # generic, not research-specific
    plan: str = "consumption"           # NEW
    initial_balance: float = 0.0
    consumption_unit_cost: float = 0.01 # renamed from credit_rate, more descriptive
    subscription_monthly_cost: float = 0.0   # NEW
    subscription_included_units: int = 0     # NEW
    plan_policy: str = "suggest_only"        # NEW: how agent handles plan switches
```

---

### `locusmeter/webhooks.py`

**Current state:** Handles Locus Checkout webhooks for top-ups. This is correct and should remain largely unchanged.

**Minor change needed:**
- After crediting balance and triggering restore, if the user was on the path to a plan optimization suggestion (e.g., they've been heavy this month), trigger the plan suggestion email at this point. "You've topped up — and you're on track for your heaviest month yet. Want me to switch you to the monthly plan?"

---

### `sdk/examples/minimal_example.py` and `research_agent.py`

**Current state:** Good for demos but framed around the research agent use case.

**Proposed new examples needed:**
1. `examples/ai_saas_integration.py` — AI writing assistant integration (the marquee use case from the design prompt)
2. `examples/hybrid_plan_example.py` — shows how to configure a user with both subscription and consumption options and how the agent switches between them
3. `examples/plan_switching_demo.py` — simulates a user hitting the tier cliff and the agent catching them

Keep the research agent example as `examples/research_agent_demo.py` — it's a good end-to-end demo, just rename it.

---

### `README.md`

**Current state:** Positions Drip as a developer-first infrastructure tool. Good technical depth but wrong audience framing.

**Proposed changes (already partially addressed in new README, but key repositioning):**
1. Open with the B2B2C value proposition, not the developer API
2. The "business plan" section should lead with the SaaS vendor's revenue problem, not Drip's own monetization
3. Remove all language about "running Drip on BuildWithLocus" and "master wallet" — these are internal implementation details
4. Add "Integration Guide" as first technical section (not architecture)
5. Add "Pricing Cliff Explainer" as a standalone section with the User A / User B example

---

## Summary Table

| File | Change Type | Priority | Complexity |
|------|------------|----------|-----------|
| `sdk/locus_drip/client.py` — `DripConfig` | Simplify API surface (hide BWL/PWL) | HIGH | Medium |
| `sdk/locus_drip/client.py` — `provision_user` | Add plan params | HIGH | Low |
| `sdk/locus_drip/client.py` — `start_polling` | Add plan optimization logic | HIGH | High |
| `sdk/locus_drip/notifications.py` | Add plan suggestion template, fix language | HIGH | Low |
| `sdk/locus_drip/state.py` | Add billing period + plan fields to schema | HIGH | Low |
| `sdk/locus_drip/lifecycle.py` | Move to server-only, remove from SDK public surface | MEDIUM | Medium |
| `sdk/locus_drip/wallet.py` | Remove from SDK, keep server-side only | MEDIUM | Low |
| `sdk/locus_drip/exceptions.py` | Add `DripPlanLimitReached`, `DripPlanSwitchFailed` | LOW | Low |
| `sdk/locus_drip/meter.py` | Add `unit`, `label`, `dry_run` params | LOW | Low |
| `locusmeter/models.py` | Rename `topic` → `metadata`, add plan fields | MEDIUM | Low |
| `locusmeter/main.py` | Remove `/debug/env`, gate demo endpoints, add plan endpoint | MEDIUM | Low |
| `locusmeter/webhooks.py` | Trigger plan suggestion on top-up | LOW | Low |
| `sdk/examples/` | New AI SaaS and hybrid plan examples | MEDIUM | Low |
| `README.md` | Reframe for B2B2C, remove internal infrastructure details | HIGH | Low |

---

## What NOT to Change

1. **The `@meter` decorator interface** — correct as-is, only additive changes
2. **The polling loop architecture** — sound design, only extend it
3. **HMAC webhook verification** — correctly implemented, keep
4. **SQLite/Postgres state layer** — correct design, only add columns
5. **The `DripInsufficientCredits` exception** — exactly right, keep
6. **The BWL container provision/hibernate/restore logic** — technically correct, just move it server-side so customers don't see it

---

## Implementation Order (for when you're ready)

1. Add plan fields to the database schema (`state.py`) — no risk, backward compatible
2. Update `UserCreate` model and `/provision` endpoint to accept plan params
3. Add plan suggestion notification template to `notifications.py`
4. Add plan optimization logic to `start_polling` in `client.py`
5. Abstract `DripConfig` to single `api_key` (requires Drip's own API proxy layer to be built first)
6. Move `lifecycle.py` and `wallet.py` to server-side only
7. Update examples with AI SaaS use case
8. Update README
