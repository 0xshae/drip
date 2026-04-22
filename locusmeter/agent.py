"""Agent polling loop — the brain of Drip.

Runs as an asyncio background task. Every POLL_INTERVAL_SECONDS:
1. Checks all active users' credit balances
2. Sends low-credit warnings at < 20%
3. Triggers teardown when balance hits 0
4. Detects top-ups on paused users and triggers restore
5. Periodically checks master wallet balance

All decisions are logged to the agent_logs table for the live demo UI.
"""

import asyncio
import os
import httpx

from locusmeter import db
from locusmeter.lifecycle import teardown, restore
from locusmeter.billing import check_master_wallet_balance

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")
LOCUS_API_BASE = os.getenv("LOCUS_API_BASE", "https://beta-api.paywithlocus.com/api")


async def log_decision(user_id: str, message: str):
    """Write an agent reasoning entry to the log table."""
    await db.add_log(user_id, message)


async def send_agentmail_warning(user: dict, warning_type: str):
    """Send a warning email via AgentMail.

    Types: 'low_credit', 'paused', 'restored'
    """
    inbox = os.getenv("AGENTMAIL_INBOX", "") or "shagun@agentmail.to"
    api_key = os.getenv("LOCUS_API_KEY", "")
    if not api_key:
        await log_decision(user["user_id"],
                          f"AgentMail skip — no API key (would send: {warning_type})")
        return

    templates = {
        "low_credit": {
            "subject": f"⚠️ Low credits — {user.get('balance_usdc', 0):.2f} USDC remaining",
            "body": (
                f"Your research agent is running low on credits.\n\n"
                f"Remaining balance: {user.get('balance_usdc', 0):.2f} USDC\n"
                f"Topic: {user.get('topic', 'N/A')}\n\n"
                f"Top up to keep your research running."
            ),
        },
        "paused": {
            "subject": "⏸️ Your research container has been paused",
            "body": (
                f"Your research agent ran out of credits and has been paused.\n\n"
                f"Topic: {user.get('topic', 'N/A')}\n"
                f"Your research data is safe — it's stored in managed Postgres.\n\n"
                f"Recharge your credits to bring your agent back online."
            ),
        },
        "restored": {
            "subject": "🔄 Your research agent is back online!",
            "body": (
                f"Your credits have been replenished and your research agent "
                f"is waking up.\n\n"
                f"Balance: {user.get('balance_usdc', 0):.2f} USDC\n"
                f"Topic: {user.get('topic', 'N/A')}\n\n"
                f"Research will resume shortly."
            ),
        },
    }

    template = templates.get(warning_type, templates["low_credit"])

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{LOCUS_API_BASE}/x402/agentmail-send-message",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": user.get("email", ""),
                    "from": inbox,
                    "subject": template["subject"],
                    "body": template["body"],
                },
            )
            if resp.status_code < 300:
                await log_decision(user["user_id"],
                                  f"sent {warning_type} notification via AgentMail")
            else:
                await log_decision(user["user_id"],
                                  f"AgentMail send failed ({resp.status_code}): {resp.text[:100]}")
    except Exception as e:
        await log_decision(user["user_id"],
                          f"AgentMail error: {str(e)[:100]}")


async def polling_loop():
    """Main agent polling loop. Runs forever, checking all users."""
    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            users = await db.get_active_users()

            for user in users:
                user_id = user["user_id"]
                balance = user["balance_usdc"]
                initial = user["initial_balance"]
                status = user["status"]

                pct = balance / initial if initial > 0 else 0

                await log_decision(user_id,
                                  f"checking balance... {balance:.2f} USDC remaining "
                                  f"({pct*100:.0f}% of initial)")

                # Zero balance → teardown
                if pct <= 0 and status == "active":
                    await teardown(user_id)
                    await send_agentmail_warning(user, "paused")

                # Low credit warning (< 20%)
                elif pct < 0.2 and status == "active":
                    await db.set_status(user_id, "low_credit")
                    await log_decision(user_id,
                                      f"⚠️ low credit warning — {balance:.2f} USDC "
                                      f"({pct*100:.0f}% remaining)")
                    await send_agentmail_warning(user, "low_credit")

            # Also check paused users for top-ups (restore trigger fallback)
            all_users = await db.get_all_users()
            for user in all_users:
                if user["status"] == "paused" and user["balance_usdc"] > 0:
                    await log_decision(user["user_id"],
                                      f"detected top-up on paused user — "
                                      f"balance: {user['balance_usdc']:.2f} USDC")
                    await restore(user["user_id"])
                    await send_agentmail_warning(user, "restored")

            # Periodic master wallet check (every 10 cycles)
            if cycle_count % 10 == 0:
                master_balance = await check_master_wallet_balance()
                if master_balance >= 0:
                    await log_decision(None,
                                      f"master wallet audit: {master_balance:.2f} USDC")
                    if master_balance < 1.0:
                        await log_decision(None,
                                          "⚠️ CRITICAL: master wallet below $1.00 — "
                                          "all user API calls may fail!")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Critical gap from eng review: crash-proof the loop
            await db.add_log(None,
                            f"polling loop error (recovering): {str(e)[:200]}")

        await asyncio.sleep(POLL_INTERVAL)


async def start_polling_loop():
    """Entry point for the background polling task."""
    await log_decision(None, f"agent loop started — polling every {POLL_INTERVAL}s")
    await polling_loop()
