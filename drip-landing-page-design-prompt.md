# Drip Landing Page Design Prompt

## Project Overview
**Drip** — The first agent-native SaaS billing layer. Software that runs itself within your budget, powered by an AI agent that makes real-time decisions about resource allocation, credit management, and container lifecycle.

**Core Value Proposition:** "You paid $29 last month for a tool you opened four times. The subscription didn't know. Drip does — because the billing layer is an agent, not a form."

## Design Aesthetic Requirements

### 1. Primary Aesthetic: Apple-Minimalist
- **Visual Language:** Clean, spacious, purposeful
- **Typography:** San-serif, highly legible, generous line height
- **Whitespace:** Ample breathing room between elements
- **Color Palette:** Neutral foundation with single accent color for CTAs
- **Visual Hierarchy:** Obvious through typography size/weight, not decoration
- **Interaction Design:** Subtle animations, restrained hover states
- **Grid System:** Rigid, but appears flexible through intelligent composition

### 2. Locus-Inspired Elements
- **Modular Design:** Components that feel like building blocks
- **Technical Authenticity:** Feels like a developer tool, not marketing fluff
- **Data Visualization:** Clean presentation of system states, credits, timelines
- **Status Indicators:** Clear, color-coded status badges (active/paused/restoring)
- **API-First Vibe:** Feels like documentation could be generated from the interface
- **Monospaced Elements:** Where appropriate for logs/code snippets

### 3. Agent-First Vibe
- **Live Agent Logs:** Real-time stream of agent decisions visible on the page
- **Decision Visualization:** Show the agent "thinking" through visualizations
- **Status Timeline:** Visual timeline of container states (active → low credit → paused → restored)
- **Budget Awareness:** Visual representation of credit burn vs budget
- **Autonomous Feel:** Interface feels like it's "running itself"

## Page Structure & Content

### Hero Section
- **Main Headline:** "Software that runs itself within your budget"
- **Subheadline:** "Drip is the first agent-native SaaS billing layer. An AI agent manages your resource lifecycle in real time, making decisions a billing form can't."
- **Primary CTA:** "Start with 20 USDC free" (leads to demo flow)
- **Secondary CTA:** "Watch the agent think" (scrolls to live logs section)
- **Visual:** Either:
  1. Animated diagram showing the agent lifecycle (provision → monitor → warn → teardown → restore)
  2. Live agent log stream showing real decisions (if possible)

### How It Works Section
Four-column visual explanation:
1. **Provision:** "Deposit USDC → Specify topic → Agent spins up your container"
2. **Monitor:** "Agent watches credits in real time, makes tradeoffs under budget pressure"
3. **Think:** "When credits run low: warns you, reduces quality to extend runtime"
4. **Restore:** "Top up → Agent auto-restores container, picks up where it left off"

### The Agent Difference Section
Contrast table:
- **Traditional Billing:** Static subscription, binary on/off, human-triggered warnings
- **Drip Agent:** Dynamic credits, graceful scaling, AI-proactive communication, budget-aware tradeoffs

### Live Demo Element
**Critical:** This isn't a static mockup — it should feel alive.
- **Status Badge:** Real-time status indicator (active/paused/restoring)
- **Credit Meter:** Visual gauge showing USDC balance with burn rate projection
  - Green zone (100-20%): "Healthy"
  - Yellow zone (20-5%): "Budget tight — crawling 2 sources instead of 5"
  - Red zone (<5%): "Hibernating container soon"
- **Live Agent Log Stream:** Actual or simulated stream showing:
  ```
  [14:02] Drip: checking balance... 0.45 USDC remaining
  [14:02] Drip: burn rate 0.02/min → estimated 22 min of life
  [14:03] Drip: sent low-credit warning to user_A via AgentMail
  [14:03] Drip: budget tight — reducing crawl to top 2 sources (was 5) to extend runtime
  [14:25] Drip: balance 0.00 — flushing state to Postgres, hibernating container via BWL API
  [14:26] Drip: container paused — user_A notified with recharge link
  ```
- **Interaction:** Click "Trigger demo mode" to see the agent make a real decision

### Technical Architecture Visual
Clean, diagrammatic explanation of:
- **User Layer:** User deposits USDC via PayWithLocus
- **Agent Layer:** Drip monitors credits, makes decisions
- **Infrastructure Layer:** BuildWithLocus containers scale up/down
- **Data Layer:** Postgres state survives hibernation
- **Communication Layer:** AgentMail autonomous messaging

### Use Cases Section
1. **Research Digest SaaS:** "Deep Research Digest — personal async research agent"
2. **API Cost Management:** "Cap your OpenAI/Exa/Firecrawl spend automatically"
3. **Infrastructure Scaling:** "Containers that sleep when you're not using them"

### Pricing Section
- **Not traditional pricing:** Instead show "What $X gets you"
- **Example:** "$20/month = 400 research cycles or 80 hours of compute"
- **Visual:** Credit calculator with sliders showing tradeoffs
- **Emphasis:** "Pay for what you use, not what you might use"

### Self-Hosting Narrative Section
**Key differentiator:** "Drip itself runs on BuildWithLocus, paid for by the credits it manages. The agent has skin in the game — it only survives while it's providing value."

### CTA Section
- **Primary:** "Try the demo — watch an agent manage your budget"
- **Secondary:** "Read the API docs" (feels technical, not salesy)
- **Tertiary:** "GitHub repo" (builders trust open source)

## Visual Design Specifications

### Color Palette
- **Primary:** Deep blue or teal (trust, intelligence, technology)
- **Secondary:** Warm gray scale (Apple-like neutral foundation)
- **Accent:** Single vibrant color for CTAs and critical states (choose one: electric blue, Locus purple, or mint green)
- **Status Colors:**
  - Active: Green (#10B981)
  - Low Credit: Amber (#F59E0B)
  - Paused: Red (#EF4444)
  - Restoring: Blue (#3B82F6)

### Typography
- **Primary Font:** System font stack with San-serif emphasis (Inter, SF Pro, -apple-system)
- **Monospace Font:** For logs/code (JetBrains Mono, SF Mono, monospace)
- **Scale:** Generous, Apple-like typographic scale
- **Readability:** High contrast, comfortable line length (60-75 characters)

### Spacing & Grid
- **Base Unit:** 8px grid system
- **Section Padding:** Generous (min 96px top/bottom on desktop)
- **Component Spacing:** Consistent vertical rhythm
- **Mobile First:** Clean adaptation to mobile without losing functionality

### Interactive Elements
- **Buttons:** Minimal, high-contrast, generous tap targets (44px+)
- **Forms:** Clean, focused states, helpful micro-copy
- **Animations:** Purposeful, not decorative. Examples:
  - Credit meter filling/draining
  - Status badge transitions
  - Log entries appearing
  - Container state changes

### Data Visualization
- **Credit Meter:** Circular or horizontal progress bar
- **Timeline:** Clean Gantt-like visualization of container states
- **Burn Rate Chart:** Simple sparkline showing credit consumption
- **Decision Flow:** Visual flowchart of agent logic

## Technical Implementation Notes

### For Mockup Generation
This is a **landing page** — not a dashboard. However:
- It needs to feel like you could click and actually interact with a live agent
- The "demo" section should be the most visually compelling part
- Consider showing both:
  1. The marketing/front page (hero, explanation)
  2. The actual app interface (dashboard with logs, meter, controls)

### Key Screens to Show (If multi-screen)
1. **Landing/Marketing Page:** As described above
2. **Dashboard View:** If showing the actual app, include:
   - Sidebar navigation
   - Credit balance widget
   - Status badge
   - Live agent log panel
   - Quick actions (provision, teardown, restore)
   - Recent activity timeline

### Mobile Considerations
- Hero section remains impactful
- Live logs become a horizontally scrollable element or toggle
- How-it-works becomes a vertical carousel or accordion
- Demo section remains interactive (touch-friendly controls)

## Mood Board Keywords
- Apple.com (cleanliness, confidence)
- Vercel Dashboard (developer aesthetic, data clarity)
- Linear.app (productivity, focus)
- Stripe Dashboard (financial clarity, trust)
- Locus Platform (technical authenticity, modular design)
- Dark Sky (data visualization elegance)

## Success Criteria
The design should make visitors feel:
1. **This is intelligent:** Not just another SaaS, but something that thinks
2. **This is trustworthy:** Financial/technical confidence
3. **This is elegant:** Pleasing to use, not just functional
4. **This is real:** Feels like it's working right now, not a concept
5. **I want to try it:** Clear path to experiencing the agent in action

---

**Final Note to Design Agent:** This isn't a traditional SaaS landing page. The hero should be the live agent demonstration, not just marketing copy. Make visitors feel like they're peering into an intelligent system already at work. The design should breathe technical authenticity while being beautiful and accessible.