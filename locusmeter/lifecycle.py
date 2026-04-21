"""BWL container lifecycle management.

Handles:
- JWT token exchange and caching
- Provisioning new user containers
- Scale-to-zero teardown
- Scale-back-up restore
"""

import os
import time
import httpx

from locusmeter import db

BWL_API_BASE = os.getenv("BWL_API_BASE", "https://beta-api.buildwithlocus.com")
BWL_API_KEY = os.getenv("BWL_API_KEY", "")
GHCR_IMAGE = os.getenv("GHCR_IMAGE", "ghcr.io/0xshae/locusmeter-research:latest")

# Module-level token cache (shared across all users since we use one master key)
_cached_token: str = ""
_cached_token_expiry: int = 0


async def get_bwl_token() -> str:
    """Exchange claw_dev API key for a BWL JWT token. Cache for reuse."""
    global _cached_token, _cached_token_expiry

    # Return cached token if still valid (with 5-minute buffer)
    if _cached_token and _cached_token_expiry > time.time() + 300:
        return _cached_token

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{BWL_API_BASE}/v1/auth/exchange",
            json={"apiKey": BWL_API_KEY},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    _cached_token = data["token"]
    # Tokens expire in 30 days; cache with same expiry
    _cached_token_expiry = int(time.time()) + (30 * 24 * 3600)

    return _cached_token


async def _bwl_headers() -> dict:
    """Get authorization headers for BWL API calls."""
    token = await get_bwl_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


async def provision(user_id: str) -> dict:
    """Provision a new BWL container for a user.

    Steps:
    1. Create a project
    2. Create a production environment
    3. Create a service (pre-built Docker image)
    4. Set environment variables
    5. Trigger deployment
    """
    headers = await _bwl_headers()
    user = await db.get_user(user_id)

    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Create project
        await db.add_log(user_id, "creating BWL project...")
        proj_resp = await client.post(
            f"{BWL_API_BASE}/v1/projects",
            headers=headers,
            json={
                "name": f"drip-{user_id[:8]}",
                "description": f"Research container for {user_id}",
            },
        )
        proj_resp.raise_for_status()
        project = proj_resp.json()
        project_id = project["id"]

        # 2. Create environment
        await db.add_log(user_id, "creating production environment...")
        env_resp = await client.post(
            f"{BWL_API_BASE}/v1/projects/{project_id}/environments",
            headers=headers,
            json={"name": "production", "type": "production"},
        )
        env_resp.raise_for_status()
        environment = env_resp.json()
        env_id = environment["id"]

        # 3. Create service with pre-built image
        await db.add_log(user_id, f"creating service from image: {GHCR_IMAGE}")
        svc_resp = await client.post(
            f"{BWL_API_BASE}/v1/services",
            headers=headers,
            json={
                "projectId": project_id,
                "environmentId": env_id,
                "name": "research",
                "source": {
                    "type": "image",
                    "imageUri": GHCR_IMAGE,
                },
                "runtime": {
                    "port": 8080,
                    "cpu": 256,
                    "memory": 512,
                    "minInstances": 1,
                    "maxInstances": 1,
                },
                "healthCheckPath": "/health",
            },
        )
        svc_resp.raise_for_status()
        service = svc_resp.json()
        service_id = service["id"]
        service_url = service.get("url", "")

        # Store IDs in SQLite
        await db.set_service_id(user_id, service_id, project_id, env_id)

        # 4. Set environment variables for the research container
        locus_api_key = os.getenv("LOCUS_API_KEY", "")
        drip_url = os.getenv("DRIP_URL", "")  # Set after Drip itself is deployed

        await client.put(
            f"{BWL_API_BASE}/v1/variables/service/{service_id}",
            headers=headers,
            json={
                "variables": {
                    "LOCUS_API_KEY": locus_api_key,
                    "LOCUSMETER_URL": drip_url,
                    "USER_ID": user_id,
                    "TOPIC": user.get("topic", ""),
                }
            },
        )

        # 5. Trigger deployment
        await db.add_log(user_id, "triggering deployment — this takes 1-2 minutes for pre-built images")
        deploy_resp = await client.post(
            f"{BWL_API_BASE}/v1/deployments",
            headers=headers,
            json={"serviceId": service_id},
        )
        deploy_resp.raise_for_status()
        deployment = deploy_resp.json()

        # Mark user as active
        await db.set_status(user_id, "active")

        return {
            "service_id": service_id,
            "project_id": project_id,
            "env_id": env_id,
            "deployment_id": deployment.get("id"),
            "service_url": service_url,
        }


async def teardown(user_id: str):
    """Scale user's container to zero (hibernate).

    Uses PATCH to set minInstances=0. Service definition is preserved,
    container just stops running. State survives in managed Postgres.
    """
    user = await db.get_user(user_id)
    if not user or not user.get("bwl_service_id"):
        await db.add_log(user_id, "teardown skipped — no service ID found")
        return

    # Idempotent: skip if already paused
    if user.get("status") == "paused":
        await db.add_log(user_id, "teardown skipped — already paused")
        return

    headers = await _bwl_headers()
    service_id = user["bwl_service_id"]

    async with httpx.AsyncClient(timeout=30) as client:
        await db.add_log(user_id,
                         f"balance 0.00 — hibernating container (minInstances=0)")
        resp = await client.patch(
            f"{BWL_API_BASE}/v1/services/{service_id}",
            headers=headers,
            json={"runtime": {"minInstances": 0}},
        )
        resp.raise_for_status()

    await db.set_status(user_id, "paused")
    await db.add_log(user_id, "container paused — user notified with recharge link")


async def restore(user_id: str):
    """Scale user's container back up + trigger new deployment.

    1. PATCH minInstances back to 1
    2. POST new deployment
    """
    user = await db.get_user(user_id)
    if not user or not user.get("bwl_service_id"):
        await db.add_log(user_id, "restore skipped — no service ID found")
        return

    headers = await _bwl_headers()
    service_id = user["bwl_service_id"]

    async with httpx.AsyncClient(timeout=30) as client:
        await db.add_log(user_id, "credits replenished — restoring container")

        # PATCH back to 1 instance
        await client.patch(
            f"{BWL_API_BASE}/v1/services/{service_id}",
            headers=headers,
            json={"runtime": {"minInstances": 1}},
        )

        # Trigger new deployment
        await db.add_log(user_id, "triggering deployment — waking up research agent")
        await client.post(
            f"{BWL_API_BASE}/v1/deployments",
            headers=headers,
            json={"serviceId": service_id},
        )

    await db.set_status(user_id, "restoring")
    await db.add_log(user_id, "container waking up — research agent coming back online")


async def check_deployment_status(user_id: str, deployment_id: str) -> str:
    """Poll a deployment's status. Returns: queued, building, deploying, healthy, failed."""
    headers = await _bwl_headers()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BWL_API_BASE}/v1/deployments/{deployment_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json().get("status", "unknown")


async def check_service_runtime(user_id: str) -> dict:
    """Check a service's runtime instance counts."""
    user = await db.get_user(user_id)
    if not user or not user.get("bwl_service_id"):
        return {"runningCount": 0, "desiredCount": 0}

    headers = await _bwl_headers()
    service_id = user["bwl_service_id"]

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BWL_API_BASE}/v1/services/{service_id}?include=runtime",
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("runtime_instances", {})
