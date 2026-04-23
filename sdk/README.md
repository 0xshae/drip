# locus-drip — Pay-as-you-go compute middleware for BuildWithLocus apps

Locus Drip is a middleware SDK that transforms any BuildWithLocus application into a pay-as-you-go service. It automatically tracks API usage, deducts credits based on compute events, and intelligently hibernates user containers when their balance runs out.

## Prerequisites
- A BuildWithLocus account and Developer API Key
- Locus API Key for the Locus Agent Ecosystem
- An AgentMail inbox address for automated notifications
- A running PostgreSQL or SQLite database for state persistence

## Installation

```bash
pip install locus-drip
```

## Quick Start

Here is a minimal example of integrating Drip into a FastAPI application:

```python
import os
from fastapi import FastAPI, HTTPException
from locus_drip import DripClient, DripConfig
from locus_drip.exceptions import DripInsufficientCredits
import httpx

app = FastAPI()
client = DripClient(DripConfig(
    locus_api_key=os.environ["LOCUS_API_KEY"],
    bwl_api_key=os.environ["BWL_API_KEY"],
    agentmail_inbox=os.environ["AGENTMAIL_INBOX"],
))

@client.meter(cost=0.01, event="joke_generated")
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
```

## The `@meter` Decorator

The `@meter` decorator automatically deducts credits before executing the wrapped function. If the user's balance is below the `cost`, it raises a `DripInsufficientCredits` exception and prevents execution.

```python
@client.meter(cost=0.007, event="exa_search", user_id_param="user_id")
async def search(query: str, user_id: str):
    ...
```

**Parameters:**
- `cost`: float — The amount of USDC to deduct.
- `event`: str — The telemetry label for this transaction.
- `user_id_param`: str — (Optional) The name of the kwarg containing the user ID. Defaults to `"user_id"`.

## DripClient Reference

`DripClient` handles the orchestration of billing and container lifecycles.

- `provision_user(user_id, email, initial_balance=0.0, credit_rate=0.0, container_image=None, metadata=None)`: Registers a user and spins up a dedicated container.
- `get_user(user_id)`: Returns user metadata and current balance.
- `debit(user_id, amount, label)`: Manually debits funds.
- `hibernate(user_id)`: Manually hibernates a user's container (scales to zero).
- `restore(user_id)`: Manually restores a user's container (scales to one).
- `topup(user_id, amount)`: Adds funds to a user's balance and auto-restores their container if it was paused.
- `start_polling()`: Starts the background polling loop to track balances and auto-hibernate empty accounts.

## DripConfig Reference

Configuration class injected into `DripClient`.

- `locus_api_key`: For billing and wrapper API calls.
- `bwl_api_key`: For container lifecycle management.
- `agentmail_inbox`: Sender address for email notifications.
- `locus_api_base`: Defaults to `https://beta-api.paywithlocus.com/api`.
- `bwl_api_base`: Defaults to `https://beta-api.buildwithlocus.com`.
- `poll_interval_seconds`: Defaults to `60`.
- `mock_drain`: Defaults to `False`. Enables artificial 1% drain per second for local demos.

## Exception Reference

- `DripInsufficientCredits`: Raised when a metered function is called by a user with insufficient funds.
- `DripUserNotFound`: Raised when attempting to interact with an unregistered user.

## How Credits Work

Drip tracks internal balances locally using the provided database to ensure zero latency on metered function calls. Background polling regularly syncs with the master `PayWithLocus` wallet to ensure platform stability. When a user's local balance hits `0`, their BuildWithLocus container is immediately hibernated (scaled to zero). When they top up, the container is resumed.

## Full Example

Check out the full Research Agent implementation in `examples/research_agent.py` to see a real-world multi-agent workflow integrated with Drip.
