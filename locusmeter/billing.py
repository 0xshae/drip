"""Credit billing and drain logic.

Supports MOCK_DRAIN mode for development (just decrements SQLite,
no real API calls). In production, credits are deducted after each
research cycle via the /internal/debit endpoint.
"""

import os

from locusmeter import db

MOCK_DRAIN = os.getenv("MOCK_DRAIN", "true").lower() == "true"


async def deduct_credits(user_id: str, amount: float, label: str):
    """Deduct credits from a user's balance.

    In real mode, credits already left the master wallet when the
    wrapped API call was made. We just decrement the SQLite ledger.
    In mock mode, same behavior — SQLite only, no real API costs.
    """
    if not MOCK_DRAIN:
        # Real mode: the Locus wrapped API already charged the master wallet.
        # We're just tracking it in our local ledger.
        pass

    await db.deduct_balance(user_id, amount)
    await db.add_log(user_id, f"deducted {amount:.4f} USDC ({label})")


async def check_master_wallet_balance() -> float:
    """Check the master Drip wallet balance via PayWithLocus API.

    Critical gap from eng review: if master wallet is drained,
    all user API calls fail silently. We check periodically.
    """
    import httpx

    locus_api_key = os.getenv("LOCUS_API_KEY", "")
    api_base = os.getenv("LOCUS_API_BASE", "https://beta-api.paywithlocus.com/api")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{api_base}/pay/balance",
                headers={"Authorization": f"Bearer {locus_api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            balance = float(data.get("data", {}).get("balance", "0"))
            return balance
    except Exception as e:
        await db.add_log(None, f"WARNING: master wallet balance check failed: {e}")
        return -1.0
