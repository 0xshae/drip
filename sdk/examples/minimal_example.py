"""
Minimal Drip example — a pay-per-use joke generator.
Users deposit credits. Each joke costs 0.01 USDC.
No credits = no jokes.
"""
import os
from fastapi import FastAPI, HTTPException
from drip import DripClient, DripConfig
from drip.exceptions import DripInsufficientCredits
import httpx

app = FastAPI()
client = DripClient(DripConfig(
    locus_api_key=os.environ.get("LOCUS_API_KEY", ""),
    bwl_api_key=os.environ.get("BWL_API_KEY", ""),
    agentmail_inbox=os.environ.get("AGENTMAIL_INBOX", ""),
))

@client.meter(cost=0.01, event="joke_generated", user_id_param="user_id")
async def generate_joke(user_id: str) -> str:
    async with httpx.AsyncClient() as http:
        resp = await http.get("https://official-joke-api.appspot.com/random_joke")
        joke = resp.json()
        return f"{joke['setup']} — {joke['punchline']}"

@app.post("/provision")
async def provision(user_id: str, email: str):
    await client.provision_user(user_id=user_id, email=email, initial_balance=0.0)
    return {"ok": True}

@app.get("/joke/{user_id}")
async def get_joke(user_id: str):
    try:
        joke = await generate_joke(user_id=user_id)
        return {"joke": joke}
    except DripInsufficientCredits:
        raise HTTPException(402, "No credits remaining. Top up to continue.")

@app.post("/topup/{user_id}")
async def topup(user_id: str, amount: float):
    await client.topup(user_id=user_id, amount=amount)
    return {"ok": True, "new_balance": amount}
