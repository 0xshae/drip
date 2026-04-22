import time
import httpx

from . import state

# Module-level token cache (shared across all users since we use one master key)
_cached_token: str = ""
_cached_token_expiry: int = 0

async def get_bwl_token(bwl_api_base: str, bwl_api_key: str) -> str:
    """Exchange API key for a BWL JWT token. Cache for reuse."""
    global _cached_token, _cached_token_expiry

    if _cached_token and _cached_token_expiry > time.time() + 300:
        return _cached_token

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{bwl_api_base}/v1/auth/exchange",
            json={"apiKey": bwl_api_key},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    _cached_token = data["token"]
    _cached_token_expiry = int(time.time()) + (30 * 24 * 3600)

    return _cached_token

async def _bwl_headers(bwl_api_base: str, bwl_api_key: str) -> dict:
    """Get authorization headers for BWL API calls."""
    token = await get_bwl_token(bwl_api_base, bwl_api_key)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

async def provision_container(
    bwl_api_base: str,
    bwl_api_key: str,
    user_id: str,
    container_image: str,
    env_vars: dict
) -> dict:
    """Provision a new BWL container for a user."""
    headers = await _bwl_headers(bwl_api_base, bwl_api_key)

    async with httpx.AsyncClient(timeout=60) as client:
        # 1. Create project
        await state.add_log(user_id, "creating BWL project...")
        proj_resp = await client.post(
            f"{bwl_api_base}/v1/projects",
            headers=headers,
            json={
                "name": f"drip-{user_id[:8]}",
                "description": f"Container for {user_id}",
            },
        )
        proj_resp.raise_for_status()
        project = proj_resp.json()
        project_id = project["id"]

        # 2. Create environment
        await state.add_log(user_id, "creating production environment...")
        env_resp = await client.post(
            f"{bwl_api_base}/v1/projects/{project_id}/environments",
            headers=headers,
            json={"name": "production", "type": "production"},
        )
        env_resp.raise_for_status()
        environment = env_resp.json()
        env_id = environment["id"]

        # 3. Create service with pre-built image
        await state.add_log(user_id, f"creating service from image: {container_image}")
        svc_resp = await client.post(
            f"{bwl_api_base}/v1/services",
            headers=headers,
            json={
                "projectId": project_id,
                "environmentId": env_id,
                "name": "drip-service",
                "source": {
                    "type": "image",
                    "imageUri": container_image,
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

        # 4. Set environment variables
        await client.put(
            f"{bwl_api_base}/v1/variables/service/{service_id}",
            headers=headers,
            json={
                "variables": env_vars
            },
        )

        # 5. Trigger deployment
        await state.add_log(user_id, "triggering deployment")
        deploy_resp = await client.post(
            f"{bwl_api_base}/v1/deployments",
            headers=headers,
            json={"serviceId": service_id},
        )
        deploy_resp.raise_for_status()
        deployment = deploy_resp.json()

        return {
            "service_id": service_id,
            "project_id": project_id,
            "environment_id": env_id,
            "deployment_id": deployment.get("id"),
            "service_url": service_url,
        }

async def hibernate_container(bwl_api_base: str, bwl_api_key: str, service_id: str) -> bool:
    """Pause the container (minInstances: 0)."""
    headers = await _bwl_headers(bwl_api_base, bwl_api_key)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.patch(
            f"{bwl_api_base}/v1/services/{service_id}",
            headers=headers,
            json={"runtime": {"minInstances": 0}},
        )
        resp.raise_for_status()
        return True

async def restore_container(bwl_api_base: str, bwl_api_key: str, service_id: str) -> bool:
    """Resume the container (minInstances: 1)."""
    headers = await _bwl_headers(bwl_api_base, bwl_api_key)
    async with httpx.AsyncClient(timeout=30) as client:
        # PATCH back to 1 instance
        resp = await client.patch(
            f"{bwl_api_base}/v1/services/{service_id}",
            headers=headers,
            json={"runtime": {"minInstances": 1}},
        )
        resp.raise_for_status()

        # Trigger new deployment
        deploy = await client.post(
            f"{bwl_api_base}/v1/deployments",
            headers=headers,
            json={"serviceId": service_id},
        )
        deploy.raise_for_status()
        return True
