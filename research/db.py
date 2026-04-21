"""Postgres connection for the research container.

Uses the DATABASE_URL injected by BWL managed Postgres addon.
Stores topics and digests, namespaced by user_id.
"""

import os
from typing import Optional, List

# In demo mode, we use a simple in-memory store
# In production, this would use asyncpg with the BWL Postgres addon
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# In-memory store for demo
_topics = {}
_digests = []


async def init_research_db():
    """Initialize the research database tables."""
    if DEMO_MODE:
        return

    # Production: use asyncpg with DATABASE_URL
    # DATABASE_URL is auto-injected by BWL managed Postgres addon
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        print("WARNING: DATABASE_URL not set — using in-memory store")
        return

    # Would use asyncpg here in production
    pass


async def save_topic(user_id: str, topic: str):
    """Save or update a user's research topic."""
    _topics[user_id] = topic


async def get_topic(user_id: str) -> Optional[str]:
    """Get a user's current research topic."""
    return _topics.get(user_id)


async def save_digest(user_id: str, content: str, sources_used: int,
                      cost_usdc: float):
    """Save a completed research digest."""
    _digests.append({
        "user_id": user_id,
        "content": content,
        "sources_used": sources_used,
        "cost_usdc": cost_usdc,
    })


async def get_digests(user_id: str, limit: int = 10) -> List[dict]:
    """Get recent digests for a user."""
    user_digests = [d for d in _digests if d["user_id"] == user_id]
    return user_digests[-limit:]
