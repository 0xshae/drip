"""Drip — Agent-Native SaaS Billing Layer.

FastAPI application that manages credit-based container lifecycle:
- Provisions per-user containers on BuildWithLocus
- Monitors credit balances via polling loop
- Tears down containers when credits hit zero
- Auto-restores when credits are replenished
"""

import asyncio
import os
import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from locusmeter import db
from locusmeter.auth import (
    generate_magic_token, generate_account_id, set_session_cookie,
    clear_session_cookie, get_current_user, SESSION_MAX_AGE
)
from locusmeter.models import (
    UserCreate, UserResponse, DebitRequest,
    CheckoutSessionCreate,
)

import sys
sys.path.append(str(Path(__file__).parent.parent / "sdk"))
from locus_drip import DripClient, DripConfig

client = DripClient(DripConfig(
    locus_api_key=os.environ.get("LOCUS_API_KEY", ""),
    bwl_api_key=os.environ.get("BWL_API_KEY", ""),
    agentmail_inbox=os.environ.get("AGENTMAIL_INBOX", "ricc@agentmail.to"),
))

# Request models for auth
class MagicLinkRequest(BaseModel):
    email: str
    company_name: str = None

class OnboardRequest(BaseModel):
    bwl_api_key: str
    webhook_url: str = None
    company_name: str = None

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup: init DB tables and start polling loop
    await db.init_tables()
    await db.add_log(None, "Drip agent started — initializing systems")

    # Start the SDK polling loop
    polling_task = asyncio.create_task(client.start_polling())

    await db.add_log(None, "polling loop active — monitoring all user balances")
    yield

    # Shutdown
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await db.close_db()


app = FastAPI(
    title="Drip",
    description="Agent-Native SaaS Billing Layer",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------- Health ----------

@app.get("/health")
async def health():
    """BWL health check — must return 200."""
    return {"status": "ok"}


# ---------- Provision / Teardown / Restore ----------

@app.post("/provision")
async def provision_user(req: UserCreate):
    """Create a new user and spin up their BWL container."""
    try:
        # Handle backward compatibility for research agent
        metadata = req.metadata or {}
        if req.topic:
            metadata["topic"] = req.topic
        
        # Determine consumption cost
        unit_cost = req.consumption_unit_cost
        if req.credit_rate is not None:
            unit_cost = req.credit_rate

        user = await client.provision_user(
            user_id=req.user_id,
            email=req.email,
            plan=req.plan,
            initial_balance=req.initial_balance,
            consumption_unit_cost=unit_cost,
            subscription_cost=req.subscription_monthly_cost,
            included_units=req.subscription_included_units,
            container_image=os.getenv("GHCR_IMAGE", "ghcr.io/0xshae/locusmeter-research:latest"),
            metadata=metadata
        )
        return {"ok": True, "user": user}
    except Exception as e:
        raise HTTPException(400, f"Provisioning failed: {e}")


@app.post("/teardown")
async def teardown_user(user_id: str):
    """Scale user's container to zero."""
    try:
        await client.hibernate(user_id)
        return {"ok": True, "status": "paused"}
    except Exception as e:
        raise HTTPException(500, f"Teardown failed: {e}")


@app.post("/restore")
async def restore_user(user_id: str):
    """Scale user's container back up."""
    try:
        await client.restore(user_id)
        return {"ok": True, "status": "restoring"}
    except Exception as e:
        raise HTTPException(500, f"Restore failed: {e}")


# ---------- Internal Debit (called by research container) ----------

@app.post("/internal/debit")
async def internal_debit(req: DebitRequest):
    """Research container calls this to drain credits after each cycle."""
    try:
        await client.debit(req.user_id, req.amount, req.label)
        user = await client.get_user(req.user_id)
        return {"ok": True, "remaining_balance": user["balance_usdc"]}
    except Exception as e:
        raise HTTPException(402, f"Insufficient credits: {e}")


# ---------- Logs ----------

@app.get("/logs")
async def get_logs(after_id: int = 0):
    """Agent log entries. If after_id is set, return only new entries (for smooth streaming)."""
    if after_id > 0:
        logs = await db.get_logs_after(after_id, limit=50)
    else:
        logs = await db.get_logs(50)
    return logs


# ---------- Live State (for JS poller) ----------

@app.get("/state")
async def get_state():
    """Live state for dashboard JS poller — users + stats, no page reload."""
    users = await db.get_all_users()
    active = len([u for u in users if u["status"] in ("active", "low_credit")])
    paused = len([u for u in users if u["status"] == "paused"])
    return {
        "users": users,
        "stats": {
            "active": active,
            "paused": paused,
            "total": len(users),
        }
    }


# ---------- Dashboard (HTMX UI) ----------

@app.post("/users/{user_id}/plan")
async def update_user_plan(user_id: str, plan: str):
    """Update a user's billing plan."""
    try:
        user = await client.get_user(user_id)
        # Update user in DB
        db_conn = await db.get_db()
        await db_conn.execute("UPDATE users SET plan = ? WHERE user_id = ?", (plan, user_id))
        await db_conn.commit()
        await db.add_log(user_id, f"plan updated to: {plan}")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/debug/config")
async def debug_config():
    """Returns safe configuration info."""
    return {
        "poll_interval": client.config.poll_interval_seconds,
        "mock_drain": client.config.mock_drain,
        "api_base": client.config.locus_api_base
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main HTMX dashboard."""
    users = await db.get_all_users()
    logs = await db.get_logs(20)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "users": users,
        "logs": logs,
    })


# ---------- Auth Routes ----------

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Sign up page with magic link form."""
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/auth/magic")
async def create_magic_link_endpoint(req: MagicLinkRequest):
    """Create a magic link and "send" it (logs to console for demo)."""
    import time
    from cryptography.fernet import Fernet

    # Generate token
    token = generate_magic_token(req.email)
    expires_at = int(time.time()) + 900  # 15 minutes

    await db.create_magic_token(token, req.email, expires_at)

    # In demo mode: log the link instead of sending email
    magic_url = f"/auth/verify?token={token}"
    print(f"\n{'='*60}")
    print(f"MAGIC LINK for {req.email}")
    print(f"URL: {magic_url}")
    print(f"{'='*60}\n")

    return {"ok": True, "message": "Check your email (logged to console for demo)"}


@app.get("/auth/verify")
async def verify_magic_link(request: Request, token: str):
    """Verify magic link and create session."""
    magic = await db.get_magic_token(token)
    if not magic:
        raise HTTPException(400, "Invalid or expired magic link")

    email = magic["email"]

    # Check if account exists, create if not
    account = await db.get_saas_account_by_email(email)
    if not account:
        account_id = generate_account_id()
        account = await db.create_saas_account(account_id, email)

        # Generate demo data for new account
        await _create_demo_data(account_id)

    account_id = account["account_id"]
    await db.mark_magic_token_used(token, account_id)

    # Create session and redirect
    response = RedirectResponse(
        url="/onboard" if not account.get("is_onboarded") else "/admin/dashboard",
        status_code=302
    )
    set_session_cookie(response, email, account_id)
    return response


@app.get("/onboard", response_class=HTMLResponse)
async def onboard_page(request: Request):
    """Onboarding page to connect BWL."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/signup", status_code=302)

    account = await db.get_saas_account(user["account_id"])
    return templates.TemplateResponse("onboard.html", {
        "request": request,
        "account": account,
    })


@app.post("/onboard")
async def complete_onboarding(request: Request, req: OnboardRequest):
    """Complete onboarding with BWL credentials."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    # In production: encrypt the API key
    # For demo: store as-is (it's demo data anyway)
    encrypted_key = req.bwl_api_key  # TODO: Fernet encryption

    await db.update_saas_onboarding(
        user["account_id"],
        company_name=req.company_name,
        bwl_api_key_encrypted=encrypted_key,
        webhook_url=req.webhook_url,
    )

    return {"ok": True}


@app.post("/onboard/skip")
async def skip_onboarding(request: Request):
    """Skip onboarding and go to dashboard."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/signup", status_code=302)

    await db.update_saas_onboarding(user["account_id"])
    return RedirectResponse(url="/admin/dashboard", status_code=302)


@app.get("/logout")
async def logout():
    """Clear session and redirect to home."""
    response = RedirectResponse(url="/", status_code=302)
    clear_session_cookie(response)
    return response


async def _create_demo_data(account_id: str):
    """Generate synthetic end-users for a new SaaS account."""
    import random

    demo_users = [
        {"id": f"user_{generate_account_id()[-8:]}", "email": "sarah@example.com", "topic": "Cloud infrastructure research"},
        {"id": f"user_{generate_account_id()[-8:]}", "email": "mike@example.com", "topic": "AI model comparison"},
        {"id": f"user_{generate_account_id()[-8:]}", "email": "alex@example.com", "topic": "Market analysis"},
    ]

    for demo in demo_users:
        balance = round(random.uniform(0.5, 5.0), 2)
        status = random.choice(["active", "active", "low_credit", "paused"])
        await db.create_user(
            user_id=demo["id"],
            email=demo["email"],
            metadata={"topic": demo["topic"]},
            initial_balance=balance,
            consumption_unit_cost=0.05,
        )
        await db.link_user_to_saas(demo["id"], account_id)
        if status != "active":
            await db.set_status(demo["id"], status)
        await db.add_log(demo["id"], f"Demo user created with ${balance:.2f} balance")


# ---------- Checkout ----------

@app.post("/checkout/create")
async def create_checkout(req: CheckoutSessionCreate):
    """Create a Locus Checkout session for top-up."""
    from locusmeter.webhooks import create_checkout_session
    result = await create_checkout_session(req.user_id, req.amount)
    return result


# ---------- Webhook ----------

@app.post("/webhook/checkout-paid")
async def webhook_checkout_paid(request: Request):
    """Handle Locus Checkout webhook for successful payment."""
    from locusmeter.webhooks import handle_checkout_paid
    return await handle_checkout_paid(request)


# ---------- Users list ----------

@app.get("/users")
async def list_users():
    """List all users and their status."""
    users = await db.get_all_users()
    return {"users": users}


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get a single user's state."""
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(404, f"User {user_id} not found")
    return user


# ---------- Recharge Page ----------

@app.get("/recharge", response_class=HTMLResponse)
async def recharge_page(request: Request):
    """Credit recharge page with Locus Checkout integration."""
    return templates.TemplateResponse("recharge.html", {"request": request})


# ---------- Research Results ----------

@app.get("/research/latest")
async def research_latest():
    """Get the most recent research result for the findings panel."""
    results = await db.get_latest_research(limit=1)
    if not results:
        return {"result": None}
    r = results[0]
    # Parse sources_json back to list
    import json as _json
    try:
        sources = _json.loads(r.get("sources_json", "[]"))
    except Exception:
        sources = []
    return {
        "result": {
            "user_id": r["user_id"],
            "topic": r["topic"],
            "digest": r["digest"],
            "sources": sources,
            "budget_mode": r["budget_mode"],
            "sources_used": r["sources_used"],
            "created_at": r["created_at"],
        }
    }


# ---------- Demo Controls ----------

_demo_tasks = {}

@app.post("/demo/drain")
async def demo_drain():
    """Start a compressed demo drain cycle.

    Simulates rapid credit depletion on all active users to
    demonstrate the full lifecycle (active → warning → teardown)
    within ~2 minutes. Triggers low-credit warnings and teardown inline.
    """
    from locusmeter.billing import deduct_credits
    from locusmeter.lifecycle import teardown
    from locusmeter.agent import send_agentmail_warning

    users = await db.get_active_users()
    if not users:
        raise HTTPException(400, "No active users to drain")

    async def drain_loop(user_id: str, credit_rate: float, initial_balance: float):
        """Drain credits from a user at compressed rate with lifecycle events."""
        demo_rate = credit_rate * 4  # 4x speed for demo
        warned = False
        await db.add_log(user_id, f"🎮 demo drain started — {demo_rate:.4f} USDC every 5s")
        while True:
            user = await db.get_user(user_id)
            if not user or user["status"] == "paused":
                await db.add_log(user_id, "🎮 demo drain complete")
                break

            balance = user["balance_usdc"]
            if balance <= 0:
                # Trigger teardown
                await db.add_log(user_id,
                    "💀 credits exhausted — triggering container teardown")
                await teardown(user_id)
                await send_agentmail_warning(user, "paused")
                await db.add_log(user_id, "🎮 demo drain complete")
                break

            pct = balance / initial_balance if initial_balance > 0 else 0

            # Low credit warning at 20% (Fix 4)
            if pct < 0.2 and not warned and user["status"] == "active":
                warned = True
                await db.set_status(user_id, "low_credit")
                await db.add_log(user_id,
                    f"⚠️ LOW CREDIT WARNING — {balance:.4f} USDC "
                    f"({pct*100:.0f}% remaining) — switching to budget mode")
                await send_agentmail_warning(user, "low_credit")

            await deduct_credits(user_id, demo_rate, "demo_drain")
            await asyncio.sleep(5)

    for user in users:
        task = asyncio.create_task(
            drain_loop(user["user_id"], user["credit_rate"], user["initial_balance"])
        )
        _demo_tasks[user["user_id"]] = task

    await db.add_log(None, f"🎮 demo drain started for {len(users)} user(s)")
    return {"ok": True, "draining": [u["user_id"] for u in users]}


@app.post("/demo/topup")
async def demo_topup():
    """Simulate a top-up: reset balance and restore status immediately."""
    from locusmeter.lifecycle import restore

    users = await db.get_all_users()
    topped_up = []

    for user in users:
        user_id = user["user_id"]
        amount = user.get("initial_balance", 1.0)

        # Fix 7: Use set_balance for absolute reset
        await db.set_balance(user_id, amount)

        # Fix 6: Immediately set status to active (don't wait for poller)
        if user["status"] in ("paused", "low_credit", "restoring"):
            await db.set_status(user_id, "active")
            await db.add_log(user_id,
                f"💰 demo top-up — balance reset to {amount:.2f} USDC — service restored")
        else:
            await db.add_log(user_id,
                f"💰 demo top-up — balance reset to {amount:.2f} USDC")

        topped_up.append(user_id)

    return {"ok": True, "topped_up": topped_up}


@app.post("/demo/research")
async def demo_research():
    """Trigger a research cycle for the first active user."""
    users = await db.get_active_users()
    if not users:
        raise HTTPException(400, "No active users to run research on")

    user = users[0]
    await db.add_log(user["user_id"],
                    f"🔬 manual research trigger — topic: '{user['topic']}'")

    # Run research in background
    async def _do_research():
        try:
            from research.digest import run_research_cycle
            result = await run_research_cycle(
                topic=user["topic"],
                balance=user["balance_usdc"],
                initial_balance=user["initial_balance"],
                user_email=user.get("email", ""),
            )

            sources_used = result.get("sources_used", 0)
            budget_mode = result.get("budget_mode", "normal")
            digest = result.get("digest", "")

            await db.add_log(user["user_id"],
                            f"📊 research complete — {sources_used} sources, "
                            f"{budget_mode} mode")

            # Fix 3: Store research result for findings panel
            import json as _json
            sources_data = result.get("sources", [])
            await db.save_research_result(
                user_id=user["user_id"],
                topic=user["topic"],
                digest=digest,
                sources_json=_json.dumps(sources_data) if sources_data else "[]",
                budget_mode=budget_mode,
                sources_used=sources_used,
            )

            # Deduct cost
            from locusmeter.billing import deduct_credits
            cost = result.get("cost_estimate", 0.05)
            await deduct_credits(user["user_id"], cost,
                               f"research_cycle ({sources_used} sources)")
        except Exception as e:
            await db.add_log(user["user_id"],
                            f"research failed: {str(e)[:100]}")

    asyncio.create_task(_do_research())
    return {"ok": True, "user_id": user["user_id"]}


@app.post("/demo/reset")
async def demo_reset():
    """Reset the demo — clear all users and logs for a fresh start."""
    users = await db.get_all_users()
    deleted = []
    for user in users:
        await db.delete_user(user["user_id"])
        deleted.append(user["user_id"])

    await db.clear_logs()
    await db.add_log(None, "🔄 demo reset — all users and logs cleared")
    return {"ok": True, "deleted_users": deleted}


# ---------- SaaS Admin Dashboard ----------

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def saas_dashboard(request: Request):
    """SaaS company dashboard showing their metrics and customer overview."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/signup", status_code=302)

    account = await db.get_saas_account(user["account_id"])
    if not account:
        raise HTTPException(404, "Account not found")

    # Get this account's end users
    users = await db.get_users_by_saas_account(user["account_id"])

    # Calculate metrics
    active_users = [u for u in users if u["status"] in ("active", "low_credit")]
    paused_users = [u for u in users if u["status"] == "paused"]

    total_revenue = sum(u["initial_balance"] - u["balance_usdc"] for u in users)
    total_credits = sum(u["balance_usdc"] for u in users)

    # Mock tier-cliff saves (in real version, track these as events)
    saves = [
        {"user_id": "user_8472", "action": "Pro → Pay-as-you-go", "saved": 34},
        {"user_id": "user_1923", "action": "Team → Enterprise", "saved": 127},
    ] if len(users) > 2 else []

    return templates.TemplateResponse("saas_dashboard.html", {
        "request": request,
        "account": account,
        "users": users,
        "metrics": {
            "total_revenue": round(total_revenue, 2),
            "active_count": len(active_users),
            "paused_count": len(paused_users),
            "total_credits": round(total_credits, 2),
            "at_risk": len([u for u in users if u["status"] == "low_credit"]),
        },
        "saves": saves,
    })


@app.get("/admin/api-keys", response_class=HTMLResponse)
async def api_keys_page(request: Request):
    """Page to manage API keys."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/signup", status_code=302)

    return templates.TemplateResponse("api_keys.html", {
        "request": request,
        "api_key": f"drip_{user['account_id']}_demo",
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("locusmeter.main:app", host="0.0.0.0", port=port, reload=True)

