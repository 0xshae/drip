import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

BWL_API_BASE = os.getenv("BWL_API_BASE", "https://beta-api.buildwithlocus.com")
BWL_API_KEY = os.getenv("BWL_API_KEY")

async def get_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BWL_API_BASE}/v1/auth/exchange",
            json={"apiKey": BWL_API_KEY}
        )
        resp.raise_for_status()
        return resp.json()["token"]

async def deploy():
    token = await get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        # 1. List projects to find where "drip" might be
        print("Listing projects...")
        resp = await client.get(f"{BWL_API_BASE}/v1/projects", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        projects = data.get("projects", [])
        print(f"Found {len(projects)} projects")
        
        drip_service = None
        for project in projects:
            project_id = project["id"]
            print(f"Checking project: {project['name']} ({project_id})")
            
            # 2. List services in this project
            resp = await client.get(f"{BWL_API_BASE}/v1/projects/{project_id}/services", headers=headers)
            print(f"  Services status: {resp.status_code}")
            if resp.status_code == 200:
                services_data = resp.json()
                services = services_data.get("services", []) if isinstance(services_data, dict) else services_data
                print(f"  Services: {[s['name'] for s in services]}")
                drip_service = next((s for s in services if s["name"].lower() in ("drip", "locus-drip", "dashboard")), None)
                if drip_service:
                    print(f"  Matched service: {drip_service['name']}")
                    break
            else:
                print(f"  Error: {resp.text}")
        
        if not drip_service:
            print("Drip service not found in any project")
            return
        
        service_id = drip_service["id"]
        print(f"Found drip service: {service_id}")
        
        # 3. Trigger deployment
        print(f"Triggering deployment for {service_id}...")
        resp = await client.post(
            f"{BWL_API_BASE}/v1/deployments",
            headers=headers,
            json={"serviceId": service_id}
        )
        resp.raise_for_status()
        print("Deployment triggered successfully!")
        print(resp.json())

if __name__ == "__main__":
    asyncio.run(deploy())
