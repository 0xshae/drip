import httpx
from typing import Optional

async def send_agentmail_warning(
    locus_api_base: str,
    locus_api_key: str,
    agentmail_inbox: str,
    user_id: str,
    user_email: str,
    balance_usdc: float,
    warning_type: str,
    metadata: Optional[dict] = None
) -> bool:
    """Send a notification email via AgentMail.
    Returns True if sent, False otherwise.
    """
    if not locus_api_key or not agentmail_inbox:
        return False
        
    fallback_email = user_email if user_email else "shagun.prasad28@gmail.com"
    topic = metadata.get("topic", "N/A") if metadata else "N/A"

    templates = {
        "low_credit": {
            "subject": f"⚠️ Low credits — {balance_usdc:.2f} USDC remaining",
            "body": (
                f"Your container is running low on credits.\n\n"
                f"Remaining balance: {balance_usdc:.2f} USDC\n"
                f"Context: {topic}\n\n"
                f"Top up to keep it running."
            ),
        },
        "paused": {
            "subject": f"🛑 Container paused — {balance_usdc:.2f} USDC",
            "body": (
                f"Your container has been paused due to insufficient credits.\n\n"
                f"Final balance: {balance_usdc:.2f} USDC\n"
                f"Context: {topic}\n\n"
                f"Top up to automatically resume your workloads."
            ),
        },
        "restored": {
            "subject": f"✅ Container resumed — {balance_usdc:.2f} USDC",
            "body": (
                f"Top-up received. Your container has been successfully resumed.\n\n"
                f"New balance: {balance_usdc:.2f} USDC\n"
                f"Context: {topic}\n\n"
                f"Operations will continue."
            ),
        },
    }

    template = templates.get(warning_type, templates["low_credit"])

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{locus_api_base}/x402/agentmail-send-message",
                headers={
                    "Authorization": f"Bearer {locus_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": [{"email": fallback_email}],
                    "inbox_id": agentmail_inbox,
                    "subject": template["subject"],
                    "body": template["body"],
                },
            )
            return resp.status_code < 300
    except Exception as e:
        print(f"AgentMail error: {e}")
        return False
