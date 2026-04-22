"""Research digest pipeline.

Exa search → Firecrawl scrape → Claude synthesis → AgentMail delivery.

Uses Locus Wrapped APIs — single API key, same interface as native SDKs.
All calls go through the Locus proxy, which handles billing in USDC.
"""

import os
import httpx
from typing import List, Optional

from research.budget import get_crawl_config

LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")
LOCUS_API_BASE = os.getenv("LOCUS_API_BASE", "https://beta-api.paywithlocus.com/api")
LOCUSMETER_URL = os.getenv("LOCUSMETER_URL", "")  # Drip callback URL
USER_ID = os.getenv("USER_ID", "")


async def _locus_wrapped_call(provider: str, endpoint: str, payload: dict) -> dict:
    """Make a call to a Locus Wrapped API.

    Format: POST /api/wrapped/{provider}/{endpoint}
    Auth: Bearer {LOCUS_API_KEY}
    """
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{LOCUS_API_BASE}/wrapped/{provider}/{endpoint}",
            headers={
                "Authorization": f"Bearer {LOCUS_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def search_exa(topic: str, max_results: int = 5) -> List[dict]:
    """Search for recent content on a topic using Exa via Locus Wrapped API."""
    try:
        result = await _locus_wrapped_call("exa", "search", {
            "query": topic,
            "numResults": max_results,
            "useAutoprompt": True,
            "type": "auto",
        })

        # Extract results
        data = result.get("data", result)
        results = data.get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("text", r.get("snippet", ""))[:500],
            }
            for r in results[:max_results]
        ]
    except Exception as e:
        print(f"Exa search error: {e}")
        return []


async def scrape_firecrawl(url: str) -> str:
    """Scrape a single page using Firecrawl via Locus Wrapped API."""
    try:
        result = await _locus_wrapped_call("firecrawl", "scrape", {
            "url": url,
            "formats": ["markdown"],
        })

        data = result.get("data", result)
        # Firecrawl returns content in different possible fields
        content = data.get("markdown", data.get("content", data.get("text", "")))
        # Truncate to reasonable size for synthesis
        return content[:3000] if content else ""
    except Exception as e:
        print(f"Firecrawl scrape error for {url}: {e}")
        return ""


async def synthesize_claude(topic: str, sources: List[dict],
                            mode: str = "detailed") -> str:
    """Synthesize research sources into a digest using Claude via Locus Wrapped API."""
    prompt_styles = {
        "detailed": (
            f"You are a research analyst. Synthesize these sources about '{topic}' "
            f"into a comprehensive research digest. Include key findings, trends, "
            f"and actionable insights. Use clear headings and bullet points."
        ),
        "brief": (
            f"You are a research analyst. Briefly summarize these sources about "
            f"'{topic}'. Focus on the top 2-3 key takeaways. Keep it concise."
        ),
        "minimal": (
            f"Summarize the key finding about '{topic}' from these sources in "
            f"2-3 sentences."
        ),
    }

    source_text = "\n\n---\n\n".join([
        f"Source: {s.get('title', 'Untitled')}\nURL: {s.get('url', '')}\n"
        f"Content: {s.get('content', s.get('snippet', ''))}"
        for s in sources
    ])

    try:
        result = await _locus_wrapped_call("anthropic", "messages", {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 1024 if mode == "detailed" else 512,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt_styles.get(mode, prompt_styles['detailed'])}"
                               f"\n\nSources:\n{source_text}",
                }
            ],
        })

        data = result.get("data", result)
        # Claude API returns content as a list of blocks
        content_blocks = data.get("content", [])
        if isinstance(content_blocks, list):
            return "\n".join(
                block.get("text", "") for block in content_blocks
                if isinstance(block, dict)
            )
        return str(content_blocks)
    except Exception as e:
        print(f"Claude synthesis error: {e}")
        return f"Synthesis failed: {str(e)}"


async def send_digest_email(user_email: str, topic: str, digest: str,
                             inbox: str = ""):
    """Send the completed digest via AgentMail."""
    if not inbox:
        inbox = os.getenv("AGENTMAIL_INBOX", "")
    if not inbox:
        print("No AgentMail inbox configured — skipping email delivery")
        return

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(
                f"{LOCUS_API_BASE}/x402/agentmail-send-message",
                headers={
                    "Authorization": f"Bearer {LOCUS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "to": user_email,
                    "from": inbox,
                    "subject": f"📊 Research Digest: {topic}",
                    "body": digest,
                },
            )
    except Exception as e:
        print(f"AgentMail send error: {e}")


async def run_research_cycle(topic: str, balance: float, initial_balance: float,
                              user_email: str = "", demo_mode: bool = False) -> dict:
    """Run a complete research cycle.

    1. Check budget → determine crawl config
    2. Exa search for topic
    3. Firecrawl scrape top results
    4. Claude synthesis
    5. AgentMail delivery
    6. Report credit cost

    Returns: {digest, sources_used, cost_estimate, budget_mode}
    """
    # 1. Budget-aware config
    config = get_crawl_config(balance, initial_balance)
    max_sources = config["max_sources"]
    synthesis_mode = config["synthesis_prompt"]

    # 2. Exa search
    search_results = await search_exa(topic, max_results=max_sources)
    if not search_results:
        return {
            "digest": f"No search results found for '{topic}'",
            "sources_used": 0,
            "cost_estimate": 0.007,  # Just the search call cost
            "budget_mode": config["budget_mode"],
            "log_message": config["log_message"],
        }

    # 3. Firecrawl scrape
    for result in search_results:
        content = await scrape_firecrawl(result["url"])
        result["content"] = content

    # 4. Claude synthesis
    digest = await synthesize_claude(topic, search_results, mode=synthesis_mode)

    # 5. Email delivery
    if user_email:
        await send_digest_email(user_email, topic, digest)

    # 6. Cost estimate
    sources_used = len(search_results)
    # Per eng plan: Exa ~$0.007, Firecrawl ~$0.003/page, Claude ~$0.01
    cost_estimate = 0.007 + (sources_used * 0.003) + 0.01 + 0.02  # + compute

    return {
        "digest": digest,
        "sources_used": sources_used,
        "sources": [
            {"title": s.get("title", ""), "url": s.get("url", "")}
            for s in search_results
        ],
        "cost_estimate": cost_estimate,
        "budget_mode": config["budget_mode"],
        "log_message": config["log_message"],
    }
