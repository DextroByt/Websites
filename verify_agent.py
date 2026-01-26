import httpx
import asyncio
import sys

AGENT_URL = "http://localhost:9002"

async def check_agent_state():
    print(f"Testing Agent API at {AGENT_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            # 1. Check if Agent is up
            resp = await client.get(f"{AGENT_URL}/")
            print(f"Agent UI Root: {resp.status_code}")
            
            # 2. Check Local Products Endpoint
            print("Querying /api/local_products...")
            resp = await client.get(f"{AGENT_URL}/api/local_products")
            if resp.status_code == 200:
                products = resp.json()
                print(f"📦 Agent sees {len(products)} products.")
                if len(products) == 0:
                    print("❌ FAILURE: Agent API returns empty list! Data is not persisting.")
                    return False
                else:
                    print("✅ SUCCESS: Agent has data!")
                    return True
            else:
                print(f"❌ FAILURE: Agent API returned {resp.status_code}")
                
        except Exception as e:
            print(f"❌ FAILURE: Could not connect to Agent at {AGENT_URL}")
            print(f"   Error: {e}")
    return False

if __name__ == "__main__":
    try:
        success = asyncio.run(check_agent_state())
        if not success: sys.exit(1)
    except KeyboardInterrupt:
        pass
