"""Deep Research Digest — Research Container Service.

Runs inside the user's BWL container. Exposes:
- GET /health — required by BWL
- POST /research/trigger — run a research cycle

In demo mode (?demo_mode=true), compresses credit drain to
reach 20% warning within 2 minutes.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI(
    title="Deep Research Digest",
    description="Personal async research agent powered by Drip",
    version="0.1.0",
)

# Config from environment (injected by BWL)
USER_ID = os.getenv("USER_ID", "demo_user")
TOPIC = os.getenv("TOPIC", "AI agent infrastructure")
LOCUSMETER_URL = os.getenv("LOCUSMETER_URL", "")
LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")


@app.get("/health")
async def health():
    """BWL health check — must return 200."""
    return {"status": "ok", "service": "research-digest"}


@app.post("/research/trigger")
async def trigger_research(
    demo_mode: bool = Query(False, description="Compress drain for demo"),
    topic: str = Query(None, description="Override research topic"),
):
    """Run a research cycle.

    In demo mode, uses compressed drain rate so the full lifecycle
    (deposit → research → low-credit → drain → teardown) plays out
    within ~2 minutes.
    """
    import httpx
    from research.digest import run_research_cycle

    research_topic = topic or TOPIC

    # Get current balance from Drip
    balance = 1.0
    initial_balance = 1.0

    if LOCUSMETER_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{LOCUSMETER_URL}/users/{USER_ID}"
                )
                if resp.status_code == 200:
                    user_data = resp.json()
                    balance = user_data.get("balance_usdc", 1.0)
                    initial_balance = user_data.get("initial_balance", 1.0)
        except Exception as e:
            print(f"Could not fetch balance from Drip: {e}")

    # Abort if no credits
    if balance <= 0:
        return JSONResponse(
            status_code=402,
            content={"error": "No credits remaining — research paused"},
        )

    # Run the research cycle
    result = await run_research_cycle(
        topic=research_topic,
        balance=balance,
        initial_balance=initial_balance,
        demo_mode=demo_mode,
    )

    # Report credit drain to Drip
    cost = result.get("cost_estimate", 0.05)
    if demo_mode:
        cost = 0.20  # Compressed drain for faster demo

    if LOCUSMETER_URL:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{LOCUSMETER_URL}/internal/debit",
                    json={
                        "user_id": USER_ID,
                        "amount": cost,
                        "label": (
                            f"research_cycle ({result.get('sources_used', 0)} sources, "
                            f"{result.get('budget_mode', 'normal')} mode)"
                        ),
                    },
                )
        except Exception as e:
            print(f"Could not report debit to Drip: {e}")

    return {
        "ok": True,
        "topic": research_topic,
        "sources_used": result.get("sources_used", 0),
        "budget_mode": result.get("budget_mode", "normal"),
        "cost_usdc": cost,
        "digest_preview": result.get("digest", "")[:500],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("research.main:app", host="0.0.0.0", port=port, reload=True)
