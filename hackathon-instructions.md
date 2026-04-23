> ## Documentation Index
> Fetch the complete documentation index at: https://docs.paywithlocus.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Hackathon — Paygentic

> Build with Locus at the Paygentic Hackathon Series — weekly tracks with cash, Locus credits, and a YC founder call on the line

## Locus' Paygentic Hackathon Series

The Paygentic Hackathon Series is a four-week run of themed hackathons, each centered on a different Locus product. Pick any week — or sweep all four.

| Week | Track                 | Focus                                                                                               |
| ---- | --------------------- | --------------------------------------------------------------------------------------------------- |
| 1    | **PayWithLocus**      | Agents that buy and sell from each other, consumer agents that transact, automated business finance |
| 2    | **BuildWithLocus**    | Agent-native PaaS — deploy full-stack apps via API, no DevOps                                       |
| 3    | **CheckoutWithLocus** | Stripe-style USDC checkout that's machine-readable by design                                        |
| 4    | **LocusFounder**      | Agents that don't assist businesses — they *are* the business                                       |

***

## Prizes (per week)

| Place | Cash  | Locus Credits | Bonus                         |
| ----- | ----- | ------------- | ----------------------------- |
| 1st   | \$600 | \$300         | 30-min call with a YC founder |
| 2nd   | \$300 | \$150         | —                             |
| 3rd   | \$100 | \$75          | —                             |

**Every team** that submits gets **\$10 in Locus credits** for participating.

***

## Weekly schedule

Every week runs Friday → Thursday:

| Day     | What happens                                                                             |
| ------- | ---------------------------------------------------------------------------------------- |
| **Fri** | Opening ceremony, challenge briefing, technical setup webinar — hacking starts           |
| **Sat** | Technical office hours open; Twitter Spaces Q\&A on the agentic economy                  |
| **Sun** | Continued hacking, technical office hours                                                |
| **Mon** | Midpoint check-in and mentor sessions; 24/7 Discord support in a dedicated VC            |
| **Tue** | Continued mentorship; Late Night Code & Coffee virtual hangout                           |
| **Wed** | **Submissions deadline**                                                                 |
| **Thu** | Demo presentations, judging, awards ceremony — and registration opens for the next track |

***

## Tracks in detail

### Week 1 — PayWithLocus

Build systems where AI agents buy and sell services from each other, consumer-facing agents that make purchases, or agents that run real business financial operations.

**Example projects:**

* Agents trading compute, data processing, or API calls
* Personal shopping agents, booking bots, subscription managers
* Automated procurement, expense management, invoice processing

### Week 2 — BuildWithLocus

[Build with Locus](/build/index) is an agent-native PaaS that deploys full-stack apps in minutes through a simple API — no cloud consoles, no Dockerfiles, no DevOps. Push code, and Locus handles builds, infrastructure, routing, SSL, databases, and scaling.

**Example projects:**

* **One-click SaaS launcher** — takes a GitHub repo URL, spins up a service + Postgres + domain in one request
* **Multi-tenant app platform** — provisions isolated Locus environments per customer, auto-teardown after trials
* **CI/CD bot** — a GitHub Actions or Slack bot that listens for events, triggers Locus deployments, and streams build status
* **Infrastructure-as-chat** — a natural-language interface where an agent translates deploy intents into Locus API calls

### Week 3 — CheckoutWithLocus

[Checkout with Locus](/checkout/index) is a Stripe-style USDC payments SDK for the agent economy. The checkout page is machine-readable by design — agents discover and pay programmatically, as easily as humans click through.

**Example projects:**

* **Agent-to-agent marketplace** — agents list services (data enrichment, code review, image generation); other agents discover and pay autonomously
* **Pay-per-use API wrapper** — gate any tool behind a Locus checkout session, no subscriptions or accounts
* **AI freelancer platform** — an agent completes tasks and invoices via checkout link, collecting USDC on completion
* **Token-gated content** — pay USDC to unlock premium content or one-time downloads with instant on-chain confirmation

### Week 4 — LocusFounder

End-to-end business creation — autonomous operations, agent-run storefronts, real revenue. Build agents that don't assist founders — they *are* the founder.

Using Locus Checkout for transactions and Locus wallets for payouts, your agent should take a prompt, stand up a working commercial operation, and generate revenue with no human in the loop.

**Example projects:**

* Receives a niche prompt (*"pet accessory dropshipping store"*), sources products, builds a storefront, writes listings, wires up Checkout, and routes payouts — fully unattended
* A multi-agent pipeline: sales agent acquires customers via Checkout, fulfillment agent delivers, finance agent logs revenue and manages payouts
* An agent-operated digital services business (logos, content, SEO audits) that accepts orders, fulfills using wrapped APIs, and settles payment end-to-end
* An agent that monitors trending product categories, spins up a new store per opportunity, winds it down when demand drops — businesses as ephemeral units

***

## Get started in 5 minutes

<Steps>
  <Step title="Register your agent">
    Your agent can self-register on the beta environment — no account needed:

    ```bash theme={null}
    curl -X POST https://beta-api.paywithlocus.com/api/register \
      -H "Content-Type: application/json" \
      -d '{"name": "MyAgent", "email": "you@example.com"}'
    ```

    Save the `apiKey` and `ownerPrivateKey` from the response.
  </Step>

  <Step title="Use the PAYGENTIC access code">
    Sign up at [beta.paywithlocus.com](https://beta.paywithlocus.com) with code **`PAYGENTIC`** to unlock beta access for your team.
  </Step>

  <Step title="Request credits">
    Get free USDC to build with — no auth required:

    ```bash theme={null}
    curl -X POST https://beta-api.paywithlocus.com/api/gift-code-requests \
      -H "Content-Type: application/json" \
      -d '{
        "email": "you@example.com",
        "reason": "Building at the Paygentic Hackathon",
        "githubUrl": "https://github.com/your-username/paygentic-project",
        "requestedAmountUsdc": 5
      }'
    ```

    You'll receive a redemption code via email once approved.
  </Step>

  <Step title="Read the skill file">
    Point your agent at the skill file to learn all available APIs:

    ```
    Read https://beta-api.paywithlocus.com/api/skills/skill.md and follow the instructions
    ```
  </Step>

  <Step title="Build!">
    Use Locus wallets, transfers, wrapped APIs, checkout, or vertical tools in your project.
  </Step>
</Steps>

<Note>
  See the [Beta Quick Start](/quickstart-beta) for a full walkthrough of setup options.
</Note>

***

## What Locus offers

Locus is payment infrastructure for AI agents. One wallet, one USDC balance — agents pay for APIs, deploy services, process payments, and make purchases without creating separate accounts.

| Capability            | Description                                                            |
| --------------------- | ---------------------------------------------------------------------- |
| **Agent Wallets**     | Non-custodial smart wallets on Base with sponsored gas                 |
| **USDC Transfers**    | Send to wallet addresses or via email escrow                           |
| **Spending Controls** | Allowances, per-tx limits, approval thresholds                         |
| **Wrapped APIs**      | Pay-per-use access to OpenAI, Gemini, Firecrawl, Exa, and more         |
| **Checkout SDK**      | Stripe-style USDC payments — accepts wallet, external wallet, or agent |
| **Build with Locus**  | Deploy containerized services via API                                  |
| **Laso Finance**      | Prepaid virtual debit cards from USDC                                  |
| **Auditability**      | Full transaction history with agent intent logging                     |

***

## Judging criteria

**100 points total**, weighted across four dimensions:

| Dimension                   | Points | What we're looking for                                                               |
| --------------------------- | ------ | ------------------------------------------------------------------------------------ |
| **Technical Excellence**    | 30     | Implementation quality, proper use of Locus APIs, performance, security, reliability |
| **Innovation & Creativity** | 25     | Uniqueness of approach, novel applications of agent financial autonomy               |
| **Business Impact**         | 25     | Commercial viability, clear value proposition, scalable market                       |
| **User Experience**         | 20     | Interface design, demo quality, documentation and ease of use                        |

### Judging panel

* **Locus Leadership** — technical and business perspective
* **External VCs** — market viability and investment potential
* **Industry Experts** — fintech, AI, automation
* **Developer Community** — technical merit and innovation

### Process

1. **Initial screening** — technical functionality verification
2. **Demo presentations** — 5-minute pitch + 2-minute Q\&A per team
3. **Deliberation** — judges discuss and score
4. **Winner selection** — top projects per category + grand prize

***

## Registration & requirements

### Team structure

* **Size:** 1–4 people maximum
* **Skills:** at least one team member with API integration experience
* **Cost:** free; capped at 200 teams, first-come first-served

### Submission requirements

* **Working demo** of core functionality
* **Source code** in a public GitHub repository
* **Documentation** — README with setup and API usage
* **Video demo** — 3-minute screen recording of key features
* **Brief business plan** — one-page commercial potential summary

### Eligibility

* Open to everyone — students, professionals, international participants
* Locus employees may participate but are not eligible for prizes
* Code of conduct: respectful, inclusive, collaborative

### Disqualifiers

* No working Locus integration (mentioning Locus in the README doesn't count)
* Custodial designs that bypass the non-custodial architecture
* Agents that spend with no controls or logging
* Security vulnerabilities in fund handling

***

## Support

* **Locus engineers** — technical implementation support, available 24/7 in Discord
* **Design partners** — UX/UI guidance and user experience review
* **Dedicated office-hours VC** in Discord throughout each week

***

## Key beta endpoints for hackathon builders

| Endpoint                             | Method | Auth    | Description                    |
| ------------------------------------ | ------ | ------- | ------------------------------ |
| `/api/register`                      | POST   | None    | Agent self-registration        |
| `/api/status`                        | GET    | API Key | Check wallet deployment status |
| `/api/skills/skill.md`               | GET    | None    | Fetch skill file               |
| `/api/gift-code-requests`            | POST   | None    | Request free credits           |
| `/api/pay/send`                      | POST   | API Key | Send USDC                      |
| `/api/pay/balance`                   | GET    | API Key | Check balance                  |
| `/api/wrapped/:provider/:endpoint`   | POST   | API Key | Call wrapped API               |
| `/api/checkout/agent/pay/:sessionId` | POST   | API Key | Pay checkout session           |
| `/api/x402/:slug`                    | POST   | API Key | Call x402 endpoint             |
| `/api/feedback`                      | POST   | API Key | Submit feedback                |

All endpoints above use base URL `https://beta-api.paywithlocus.com`.

***

## Resources

<CardGroup cols={2}>
  <Card title="Beta Quick Start" icon="rocket" href="/quickstart-beta">
    Full setup guide for the beta environment.
  </Card>

  <Card title="Request Credits" icon="gift" href="/credits">
    Get free USDC credits — no auth required.
  </Card>

  <Card title="Wrapped APIs" icon="plug" href="/wrapped-apis/index">
    Browse the pay-per-use API catalog.
  </Card>

  <Card title="Checkout" icon="cash-register" href="/checkout/index">
    Integrate the checkout SDK.
  </Card>
</CardGroup>
