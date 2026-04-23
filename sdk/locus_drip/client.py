import asyncio
from dataclasses import dataclass
from typing import Optional, Any
from functools import wraps

from . import state
from . import wallet
from . import lifecycle
from .notifications import send_agentmail_notification
from .exceptions import DripInsufficientCredits, DripUserNotFound

@dataclass
class DripSubscriptionConfig:
    monthly_cost_usdc: float      # e.g., 20.0
    included_units: int           # e.g., 1000
    overage_cost_per_unit: float  # e.g., 0.007
    cycle_day: int = 1            # which day of month billing resets


@dataclass
class DripConfig:
    locus_api_key: str
    bwl_api_key: str
    agentmail_inbox: str
    locus_api_base: str = "https://beta-api.paywithlocus.com/api"
    bwl_api_base: str = "https://beta-api.buildwithlocus.com"
    poll_interval_seconds: int = 60
    mock_drain: bool = False
    api_key: Optional[str] = None  # Unified Drip API key (Future)

class DripClient:
    def __init__(self, config: DripConfig):
        self.config = config

    async def init_db(self):
        """Initialize the database tables."""
        await state.init_tables()

    async def provision_user(
        self,
        user_id: str,
        email: str,
        plan: str = "consumption",
        initial_balance: float = 0.0,
        consumption_unit_cost: float = 0.01,
        subscription_cost: float = 0.0,
        included_units: int = 0,
        container_image: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Create a user and provision a container for them."""
        # Check if user exists
        existing = await state.get_user(user_id)
        if existing:
            return existing

        user = await state.create_user(
            user_id=user_id,
            email=email,
            metadata=metadata or {},
            initial_balance=initial_balance,
            consumption_unit_cost=consumption_unit_cost,
            plan=plan,
            subscription_cost=subscription_cost,
            included_units=included_units
        )
        
        await state.add_log(user_id, f"new user registered — balance: {initial_balance:.2f} USDC")

        if container_image:
            try:
                env_vars = {
                    "USER_ID": user_id,
                    "LOCUS_API_KEY": self.config.locus_api_key,
                    "LOCUS_API_BASE": self.config.locus_api_base,
                    "AGENTMAIL_INBOX": self.config.agentmail_inbox,
                }
                result = await lifecycle.provision_container(
                    bwl_api_base=self.config.bwl_api_base,
                    bwl_api_key=self.config.bwl_api_key,
                    user_id=user_id,
                    container_image=container_image,
                    env_vars=env_vars
                )
                await state.set_service_id(
                    user_id,
                    result["service_id"],
                    result.get("project_id"),
                    result.get("environment_id")
                )
                await state.set_status(user_id, "active")
                await state.add_log(user_id, "container provisioned on BuildWithLocus")
            except Exception as e:
                await state.set_status(user_id, "failed")
                await state.add_log(user_id, f"provision failed: {e}")
                raise
        else:
            await state.set_status(user_id, "active")
            await state.add_log(user_id, "user provisioned (no container)")

        return await state.get_user(user_id)

    async def get_user(self, user_id: str) -> dict:
        """Get user state."""
        user = await state.get_user(user_id)
        if not user:
            raise DripUserNotFound(f"User {user_id} not found")
        return user

    async def debit(self, user_id: str, amount: float, label: str):
        """Debit credits from a user. Raises DripInsufficientCredits if empty."""
        user = await self.get_user(user_id)
        
        if user["balance_usdc"] < amount:
            raise DripInsufficientCredits(f"User {user_id} lacks {amount} USDC")

        await state.deduct_balance(user_id, amount)
        await state.add_log(user_id, f"debited {amount:.4f} USDC for {label}")

    async def hibernate(self, user_id: str):
        """Manually hibernate a user's container."""
        user = await self.get_user(user_id)
        if user.get("bwl_service_id"):
            await lifecycle.hibernate_container(
                self.config.bwl_api_base,
                self.config.bwl_api_key,
                user["bwl_service_id"]
            )
        await state.set_status(user_id, "paused")
        await state.add_log(user_id, "container hibernated to zero")

    async def restore(self, user_id: str):
        """Manually restore a user's container."""
        user = await self.get_user(user_id)
        if user.get("bwl_service_id"):
            await lifecycle.restore_container(
                self.config.bwl_api_base,
                self.config.bwl_api_key,
                user["bwl_service_id"]
            )
        await state.set_status(user_id, "active")
        await state.add_log(user_id, "container restored")

    async def topup(self, user_id: str, amount: float):
        """Top up a user's balance and auto-restore if paused."""
        user = await self.get_user(user_id)
        
        await state.set_balance(user_id, user["balance_usdc"] + amount)
        await state.add_log(user_id, f"top-up received: {amount:.2f} USDC")

        user = await self.get_user(user_id)
        if user["status"] == "paused" and user["balance_usdc"] > 0:
            await self.restore(user_id)

    def meter(
        self,
        cost: float,
        event: str,
        user_id_param: str = "user_id",
        unit: int = 1,
        label: Optional[str] = None,
        dry_run: bool = False
    ):
        """Decorator to meter an async function.
        
        Supports unit tracking for subscription plans.
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user_id = kwargs.get(user_id_param)
                if not user_id:
                    raise ValueError(f"Missing kwarg {user_id_param}")

                if not dry_run:
                    # Debit balance (for consumption or overages)
                    await self.debit(user_id, cost, label or event)
                    # Track units (for subscription quotas)
                    await state.increment_units(user_id, unit)
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    async def start_polling(self):
        """Start the background polling loop."""
        await state.add_log(None, f"agent loop started — polling every {self.config.poll_interval_seconds}s")
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                users = await state.get_active_users()
                for user in users:
                    user_id = user["user_id"]

                    # 1. Handle Low Credit / Teardown
                    pct = user["balance_usdc"] / max(user["initial_balance"], 0.01)
                    if pct <= 0 and user["status"] == "active":
                        await state.add_log(user_id, "balance depleted — triggering teardown")
                        await self.hibernate(user_id)
                        await send_agentmail_notification(
                            self.config.locus_api_base, self.config.locus_api_key, self.config.agentmail_inbox,
                            user_id, user["email"], user["balance_usdc"], "paused", user.get("metadata")
                        )
                    elif 0 < pct <= 0.2 and user["status"] == "active":
                        await state.set_status(user_id, "low_credit")
                        await state.add_log(user_id, f"balance <20% ({user['balance_usdc']:.2f}) — sending warning")
                        await send_agentmail_notification(
                            self.config.locus_api_base, self.config.locus_api_key, self.config.agentmail_inbox,
                            user_id, user["email"], user["balance_usdc"], "low_credit", user.get("metadata")
                        )

                    # 2. Plan Optimization Intelligence (Hybrid Billing)
                    # If user is on 'consumption' but trending towards 'subscription' being cheaper
                    if user["plan"] == "consumption" and user["subscription_monthly_cost"] > 0:
                        usage = await state.get_billing_period_usage(user_id)
                        units = usage.get("units_consumed", 0)
                        cost_so_far = units * user["credit_rate"] # using credit_rate as per-unit cost
                        
                        if cost_so_far >= user["subscription_monthly_cost"] * 0.8:
                            # User is at 80% of subscription cost — suggest switch
                            await state.add_log(user_id, f"intelligence: user usage ({cost_so_far:.2f}) approaching subscription cost ({user['subscription_monthly_cost']:.2f})")
                            # Only suggest once per period (could track this in metadata)
                            await send_agentmail_notification(
                                self.config.locus_api_base, self.config.locus_api_key, self.config.agentmail_inbox,
                                user_id, user["email"], user["balance_usdc"], "plan_suggestion", user.get("metadata")
                            )

                # Periodic master wallet check (every 10 cycles)
                if cycle_count % 10 == 0:
                    master_balance = await wallet.check_master_wallet_balance(
                        self.config.locus_api_base,
                        self.config.locus_api_key
                    )
                    if master_balance >= 0:
                        await state.add_log(None, f"master wallet audit: {master_balance:.2f} USDC")
                        if master_balance < 1.0:
                            await state.add_log(None, "⚠️ CRITICAL: master wallet below $1.00 — all user API calls may fail!")

            except asyncio.CancelledError:
                raise
            except Exception as e:
                await state.add_log(None, f"polling loop error (recovering): {str(e)[:200]}")
            
            await asyncio.sleep(self.config.poll_interval_seconds)
