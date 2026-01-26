import subprocess
import time
import requests
import sys

# Configuration
RIO_URL = "http://localhost:9001"
AGENT_URL = "http://localhost:9002"
API_KEY = "rio_sk_live_7384928492"

def main():
    print("🚀 Starting Enterprise Simulation Verification...")

    # 1. Start RioMart
    print("   Starting RioMart Warehouse (Port 9001)...")
    rio_proc = subprocess.Popen([sys.executable, "main.py"], cwd="RioMart_Warehouse")
    
    # 2. Start Supply Agent
    print("   Starting Supply Agent (Port 9002)...")
    agent_proc = subprocess.Popen([sys.executable, "app.py"], cwd="Supply_Agent")
    
    # Wait for Startup
    time.sleep(5)
    
    try:
        # 3. Check RioMart Health
        try:
            resp = requests.get(f"{RIO_URL}/logs/stream")
            if resp.status_code == 200:
                print("   ✅ RioMart is Online")
            else:
                print(f"   ❌ RioMart User Interface Error: {resp.status_code}")
        except:
            print("   ❌ RioMart Connection Failed")

        # 4. Check Agent Health
        try:
            resp = requests.get(f"{AGENT_URL}/status")
            status = resp.json()
            if status.get("running"):
                print("   ✅ Supply Agent is Online & Active")
            else:
                print("   ❌ Supply Agent Paused?")
        except:
            print("   ❌ Supply Agent Connection Failed")

        # 5. Verify Auth Block
        print("\n🔐 Verifying Security Layer...")
        try:
            # Try to order without key
            resp = requests.post(f"{RIO_URL}/api/v1/order", json={"items": []})
            if resp.status_code == 403 or resp.status_code == 401:
                print("   ✅ Security Active: Unauthorized Request Blocked (403/401)")
            else:
                print(f"   ❌ Security Fail: Request allowed without key ({resp.status_code})")
        except Exception as e:
            print(f"   ⚠️ Test Error: {e}")

        # 6. Wait for a simulated cycle (Automated Logistics)
        print("\n⏳ Waiting 15s for automated logistics cycle...")
        time.sleep(15)
        
        # 7. Check if Agent Placed any Orders
        print("\n📦 Verifying Automated Supply Chain...")
        try:
            # Check Agent Logs
            resp = requests.get(f"{AGENT_URL}/logs")
            logs = resp.json()
            
            order_confirmed = any("Order Confirmed" in log['msg'] for log in logs)
            catalog_fetched = any("Discovering Supplier Catalog" in log['msg'] for log in logs)
            
            if catalog_fetched:
                print("   ✅ Agent Successfully Discovered RioMart Catalog")
            else:
                print("   ⚠️ Agent didn't report fetching catalog yet.")

            if order_confirmed:
                print("   ✅ SUCCESS: Agent autonomously placed an order!")
            else:
                print("   ℹ️ No orders yet (Inventory might be sufficient). Checking low stock...")
                # Force consumption?
                # For this test, we just check if it's running correctly.
                
        except Exception as e:
            print(f"   ❌ Verification Failed: {e}")

    finally:
        print("\n🛑 Shutting down servers...")
        rio_proc.terminate()
        agent_proc.terminate()
        
if __name__ == "__main__":
    main()
