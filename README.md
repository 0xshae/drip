# drip

Pay-as-you-go compute middleware for BuildWithLocus apps.

Users deposit USDC credits. Your app runs. Credits drain on actual compute events — API calls, tokens, storage writes. Credits hit zero, the container hibernates. User tops up, it resumes exactly where it left off.

## What's in this repo

- `sdk/` — the drip-sdk Python package (installable via pip)
- `research/` — reference implementation: a pay-per-use research agent
- `locusmeter/` — the core Drip agent server (deployed on BuildWithLocus)
- `smoke_test.py` — full lifecycle verification

## Quick start for developers

```bash
pip install drip-sdk
```

See [sdk/README.md](sdk/README.md) for full integration details.

## Running the reference implementation

1. Set up your `.env` with `LOCUS_API_KEY`, `BWL_API_KEY`, and `AGENTMAIL_INBOX`.
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `uvicorn locusmeter.main:app --host 0.0.0.0 --port 8080`
4. Visit `http://localhost:8080/dashboard` to view the UI.

## Architecture

Your BuildWithLocus app is decorated with `@drip.meter()`, which intercepts metered actions and delegates the billing logic to `DripClient`. 

- **PayWithLocus** handles the master wallet and credit top-ups.
- **BuildWithLocus** manages container lifecycle (scale to zero when credits hit 0).
- **AgentMail** automatically emails the user when their balance is low.
- **Postgres/SQLite** persists the user credit ledgers and session state.
