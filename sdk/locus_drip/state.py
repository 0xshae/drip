"""SQLite database layer for Drip.

Uses aiosqlite for async access. All state lives here:
- users: per-user credit balances, BWL service IDs, status
- agent_logs: timestamped agent reasoning entries
- checkout_sessions: pending checkout sessions with webhook secrets
"""

import aiosqlite
import time
from typing import Optional, List
from pathlib import Path

DB_PATH = Path("locus_drip.db")
_db: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    """Get or create the database connection."""
    global _db
    if _db is None:
        _db = await aiosqlite.connect(str(DB_PATH))
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
    return _db


async def init_tables():
    """Create tables if they don't exist."""
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            topic TEXT NOT NULL,
            bwl_service_id TEXT,
            bwl_project_id TEXT,
            bwl_env_id TEXT,
            bwl_token TEXT,
            bwl_token_expiry INTEGER,
            status TEXT DEFAULT 'provisioning',
            balance_usdc REAL DEFAULT 0.0,
            initial_balance REAL DEFAULT 0.0,
            credit_rate REAL DEFAULT 0.05,
            plan TEXT DEFAULT 'consumption',
            plan_policy TEXT DEFAULT 'suggest_only',
            subscription_monthly_cost REAL DEFAULT 0.0,
            subscription_included_units INTEGER DEFAULT 0,
            overage_cost_per_unit REAL DEFAULT 0.0,
            billing_period_start INTEGER,
            billing_period_units_consumed INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            user_id TEXT,
            message TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS checkout_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            webhook_secret TEXT NOT NULL,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        );
    """)
    await db.commit()


# --- User CRUD ---

async def create_user(user_id: str, email: str, metadata: dict = {},
                      initial_balance: float = 0.0, consumption_unit_cost: float = 0.01,
                      plan: str = "consumption", subscription_cost: float = 0.0,
                      included_units: int = 0) -> dict:
    """Insert a new user row with billing plan support."""
    db = await get_db()
    import json
    metadata_json = json.dumps(metadata)
    now = int(time.time())
    
    await db.execute(
        """INSERT INTO users (
            user_id, email, topic, balance_usdc, initial_balance, 
            credit_rate, plan, subscription_monthly_cost, 
            subscription_included_units, billing_period_start
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id, email, metadata_json, initial_balance, initial_balance, 
            consumption_unit_cost, plan, subscription_cost, 
            included_units, now
        ),
    )
    await db.commit()
    return await get_user(user_id)


async def get_user(user_id: str) -> Optional[dict]:
    """Get a single user by ID."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_active_users() -> List[dict]:
    """Get all users with status in (active, low_credit)."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM users WHERE status IN ('active', 'low_credit')"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_all_users() -> List[dict]:
    """Get all users regardless of status."""
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def set_status(user_id: str, status: str):
    """Update user status."""
    db = await get_db()
    await db.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    await db.commit()


async def set_service_id(user_id: str, service_id: str,
                         project_id: str = None, env_id: str = None):
    """Store BWL service/project/env IDs after provisioning."""
    db = await get_db()
    await db.execute(
        """UPDATE users SET bwl_service_id = ?, bwl_project_id = ?, bwl_env_id = ?
           WHERE user_id = ?""",
        (service_id, project_id, env_id, user_id),
    )
    await db.commit()


async def update_token(user_id: str, token: str, expiry: int):
    """Cache BWL JWT token with expiry timestamp."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET bwl_token = ?, bwl_token_expiry = ? WHERE user_id = ?",
        (token, expiry, user_id),
    )
    await db.commit()


async def deduct_balance(user_id: str, amount: float):
    """Subtract credits from user balance. Floor at 0."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_usdc = MAX(0, balance_usdc - ?) WHERE user_id = ?",
        (amount, user_id),
    )
    await db.commit()


async def credit_balance(user_id: str, amount: float):
    """Add credits to user balance."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_usdc = balance_usdc + ? WHERE user_id = ?",
        (amount, user_id),
    )
    await db.commit()


async def increment_units(user_id: str, units: int = 1):
    """Track unit consumption (for subscription tier usage)."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET billing_period_units_consumed = billing_period_units_consumed + ? WHERE user_id = ?",
        (units, user_id),
    )
    await db.commit()


async def reset_billing_period(user_id: str):
    """Reset period counters at billing cycle boundary."""
    db = await get_db()
    now = int(time.time())
    await db.execute(
        """UPDATE users SET 
           billing_period_start = ?, 
           billing_period_units_consumed = 0 
           WHERE user_id = ?""",
        (now, user_id),
    )
    await db.commit()


async def get_billing_period_usage(user_id: str) -> dict:
    """Return usage stats for current billing period."""
    user = await get_user(user_id)
    if not user:
        return {}
    
    return {
        "start": user.get("billing_period_start"),
        "units_consumed": user.get("billing_period_units_consumed", 0),
        "included_units": user.get("subscription_included_units", 0),
        "plan": user.get("plan"),
        "monthly_cost": user.get("subscription_monthly_cost", 0.0)
    }


# --- Agent Logs ---

async def add_log(user_id: Optional[str], message: str):
    """Insert an agent reasoning log entry."""
    db = await get_db()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    await db.execute(
        "INSERT INTO agent_logs (ts, user_id, message) VALUES (?, ?, ?)",
        (ts, user_id, message),
    )
    await db.commit()


async def get_logs(limit: int = 50) -> List[dict]:
    """Get the most recent agent log entries."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in reversed(rows)]


# --- Checkout Sessions ---

async def create_checkout_session(session_id: str, user_id: str,
                                   amount: float, webhook_secret: str):
    """Store a pending checkout session."""
    db = await get_db()
    await db.execute(
        """INSERT INTO checkout_sessions (session_id, user_id, amount, webhook_secret)
           VALUES (?, ?, ?, ?)""",
        (session_id, user_id, amount, webhook_secret),
    )
    await db.commit()


async def get_checkout_session(session_id: str) -> Optional[dict]:
    """Look up a checkout session by ID."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM checkout_sessions WHERE session_id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_user(user_id: str):
    """Delete a user from the database."""
    db = await get_db()
    await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    await db.commit()


async def clear_logs():
    """Clear all agent logs."""
    db = await get_db()
    await db.execute("DELETE FROM agent_logs")
    await db.commit()


async def set_balance(user_id: str, amount: float):
    """Set user balance to an exact amount (for demo resets)."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_usdc = ? WHERE user_id = ?",
        (amount, user_id),
    )
    await db.commit()


async def get_logs_after(after_id: int, limit: int = 50) -> List[dict]:
    """Get log entries with id > after_id (for incremental streaming)."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_logs WHERE id > ? ORDER BY id ASC LIMIT ?",
        (after_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]





async def close_db():
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
