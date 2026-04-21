"""Checkout webhook handling and session creation.

Handles:
- Creating Locus Checkout sessions for credit top-ups
- Verifying webhook HMAC signatures
- Processing checkout.session.paid events
- Triggering restore flow on successful payment
"""

import os
import json
import hmac
import hashlib
import httpx

from fastapi import Request, HTTPException

from locusmeter import db
from locusmeter.lifecycle import restore

LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")
LOCUS_API_BASE = os.getenv("LOCUS_API_BASE", "https://beta-api.paywithlocus.com/api")


def verify_hmac(body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 webhook signature.

    The X-Signature-256 header format is: sha256={hex_digest}
    """
    if not signature.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


async def create_checkout_session(user_id: str, amount: float) -> dict:
    """Create a Locus Checkout session for a credit top-up.

    Returns the session ID and checkout URL for the user.
    The webhook URL points back to our /webhook/checkout-paid endpoint.
    """
    user = await db.get_user(user_id)
    if not user:
        raise HTTPException(404, f"User {user_id} not found")

    # Our own URL for the webhook callback
    drip_url = os.getenv("DRIP_URL", "http://localhost:8080")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Use the Locus Agent SDK pattern via direct API call
            resp = await client.post(
                f"{LOCUS_API_BASE}/checkout/sessions",
                headers={
                    "Authorization": f"Bearer {LOCUS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "amount": str(amount),
                    "description": f"Drip credit top-up for {user_id}",
                    "webhookUrl": f"{drip_url}/webhook/checkout-paid",
                    "metadata": {
                        "user_id": user_id,
                        "type": "credit_topup",
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()

            session_id = data.get("id", data.get("sessionId", ""))
            checkout_url = data.get("checkoutUrl",
                                   f"https://checkout.paywithlocus.com/{session_id}")
            webhook_secret = data.get("webhookSecret", "")

            # Store in our DB for HMAC verification later
            await db.create_checkout_session(
                session_id=session_id,
                user_id=user_id,
                amount=amount,
                webhook_secret=webhook_secret,
            )

            await db.add_log(user_id,
                            f"checkout session created — {amount:.2f} USDC top-up")

            return {
                "session_id": session_id,
                "checkout_url": checkout_url,
                "amount": amount,
            }

    except httpx.HTTPStatusError as e:
        await db.add_log(user_id,
                        f"checkout session creation failed: {e.response.status_code}")
        raise HTTPException(500, f"Failed to create checkout session: {str(e)}")


async def handle_checkout_paid(request: Request) -> dict:
    """Process the checkout.session.paid webhook from Locus.

    1. Verify HMAC signature
    2. Extract user_id and amount from metadata
    3. Credit the user's balance
    4. Trigger restore if user was paused
    5. Send confirmation via AgentMail
    """
    body = await request.body()
    sig = request.headers.get("X-Signature-256", "")
    session_id = request.headers.get("X-Session-Id", "")
    event_type = request.headers.get("X-Webhook-Event", "")

    # Look up the webhook secret for this session
    session = await db.get_checkout_session(session_id)
    if not session:
        # Fallback: try to parse the body for session info
        try:
            data = json.loads(body)
            session_id = data.get("data", {}).get("sessionId", session_id)
            session = await db.get_checkout_session(session_id)
        except json.JSONDecodeError:
            pass

    if not session:
        raise HTTPException(400, "Unknown checkout session")

    # Verify HMAC signature
    webhook_secret = session["webhook_secret"]
    if webhook_secret and sig:
        if not verify_hmac(body, sig, webhook_secret):
            await db.add_log(session["user_id"],
                            "webhook signature verification FAILED — rejecting")
            raise HTTPException(400, "Invalid webhook signature")

    # Parse payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON payload")

    event = payload.get("event", event_type)
    if event != "checkout.session.paid":
        # Not a payment event — acknowledge but don't process
        return {"ok": True, "event": event, "action": "ignored"}

    # Extract payment details
    payment_data = payload.get("data", {})
    user_id = payment_data.get("metadata", {}).get("user_id", session["user_id"])
    amount = float(payment_data.get("amount", session["amount"]))

    # Credit the user's balance
    await db.credit_balance(user_id, amount)
    await db.add_log(user_id,
                    f"💰 payment received — {amount:.2f} USDC credited to balance")

    # Check if user was paused → trigger restore
    user = await db.get_user(user_id)
    if user and user.get("status") == "paused":
        await db.add_log(user_id, "user was paused — triggering auto-restore")
        try:
            await restore(user_id)
        except Exception as e:
            await db.add_log(user_id, f"auto-restore failed: {str(e)[:100]}")

    # Send confirmation via AgentMail
    try:
        from locusmeter.agent import send_agentmail_warning
        if user:
            # Refresh user data
            user = await db.get_user(user_id)
            await send_agentmail_warning(user, "restored")
    except Exception as e:
        await db.add_log(user_id, f"confirmation email failed: {str(e)[:50]}")

    return {"ok": True}
