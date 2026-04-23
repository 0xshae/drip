import httpx
from typing import Optional

async def send_agentmail_notification(
    locus_api_base: str,
    locus_api_key: str,
    agentmail_inbox: str,
    user_id: str,
    user_email: str,
    balance_usdc: float,
    notification_type: str,
    metadata: Optional[dict] = None
) -> bool:
    """Send a notification email via AgentMail."""
    if not locus_api_key or not agentmail_inbox:
        return False
        
    fallback_email = user_email if user_email else "shagun.prasad28@gmail.com"
    app_name = metadata.get("app_name", "your Drip service") if metadata else "your Drip service"

    templates = {
        "low_credit": {
            "subject": f"⚠️ Low credits — {balance_usdc:.2f} USDC remaining",
            "body": (
                f"Your {app_name} is running low on credits.\n\n"
                f"Remaining balance: {balance_usdc:.2f} USDC\n\n"
                f"Top up now to avoid service interruption."
            ),
        },
        "paused": {
            "subject": f"🛑 Service paused — {balance_usdc:.2f} USDC",
            "body": (
                f"Your {app_name} has been paused due to insufficient credits.\n\n"
                f"Final balance: {balance_usdc:.2f} USDC\n\n"
                f"Top up to automatically resume your workloads."
            ),
        },
        "restored": {
            "subject": f"✅ Service resumed — {balance_usdc:.2f} USDC",
            "body": (
                f"Top-up received. Your {app_name} has been successfully resumed.\n\n"
                f"New balance: {balance_usdc:.2f} USDC\n\n"
                f"Operations will continue normally."
            ),
        },
        "plan_suggestion": {
            "subject": "💡 You could save money this month — want me to handle it?",
            "body": (
                f"Hi there,\n\n"
                f"I've been watching your usage of {app_name} this week.\n\n"
                f"At your current pace, switching to our monthly subscription plan would save you money compared to pay-as-you-go billing.\n\n"
                f"Should I handle that for you? Reply YES and I'll switch your plan automatically.\n\n"
                f"— Drip Agent"
            ),
        },
    }

    template = templates.get(notification_type, templates["low_credit"])

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
