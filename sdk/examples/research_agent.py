"""
Example: A pay-per-use Research Agent using the Drip SDK.
"""
import asyncio
import os
from locus_drip import DripClient, DripConfig
from locus_drip.exceptions import DripInsufficientCredits

client = DripClient(DripConfig(
    locus_api_key=os.environ.get("LOCUS_API_KEY", ""),
    bwl_api_key=os.environ.get("BWL_API_KEY", ""),
    agentmail_inbox=os.environ.get("AGENTMAIL_INBOX", ""),
))

@client.meter(cost=0.007, event="exa_search", user_id_param="user_id")
async def search_exa(topic: str, user_id: str):
    print(f"[{user_id}] Searching Exa for {topic} (-$0.007 USDC)")
    await asyncio.sleep(1) # mock API call
    return f"Search results for {topic}"

@client.meter(cost=0.003, event="firecrawl_scrape", user_id_param="user_id")
async def scrape_firecrawl(url: str, user_id: str):
    print(f"[{user_id}] Scraping {url} (-$0.003 USDC)")
    await asyncio.sleep(1) # mock API call
    return f"Scraped content from {url}"

@client.meter(cost=0.015, event="claude_synthesize", user_id_param="user_id")
async def synthesize(content: str, user_id: str):
    print(f"[{user_id}] Synthesizing content (-$0.015 USDC)")
    await asyncio.sleep(1) # mock API call
    return "Final summarized research digest"

async def run_research_loop(user_id: str, topic: str):
    try:
        results = await search_exa(topic=topic, user_id=user_id)
        scraped = await scrape_firecrawl(url="https://example.com/source", user_id=user_id)
        digest = await synthesize(content=f"{results}\n{scraped}", user_id=user_id)
        print(f"[{user_id}] SUCCESS: {digest}")
    except DripInsufficientCredits:
        print(f"[{user_id}] HALTED: Insufficient credits. Please top up.")

async def main():
    await client.init_db()
    
    user_id = "demo_user"
    await client.provision_user(user_id, "user@example.com", initial_balance=0.05)
    
    print("\n--- Starting Research ---")
    await run_research_loop(user_id, "Quantum Computing")
    
    user = await client.get_user(user_id)
    print(f"Remaining balance: {user['balance_usdc']} USDC")

if __name__ == "__main__":
    asyncio.run(main())
