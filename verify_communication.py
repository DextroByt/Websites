import httpx
import asyncio
import sys

TARGET_URL = "http://localhost:9001"
API_KEY = "rio_sk_live_7384928492"

async def check_warehouse():
    print(f"Testing connection to {TARGET_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            # 1. Health Check (Root)
            resp = await client.get(f"{TARGET_URL}/")
            print(f"Root endpoint: {resp.status_code} (Expected 200/404)")
            
            # 2. Auth Check
            print("Verifying API Key...")
            resp = await client.get(f"{TARGET_URL}/api/v1/products", headers={"X-API-KEY": API_KEY})
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Connected to Warehouse! Found {len(resp.json())} products.")
                return True
            elif resp.status_code == 403:
                print("❌ FAILURE: API Key Rejected (403).")
            else:
                print(f"❌ FAILURE: Unexpected Status {resp.status_code}")
                
        except Exception as e:
            print(f"❌ FAILURE: Could not connect to Warehouse at {TARGET_URL}")
            print(f"   Error: {e}")
            print("   Make sure 'python main.py' is running in another terminal!")
    return False

if __name__ == "__main__":
    try:
        success = asyncio.run(check_warehouse())
        if not success: sys.exit(1)
    except KeyboardInterrupt:
        pass
