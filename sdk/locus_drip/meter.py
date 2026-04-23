from typing import Optional
from .client import DripClient, DripConfig

# Global singleton
_client: Optional[DripClient] = None

def configure(config: DripConfig):
    global _client
    _client = DripClient(config)

def meter(
    cost: float,
    event: str,
    user_id_param: str = "user_id",
    unit: int = 1,
    label: Optional[str] = None,
    dry_run: bool = False,
):
    """Global decorator to meter an async function.
    Requires drip.configure() to be called first.
    """
    global _client
    if not _client:
        raise RuntimeError("Drip is not configured. Call drip.configure() or use DripClient.meter().")
    return _client.meter(cost, event, user_id_param, unit, label, dry_run)
