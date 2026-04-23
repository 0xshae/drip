# Locus Drip 💧

**Pay-as-you-go compute middleware for the agentic economy.**

Locus Drip is an infrastructure layer that transforms any application deployed on **BuildWithLocus** into a fully monetized, usage-based service. It bridges the gap between raw compute and on-chain payments by providing a seamless SDK to meter API calls, manage user credits, and autonomously control container lifecycles based on real-time USDC balances.

Built for the **Paygentic Hackathon Series — Week 2 & 3**.

---

## 1. Built on Locus — Integration Depth

Drip is built from the ground up to utilize the full Locus stack as its foundational layer:

*   **BuildWithLocus (PaaS):** The core of our lifecycle management. Drip communicates directly with the BWL API to `provision`, `hibernate` (scale to zero), and `restore` user-specific containers based on their financial standing.
*   **CheckoutWithLocus (Payments):** Integrated for frictionless top-ups. Drip generates machine-readable checkout sessions, allowing both humans and agents to deposit USDC to replenish their compute credits.
*   **PayWithLocus (Wallet):** All wrapped API calls (Exa, Firecrawl, Claude) are billed through a master non-custodial wallet. Drip monitors this wallet's balance to ensure platform solvency.
*   **AgentMail (Notifications):** Automated email triggers notify users when their balance is low, when their container has hibernated, or when a top-up has successfully restored their service.
*   **Wrapped APIs:** Our reference implementation (the Research Agent) runs entirely on Locus-wrapped versions of Exa (Search), Firecrawl (Scraping), and OpenAI/Claude (Synthesis).

## 2. Agent Architecture

Locus Drip acts as the "financial brain" for autonomous agents:

*   **Middleware SDK:** A Python-native library (`locus-drip`) that exposes a `@meter` decorator. This allows developers to gate ANY tool or function behind a USDC cost.
*   **State Polling:** A background loop monitors the global delta between local user balances and master wallet health, making autonomous decisions to pause or resume infrastructure.
*   **Lifecycle Awareness:** The agent architecture is designed for "sleep and wake." Agents don't just stop; their entire compute environment hibernates, preserving state while saving the developer from idle costs.

## 3. Data Model (SQLite/PostgreSQL)

Drip maintains a robust internal ledger to ensure sub-millisecond metering:

*   **`users`:** Tracks `user_id`, `email`, `balance_usdc`, and `status` (`active`, `low_credit`, `paused`).
*   **`logs`:** A complete audit trail of every credit deduction, provision event, and lifecycle transition.
*   **`checkout_sessions`:** Records pending top-up sessions and maps Locus payment IDs back to internal user accounts.

## 4. Security

Security is paramount when handling fund-gated infrastructure:

*   **Webhook Verification:** All incoming payment signals from CheckoutWithLocus are verified using HMAC-SHA256 signatures to prevent credit injection attacks.
*   **Secret Management:** API keys for Locus and BWL are never exposed to the client-side and are managed via environment variables.
*   **Scoped Access:** The SDK uses scoped developer keys to manage only the containers and wallets associated with the Drip project.

## 5. Tech Stack

*   **Framework:** Python 3.10+, FastAPI (Asynchronous Backend)
*   **SDK:** `locus-drip` (Distribution name: `locus-drip`)
*   **Database:** SQLite (default for demo), supports PostgreSQL for production
*   **Payments:** Locus Beta API (PayWithLocus, CheckoutWithLocus)
*   **Infrastructure:** BuildWithLocus (Agent-native PaaS)
*   **Notifications:** AgentMail
*   **AI Stack:** Locus Wrapped OpenAI (GPT-4o), Exa, Firecrawl

## 6. Local Development

### Prerequisites
- Python 3.10+
- A Locus API Key (Beta)
- A BuildWithLocus API Key

### Setup Instructions
1.  **Clone the repo:**
    ```bash
    git clone https://github.com/0xshae/drip
    cd drip
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -e ./sdk
    ```
3.  **Environment Variables:**
    Create a `.env` file based on `.env.example`:
    ```env
    LOCUS_API_KEY=your_key
    BWL_API_KEY=your_key
    AGENTMAIL_INBOX=your_inbox@agentmail.to
    ```

### Key Scripts
- **Start the Drip Server:** `uvicorn locusmeter.main:app --port 8080`
- **Run the Smoke Test:** `python smoke_test.py`
- **Run the Research Agent:** `python sdk/examples/research_agent.py`

## 7. Deployment

Locus Drip is designed to be deployed on **BuildWithLocus**.

1.  Push your code to a GitHub repository.
2.  Use the BWL CLI or API to provision the `locusmeter` service.
3.  Set the `DRIP_URL` environment variable to your public BWL service URL.
4.  Configure your CheckoutWithLocus webhook to point to `https://your-service.bwl.com/webhook/checkout-paid`.

## 8. What We Built

*   **Locus Drip SDK:** A publishable Python package that any developer can drop into their project to add billing in minutes.
*   **Reference Research Agent:** A fully functional, budget-aware agent that uses wrapped APIs to synthesize research, paying only for what it uses.
*   **Automated Lifecycle Controller:** The core engine that manages the "provision -> monitor -> hibernate -> restore" loop autonomously.
*   **Unified Dashboard:** A real-time view of all provisioned agents, their current credit balances, and live operational logs.

## 9. Known Constraints

*   **Polling Frequency:** Currently defaults to 60-second intervals for balance checks; high-frequency apps may require webhooks for more immediate balance syncs.
*   **Concurrency:** The demo uses SQLite; production environments should scale to PostgreSQL for high-volume concurrent metering.

## 10. Future Roadmap

*   **Dynamic Pricing Engine:** Allow agents to dynamically adjust their own `@meter` costs based on current compute difficulty or market demand.
*   **Multi-Tenant Dashboard:** A self-serve portal where users can manage their own Drip balances across multiple different Locus-deployed apps.
*   **Entitlement Gating:** Move beyond just "credits" to complex feature-based gating (e.g., "Tier 1 users get access to GPT-4, Tier 2 gets GPT-4o").

## 11. Monetization Strategy

*   **SaaS Infrastructure Fee:** Drip can charge a small percentage (e.g., 2%) on top of every transaction processed through the middleware.
*   **Compute Markup:** Developers using Drip can easily build in profit margins by setting their `@meter` costs slightly higher than the raw Locus Wrapped API costs.
*   **Enterprise Tier:** Managed Drip hosting with advanced audit logging and multi-wallet spending controls for large-scale agent deployments.
