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
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from locusmeter import db
from locusmeter.models import (
    UserCreate, UserResponse, DebitRequest,
    CheckoutSessionCreate,
)

load_dotenv()

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup: init DB tables and start polling loop
    await db.init_tables()
    await db.add_log(None, "Drip agent started — initializing systems")

    # Import here to avoid circular imports
    from locusmeter.agent import start_polling_loop
    polling_task = asyncio.create_task(start_polling_loop())

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
    from locusmeter.lifecycle import provision

    # Check if user already exists
    existing = await db.get_user(req.user_id)
    if existing:
        raise HTTPException(400, f"User {req.user_id} already exists")

    # Create user in SQLite
    user = await db.create_user(
        user_id=req.user_id,
        email=req.email,
        topic=req.topic,
        initial_balance=req.initial_balance,
        credit_rate=req.credit_rate,
    )
    await db.add_log(req.user_id,
                     f"new user registered — topic: '{req.topic}', "
                     f"balance: {req.initial_balance:.2f} USDC")

    # Provision BWL container
    try:
        result = await provision(req.user_id)
        await db.add_log(req.user_id,
                         f"container provisioned — service_id: {result.get('service_id', 'pending')}")
        return {"ok": True, "user": user, "provision": result}
    except Exception as e:
        # In local/demo mode, BWL might not be available — still set user active
        await db.add_log(req.user_id,
                         f"BWL provision failed (continuing in local mode): {str(e)[:100]}")
        await db.set_status(req.user_id, "active")
        return {"ok": True, "user": user, "provision": {"local_mode": True, "error": str(e)[:100]}}


@app.post("/teardown")
async def teardown_user(user_id: str):
    """Scale user's container to zero."""
    from locusmeter.lifecycle import teardown

    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(404, f"User {user_id} not found")

    try:
        await teardown(user_id)
        return {"ok": True, "status": "paused"}
    except Exception as e:
        await db.add_log(user_id, f"teardown failed: {str(e)}")
        raise HTTPException(500, f"Teardown failed: {str(e)}")


@app.post("/restore")
async def restore_user(user_id: str):
    """Scale user's container back up."""
    from locusmeter.lifecycle import restore

    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(404, f"User {user_id} not found")

    try:
        await restore(user_id)
        return {"ok": True, "status": "restoring"}
    except Exception as e:
        await db.add_log(user_id, f"restore failed: {str(e)}")
        raise HTTPException(500, f"Restore failed: {str(e)}")


# ---------- Internal Debit (called by research container) ----------

@app.post("/internal/debit")
async def internal_debit(req: DebitRequest):
    """Research container calls this to drain credits after each cycle."""
    from locusmeter.billing import deduct_credits

    user = await db.get_user(req.user_id)
    if not user:
        raise HTTPException(404, f"User {req.user_id} not found")

    if user["balance_usdc"] <= 0:
        raise HTTPException(402, "Insufficient credits — container should pause")

    await deduct_credits(req.user_id, req.amount, req.label)
    updated = await db.get_user(req.user_id)
    return {"ok": True, "remaining_balance": updated["balance_usdc"]}


# ---------- Logs ----------

@app.get("/logs")
async def get_logs():
    """Last 50 agent log entries (HTMX polls every 2s)."""
    logs = await db.get_logs(50)
    return logs


# ---------- Dashboard (HTMX UI) ----------

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


# ---------- Demo Controls ----------

_demo_tasks = {}

@app.post("/demo/drain")
async def demo_drain():
    """Start a compressed demo drain cycle.

    Simulates rapid credit depletion on all active users to
    demonstrate the full lifecycle (active → warning → teardown)
    within ~2 minutes.
    """
    from locusmeter.billing import deduct_credits

    users = await db.get_active_users()
    if not users:
        raise HTTPException(400, "No active users to drain")

    async def drain_loop(user_id: str, credit_rate: float):
        """Drain credits from a user at compressed rate."""
        demo_rate = credit_rate * 4  # 4x speed for demo
        await db.add_log(user_id, f"🎮 demo drain started — {demo_rate:.4f} USDC every 5s")
        while True:
            user = await db.get_user(user_id)
            if not user or user["balance_usdc"] <= 0 or user["status"] == "paused":
                await db.add_log(user_id, "🎮 demo drain complete")
                break
            await deduct_credits(user_id, demo_rate, "demo_drain")
            await asyncio.sleep(5)

    for user in users:
        task = asyncio.create_task(drain_loop(user["user_id"], user["credit_rate"]))
        _demo_tasks[user["user_id"]] = task

    await db.add_log(None, f"🎮 demo drain started for {len(users)} user(s)")
    return {"ok": True, "draining": [u["user_id"] for u in users]}


@app.post("/demo/topup")
async def demo_topup():
    """Simulate a top-up for all paused users."""
    users = await db.get_all_users()
    topped_up = []

    for user in users:
        if user["status"] == "paused":
            amount = user.get("initial_balance", 1.0)
            await db.credit_balance(user["user_id"], amount)
            await db.add_log(user["user_id"],
                            f"🎮 demo top-up — {amount:.2f} USDC added")
            topped_up.append(user["user_id"])

    if not topped_up:
        # Top up all users regardless of status
        for user in users:
            amount = user.get("initial_balance", 1.0)
            await db.credit_balance(user["user_id"], amount)
            await db.add_log(user["user_id"],
                            f"🎮 demo top-up — {amount:.2f} USDC added")
            topped_up.append(user["user_id"])

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
            await db.add_log(user["user_id"],
                            f"research complete — {result.get('sources_used', 0)} sources, "
                            f"{result.get('budget_mode', 'normal')} mode")

            # Deduct cost
            from locusmeter.billing import deduct_credits
            cost = result.get("cost_estimate", 0.05)
            await deduct_credits(user["user_id"], cost,
                               f"research_cycle ({result.get('sources_used', 0)} sources)")
        except Exception as e:
            await db.add_log(user["user_id"],
                            f"research failed: {str(e)[:100]}")

    asyncio.create_task(_do_research())
    return {"ok": True, "user_id": user["user_id"]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("locusmeter.main:app", host="0.0.0.0", port=port, reload=True)

