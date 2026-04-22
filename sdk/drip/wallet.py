import httpx

async def check_master_wallet_balance(api_base: str, api_key: str) -> float:
    """Check the master Drip wallet balance via PayWithLocus API.
    
    If master wallet is drained, all user API calls fail silently.
    We check periodically to log warnings.
    """
    try:
        if not api_key:
            return -1.0

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{api_base}/pay/balance",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            d = data.get("data", {})
            usdc = float(d.get("usdc_balance", "0"))
            promo = float(d.get("promo_credit_balance", "0"))
            return usdc + promo
    except Exception as e:
        print(f"WARNING: master wallet balance check failed: {e}")
        return -1.0
