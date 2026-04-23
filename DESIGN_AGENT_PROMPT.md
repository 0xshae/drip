# Design Agent Prompt: Drip Landing Page Redesign (Locus Aesthetic Edition)

## Context

You are redesigning the landing page for **Drip** — a B2B2C middleware platform that enables SaaS companies to offer a **consumption-based ("pay-as-you-drink") billing model** alongside or instead of traditional subscriptions. The target audience is **SaaS business owners and technical founders**, not end users.

The core insight the design must communicate: AI-powered products have made the old subscription model economically dangerous. Heavy users now cost more than their subscription fee. Light users churn because the price is too high. Drip fixes both sides of this problem simultaneously — and the mechanism is an autonomous agent that manages the pricing intelligence, not a static billing rule.

**Aesthetic directive:** The visual language must precisely emulate **Locus (paywithlocus.com)** : high-trust, developer-centric, security-first, functional, and serious. No playful B2C elements. No generic startup gradients. Think **infrastructure-grade UI** — clean, precise, and authoritative.

Read everything below before touching a pixel.

---

## The Product Vision: What Drip Does

Drip is middleware. SaaS companies integrate it via a Python SDK. After integration, their customers can pay for actual usage instead of (or in addition to) a monthly subscription.

The power move: **the Drip agent manages the hybridity autonomously**. It monitors how each customer is using the service and can suggest or switch them to the most economical plan for their behavior. For example:

> "I've noticed you're using this tool heavily this week — it would actually be $5 cheaper for you to switch to the Monthly Subscription for the next 30 days. Should I handle that for you?"

This is the sentence the design must make visceral. The agent is not a rule-based billing system. It is an advocate for the customer, operating on behalf of the SaaS company. It surfaces price intelligence that humans would never manually compute, and it can act on that intelligence automatically.

---

## The Problems Drip Solves (for SaaS businesses)

You must communicate these problems sharply. Use them as the emotional hook.

### Problem 1: The Subscription Model Is Broken for AI Products

Traditional SaaS had near-zero marginal cost — serving one more user was essentially free. AI changed that. GPU compute is expensive, variable, and tied to what users actually do. A "power user" running heavy AI jobs can cost 5x their subscription fee. A light user who logs in twice a month subsidizes them.

The result: SaaS companies either eat losses from power users or raise prices and lose light users. They lose either way.

### Problem 2: The Pricing Cliff (Revenue Leakage)

Tiered subscriptions create cliffs. User A uses 2,900 units and pays the $50 tier. User B uses 3,100 units and must jump to the $100 tier for just 200 extra units — a $50 premium for $2 worth of marginal compute.

User B does one of three things: churns angrily, underuses the product (leaves value on the table), or games the system (multiple accounts, open-source alternatives). The vendor loses revenue or customers every time someone hits a tier boundary.

### Problem 3: The Waste Problem (Customer Friction)

Users who buy a 3,000-unit subscription tier and use 1,500 units feel cheated. They paid for capacity they didn't use. This creates resentment, which drives churn. Pure consumption eliminates this — users pay for exactly what they consumed, no more.

---

## The Audience

**Primary audience:** SaaS founders and CTOs at AI-powered companies experiencing margin pressure from subscription models. They know the pricing cliff problem. They've had to raise prices. They've watched users churn at tier boundaries. They want a better model but don't want to rebuild their billing stack from scratch.

**Secondary audience:** New SaaS companies building AI-native products who want to launch with consumption billing from day one.

**Not the audience:** End users of SaaS products. Individual consumers. General public.

---

## Page Structure & Sections

### 1. Hero / Opening

Single clear statement of value. Something in the direction of:

**"Your subscription model is leaking revenue. Drip plugs the holes."**

Or: **"Stop charging for the month. Start charging for the value."**

Subheadline should name the pain: AI products have variable costs. Subscriptions don't. Drip bridges that gap with an agent that manages billing intelligence autonomously.

The hero CTA should be "Get early access" or "Talk to us" — this is B2B, not self-serve signup. No "Start free trial" — that's consumer framing.

**Aesthetic instruction (Locus-inspired):**
- **Dark or neutral background** (off-black or deep charcoal, not pure black). Locus uses high-contrast, sophisticated dark tones.
- **Tagline in bold, tight-tracking sans-serif** (e.g., Inter, SF Pro, or equivalent).
- **Subheadline** set in lighter weight, 18-20px, max width 60 characters per line.
- **No hero image of people or abstract shapes.** Use a **minimal diagram or schematic** showing: `SaaS App → Drip Agent → Optimal Plan (auto-switch)`. Line-art style, isometric or flat, with one accent color.
- **Primary CTA:** "Get early access" or "Talk to us" — secondary CTA: "Watch the agent work" (links to the live demo panel immediately below).
- **Trust marker line** (small text above or below CTA): "Used by AI-native SaaS teams" or similar.

### 2. Live Agent Demo (HIGH PRIORITY — near the top)

This section is critical. It must be interactive or animated — not a static screenshot.

**Scenario to demonstrate:** An AI writing assistant SaaS company uses Drip. The demo should walk through the following sequence in a live, animated, terminal-style log panel:

```
[09:14] Agent: checking usage for user@company.com this billing period
[09:14] Agent: 47 AI generations this week — tracking ahead of monthly average
[09:15] Agent: projected total: 380 generations → pay-as-you-drink cost: $19.00
[09:15] Agent: monthly subscription cost: $20/month
[09:15] Agent: switching to subscription would save this customer $1.00
[09:15] Agent: preference set to 'suggest-only' — sending recommendation via email
[09:16] Agent: "Hi Sarah, I've noticed you're using the tool heavily this week —
you'd save $5 by switching to monthly for the next 30 days.
Reply YES and I'll handle it."
[09:17] User: YES
[09:17] Agent: subscription activated — customer switched from consumption to monthly
[09:17] Agent: your revenue for Sarah: $20.00 (previously projected: $14.20 if she'd churned)
```

The demo must make two things visible simultaneously:
1. The agent working in real time — autonomous, watching, reasoning
2. The SaaS business outcome — a customer who would have churned at a pricing cliff is retained

Include a "Watch the agent work" or "Run demo" button. Cycle through different scenarios if interactive: heavy user, light user, user about to hit a tier cliff.

**Aesthetic instruction (critical — direct Locus emulation):**
- This must be a **dark-terminal panel** (background: `#0A0A0A` or `#111111`, monospace font like JetBrains Mono, 13-14px).
- **Animated line-by-line appearance** with a blinking cursor at the end.
- **Color-coding:**
  - Timestamps: dim gray (`#666`)
  - Agent actions/decisions: bright cyan or electric blue (`#00B8D9` or `#3B82F6`)
  - Recommendations to user: white
  - User reply (`YES`): green (`#10B981`)
  - Outcome/savings: amber or green
- Include a **small status badge** above the terminal: `● AGENT ACTIVE` (green pulsing dot).
- Add a manual **"Run demo" button** below the terminal (outline style, small) that replays the animation.
- **No glossy card shadows** — the terminal should feel like a real developer tool window, not a marketing mockup.

### 3. The Problem Statement

Two-column layout or alternating cards. Each card shows:
- **The situation** (with real numbers)
- **What currently happens** (churn, underuse, gaming)
- **What Drip does instead**

Use the specific examples:
- User A: 2,900 units, $50 tier. User B: 3,100 units, forced to $100 tier. Drip: charges User B $52 for 3,100 units. User B stays.
- User buys 3,000-unit tier, uses 1,500. Feels cheated. Drips: charges for 1,500. No waste. No resentment.
- AI power user costs $75/month to serve, pays $50 subscription. Drip: their consumption billing pays $75. Business isn't subsidizing them.

Tone: clinical and factual. These are math problems, not philosophical ones.

**Aesthetic instruction:**
- **Two-column or three-card grid.** Each card has a **subtle border** (not heavy shadow), consistent border-radius (8-12px).
- **Card header:** "The Situation," "What Currently Happens," "What Drip Does Instead" — set in all-caps, tiny font, tracked out, muted color.
- **Inside the card, use real numbers in bold accent color.** Example: `2,900 units` in regular weight, but `$50 tier` in electric blue.
- **No illustrations inside cards** — this is clinical, factual, mathematical. Use typography and spacing to create hierarchy.

### 4. Before / After: Apps That Benefit from Drip

Show 3–4 real SaaS archetypes with a side-by-side comparison.

**Format for each:**
- App type (e.g., AI Writing Assistant)
- Without Drip: tier structure, cliff problem, churn rate
- With Drip: consumption model, no cliff, retention outcome

**Suggested archetypes:**

**AI Writing Assistant (e.g., Jasper-type)**
- Without Drip: $49/month for 50k words. User writes 60k words in one month, must upgrade to $99 tier. Pays $50 extra for 10k words that cost $0.50 to generate. Churns instead.
- With Drip: Pays $49 for their 50k-word baseline. Pays $0.50 for the extra 10k words. Total: $49.50. Stays.

**Data Analytics Platform (e.g., Tableau-type)**
- Without Drip: $150/month flat. Light user runs 3 reports/month. Feels ripped off. Churns after trial.
- With Drip: Pay-per-query starting at free. Light user pays $8/month for their 3 reports. Keeps using. Eventually grows to power user.

**Cloud Backup Service (e.g., Backblaze-type)**
- Without Drip: 100GB user pays same as 5TB user. 100GB user leaves for cheaper option.
- With Drip: 100GB user pays for 100GB. 5TB user pays for 5TB. Both happy. Zero churn from price mismatch.

**Developer API Tool**
- Without Drip: $200/month subscription. New developers won't commit. Churn before the 14-day trial ends.
- With Drip: Pay $0.01 per API call. Developers start immediately, no commitment. Heavy users self-select into subscription tier.

**Aesthetic instruction:**
- For each archetype, use a **side-by-side comparison table** or **two-panel card** (left: Without Drip, right: With Drip).
- **Without Drip** side: subtle red tint or red status badge (`● CHURN`).
- **With Drip** side: green or blue status badge (`● RETAINED`).
- Use **clean horizontal rules** between sections.
- Keep the tone factual. No checkmark emojis. Use SVG icons (minimal, line-art) for each archetype (e.g., document icon for writing assistant, chart icon for analytics).

### 5. The Agent Intelligence Section (THE MARQUEE SECTION)

This is the product's superpower. Design it to stop the reader.

Headline: **"The agent is the billing department."**

Explain: Traditional billing is a rule set ("charge $X on the 1st of the month"). Drip's agent is a reasoning system that:
- Watches how each customer uses the product in real time
- Computes which pricing model is economically optimal for that customer at any moment
- Can autonomously switch them or send a recommendation
- Manages the hybridity: subscription and consumption are not either/or — they're two modes the agent moves customers between based on actual behavior

The key phrase must appear prominently (word it naturally in context, not as a direct quote):
> "The agent noticed you're using this heavily this week — it would actually be cheaper to switch you to the monthly plan for 30 days. Want me to handle it?"

This demonstrates that Drip isn't just metering — it's acting in the customer's financial interest, which builds trust and reduces churn.

Show a visual of the agent's decision logic — could be a simple flowchart or animated decision tree:
- Customer usage this period vs. subscription cost
- If consumption > subscription: suggest/switch to subscription
- If consumption < subscription: keep on consumption, save the customer money
- At tier cliff: smooth consumption charge instead of forcing tier jump

**Aesthetic instruction (most Locus-like moment):**
- **Headline:** `The agent is the billing department.` — set in large, heavy weight, maybe split layout (headline left, supporting text right).
- **Visual centerpiece:** A **simple flowchart or decision tree** (isometric or flat, monochrome + one accent color) showing the logic above.
- **The key sentence** should appear in a **pull quote** (larger font, subtle left border in accent color, italic or regular but distinguished).
- **No avatar, no chat bubble styling** — this is not a chatbot. This is a system message.

### 6. How Drip Works (Technical Credibility Without Revealing IP)

This section is for the technical co-founder or CTO who needs to know how it integrates before approving it. It should be honest about the architecture without revealing proprietary implementation details (closed source).

**Key things to communicate:**
- Drip is middleware: it sits between your app and your billing/infrastructure layer
- Integration is done via a Python SDK with a decorator (`@drip.meter`) — 5-minute integration for the basic case
- The Drip agent runs a background loop, monitoring usage and balance state, making decisions every N seconds
- Containers per user are provisioned and managed by BuildWithLocus (say this — it's a genuine technical differentiator)
- Payments are processed via PayWithLocus (USDC-native, but users don't need to know that's happening)
- The agent sends user notifications via AgentMail autonomously — the SaaS company doesn't write email copy

Show a minimal code snippet:

```python
from drip import DripClient, DripConfig

client = DripClient(DripConfig(
    api_key="drip_live_...",
))

# This is all you add to your existing endpoint
@client.meter(cost=0.007, event="ai_generation")
async def generate_content(prompt: str, user_id: str):
    return await your_existing_ai_call(prompt)
```

> *One decorator. Drip handles metering, notifications, container lifecycle, and plan optimization from here.*

Then a simple architecture diagram:

Your App → Drip SDK → Drip Agent → BuildWithLocus (containers) + PayWithLocus (payments) + AgentMail (notifications)

Single direction of integration. No webhooks to build. No billing UI to design.

Do NOT explain the internals of how containers are hibernated or how HMAC signatures work. That's the IP. Show enough to earn technical trust, not enough to replicate.

Aesthetic instruction (developer documentation precision):

Code blocks must have:

Dark background (matching terminal from section 2)

Syntax highlighting (minimal: keywords bold, strings muted)

A "copy" button (icon only, appears on hover)

Line numbers (optional but encouraged)

Architecture diagram:

Use simple boxes and arrows (line-art, 1px stroke)

Nodes: "Your App" → "Drip SDK" → "Drip Agent" → stacked boxes for "BuildWithLocus | PayWithLocus | AgentMail"

No perspective/3D — pure flat diagram, technical documentation style

Caption below code block: set in small, muted monospace or sans-serif with a → or ◆ bullet.

7. Social Proof / CTA for SaaS Companies (The Conversion Section)
Tone: urgent, peer-to-peer. This is one founder talking to another.

Headline direction: "Your best customers are leaving because your pricing model forces them to."

Body: The companies that win in the AI era are the ones that price for actual value delivered — not flat calendar months. Drip is the fastest way to get there. Integrate in a day. Keep the customers who would have churned at your tier boundary. Stop subsidizing power users with flat fees.

Include customer testimonials (use placeholders for launch, mark clearly as "[TESTIMONIAL PLACEHOLDER]"):

[SaaS CEO] — "We saw 23% reduction in tier-cliff churn in the first month."

[CTO at AI startup] — "Integrated in 4 hours. The agent caught two customers about to churn and moved them to the right plan automatically."

[Founder] — "We were bleeding $2k/month on power users. Drip fixed that while we slept."

CTA: "Get early access" — form with name, company name, monthly active users, current billing model. This is a waitlist/sales conversation starter, not a self-serve signup.

Aesthetic instruction:

Headline left-aligned, not centered. Urgent, direct.

Testimonial cards: minimal — company name, title, quote. No avatar photos (since you don't have real ones). Use a simple icon instead (e.g., " " quote mark or a small company logo placeholder in grayscale).

CTA section should be visually separated by a horizontal rule or a subtle background tint (not a full colored banner — too consumer-y).

Form fields: minimal border, on-dark or on-light consistent with page theme. Label text small, tracked out.

8. Docs Teaser / Integration Guide
Not a full docs page — a teaser that links to a dedicated docs page. Should feel like the first 3 paragraphs of a great API doc.

Show:

Install command: pip install drip-sdk

The @meter decorator as primary integration pattern

One full example (provision a user, meter a function, handle insufficient credits)

```python
# 1. Install
pip install drip-sdk

# 2. Initialize
from drip import DripClient, DripConfig

client = DripClient(DripConfig(api_key="drip_live_..."))

# 3. Provision a user (creates their billing account)
await client.provision_user(
    user_id="user_abc",
    email="sarah@company.com",
    plan="consumption",          # or "subscription" or "hybrid"
    initial_balance=5.0,
)

# 4. Meter any expensive function
@client.meter(cost=0.007, event="ai_generation")
async def generate_content(prompt: str, user_id: str):
    return await your_ai_call(prompt)

# If the user runs out of credits, Drip raises DripInsufficientCredits
# The agent handles notifying the user and offering a top-up automatically
```

Link at bottom: "Read the full integration guide →"

Aesthetic instruction:

This section should visually match Stripe's docs landing — clean, high-contrast, monospaced for code, generous vertical rhythm.

Numbered steps (1. 2. 3.) set in a bold, large font in the margin (float left or absolute positioning).

Link to full docs at bottom: Read the full integration guide → (arrow as SVG, not emoji).

Dedicated Docs Page (Separate Page, Linked From Main)
URL: /docs or /how-it-works

This page is for the technical buyer who wants to understand the full system before committing. It should be professional, structured, and read like Stripe's docs — clear, authoritative, no fluff.

Sections to include:

How Drip Works
The agent architecture: a background process monitoring usage state for all provisioned users

Billing modes: consumption (pure pay-per-use), subscription (flat monthly), hybrid (subscription floor + consumption overages)

Plan optimization: the agent computes cost for each user at each billing mode and can recommend or switch plans autonomously based on configurable policies

The @meter Decorator
Explain parameters:

cost: USDC amount deducted per call

event: string label for the audit log

user_id_param: which kwarg contains the user identifier

Show sync and async usage. Show how DripInsufficientCredits is raised and what to do with it.

User Provisioning
Explain provision_user — what it creates, what parameters it accepts, what happens if the user already exists.

Lifecycle States
Explain the state machine: provisioning → active → low_credit → paused → active
Each transition is triggered by the agent's polling loop. Show what triggers each state and what the agent does at each transition (email via AgentMail, container hibernate/restore via BWL).

The Agent Loop
High-level: the agent polls every N seconds (configurable). For each user, it:

Checks current balance

If balance > 20%: no action

If balance ≤ 20%: sends low-credit warning via AgentMail

If balance = 0: hibernates container, sends pause notification, queues restore check

Periodically audits platform wallet health

Small code comment showing the decision logic is fine — do NOT show the full start_polling implementation.

Billing Modes Detail
Table comparing consumption vs subscription vs hybrid, with example cost calculation for a user who makes 3,100 units in a tiered-subscription world vs. Drip.

Webhook Integration
One section explaining the top-up flow: user hits recharge link → CheckoutWithLocus session created → user pays → webhook fires → Drip credits balance → container auto-restores if paused.

Aesthetic directive (Docs Page):

This page must feel indistinguishable from a serious infrastructure documentation site (Stripe, Vercel, Locus itself).

Left sidebar navigation (table of contents), main content area on the right.

Table for billing modes: grid lines minimal, header row subtle background.

State machine diagram as a simple horizontal flow (boxes → arrows) or as a table with states and transitions.

No glossy marketing elements. No hero. No testimonials. This is purely technical documentation.

Design System & Visual Language (Locus Emulation)
Tone
The visual language must be enterprise-credible but not enterprise-boring. Think Stripe's dashboard mixed with Linear's typography. Technical but accessible.

Color Palette (Locus-specific)
Primary background: Off-white (#F5F5F7 or #F8F9FA) for main page. Dark sections allowed for contrast (e.g., terminal demo, code blocks), but not default dark mode.

Alternative dark sections (agent terminal, footer): Deep charcoal (#111111 or #0D0D0D) — matches Locus's high-contrast dark elements.

Accent color: Electric blue (#0066FF or #3B82F6). Use sparingly: headlines, inline links, active status, key numbers.

Secondary accent (warnings/savings): Amber (#F59E0B) for "saves you $X" or low-credit states.

Success: Emerald (#10B981) for retained users, active agent, completion.

Error/churn: Red (#EF4444) only for "Without Drip" side or churn indicators.

Borders and dividers: #E5E7EB (light mode) or #2A2A2A (dark panels).

Avoid entirely: Warm pastels (pink, peach, lavender), neon gradients, purple-heavy palettes.

Typography (Locus-specific)
Headlines (H1, H2, H3): Inter, SF Pro, or equivalent sans-serif, weight 600–700, tight tracking (-0.02em to -0.01em). Large H1: 52–64px.

Body: 16–18px, line-height 1.5–1.6, max-width 70 characters per line. Regular weight.

Monospace: JetBrains Mono, Fira Code, or SF Mono. Use for:

All code blocks

Terminal demo logs

Inline technical terms (@meter, DripClient)

Numerical thresholds in problem section (2,900 units)

No display fonts, no decorative typography.

Spacing & Layout
Grid: 12-column or 24-column flexible grid. Generous vertical rhythm (margin-bottom: 2–4rem between sections).

Padding: Sections use 64–96px padding top/bottom on desktop, 32–48px on mobile.

Max-width container: 1280px, centered.

White space: Use aggressively. No clutter. Each section should breathe.

Components (Locus-inspired)
Agent Terminal Panel:

Background: #0A0A0A

Border-radius: 8px

Padding: 24px

Font: 13px JetBrains Mono

Optional window controls (traffic lights: red, yellow, green) in top-left for authenticity

Blinking cursor: vertical bar or block

Status Badges:

Small pill, border-radius: 32px

Padding: 4px 12px

Font: 11px uppercase, tracked

Dot indicator (●) before text, colored by state

Example: ● ACTIVE (green dot), ● WARNING (amber), ● PAUSED (red)

Code Blocks:

Dark background (#0D1117 or #1E1E1E)

Syntax highlighting: keywords in electric blue, strings in muted green, comments in gray

Copy button (clipboard icon) to top-right, appears on hover

No line numbers unless requested

Cards (for Problem Statement, Archetypes):

Background: white (or dark if in dark section)

Border: 1px solid #E5E7EB

Border-radius: 12–16px

Padding: 24px

Hover: subtle border color change (accent blue), no elevation change (no heavy shadows)

Buttons:

Primary: solid electric blue, white text, border-radius 32px (pill), padding 12px 28px

Secondary: outline (1px blue), blue text, same pill shape

Tertiary (e.g., "Run demo"): text link with right caret (→) or minimal outline

Icons:

All icons: line-art, 1.5px stroke, consistent style (Heroicons, Phosphor, or Feather)

No filled icons except for status indicators

Icon size: 20x20px for inline, 24x24px for section headers

Interaction & Motion (Locus-specific)
Hover states: Button background darkens by 10%. Link underlines appear (not permanently visible).

Agent terminal animation: Line-by-line appearance. Each line takes 40–60ms to appear. Cursor blinks at 1s intervals.

Scroll-triggered animations: None or extremely minimal. No fade-in-on-scroll for entire sections — that's consumer-landing-page behavior.

Transition timing: All state changes (hover, focus, toggle) at 150–200ms, ease-in-out.

No parallax, no heavy JavaScript-driven motion. The only "animation" is the terminal demo.

Things to Avoid
Do not position Drip as a consumer product. The page sells to SaaS businesses.

Do not use "wallet", "USDC", "crypto" language in headlines or hero copy. This is billing middleware, not a crypto product. The underlying rails use USDC but that's an implementation detail.

Do not show pricing for Drip itself on the landing page — this is a sales conversation product.

Do not make it look like a developer tool homepage (GitHub-aesthetic, dark mode default). The buyer is a business owner, not a hacker.

Do not use the word "blockchain" anywhere.

Do not make the agent feel like a chatbot. It is an autonomous financial decision-maker.

Do not use gradient hero backgrounds, floating shapes, or abstract 3D renderings. Locus's aesthetic is grounded, precise, and functional — no "tech art."

The One Thing
If the design communicates one thing, it should be this:

Your customers are churning at your pricing cliff right now. Drip's agent catches them before they fall.

Everything else — the hybrid model, the code snippets, the architecture diagram — is proof that this is real and you can ship it in a day.