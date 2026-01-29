from fastapi import FastAPI, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
import asyncio
import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Internal Modules
from forecasting import DemandSimulator
from purchasing import LogisticsEngine
from secure_netra_client import ProfessionalNetraClient  # [NEW]

templates = Jinja2Templates(directory="templates")

# CONFIGURATION
TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:9005") # The Local Egress Proxy
DESTINATION_URL = os.environ.get("LAPTOP_B_INGRESS_URL", "http://localhost:8000") # The Final Destination
API_KEY = "rio_sk_live_7384928492" # The key we seeded in RioMart

# Initialize Secure Client
netra_client = ProfessionalNetraClient(TARGET_URL, API_KEY)

# STATE
agent_running = True
agent_logs = [] 

# Initialize Simulation (Manage 5 random SKUs we know exist in RioMart)
# Ideally we would fetch the catalog first, but we will seed some dummy SKUs
# that likely match the faker data or we learn them.
# For robustness, let's fetch the catalog on startup.
MANAGED_SKUS = [] 
MANAGED_PRODUCTS = []
simulator = None
engine = None

class AttackRequest(BaseModel):
    category: str
    type: str
    endpoint: str
    payload: dict

ATTACKS = {
    "SQLi": {
        "desc": "Injects malicious SQL commands into input fields.",
        "payload": {"items": [{"sku": "' OR '1'='1 --", "quantity": 1}]},
        "endpoint": "/api/v1/order"
    },
    "BOLA": {
        "desc": "Broken Authorization / IDOR Test.",
        "payload": {"order_id": 101, "action": "view"},
        "endpoint": "/api/v1/order/view" 
    },
    "LargePayload": {
        "desc": "Stress Test with large JSON body.",
        "payload": {"items": [{"sku": "TEST-SKU", "quantity": 1}] * 500}, 
        "endpoint": "/api/v1/order"
    },
     "API_Hijack": {
        "desc": "Man-In-The-Middle simulation (Price Manipulation).",
        "payload": {"items": [{"sku": "Expensive_Item", "quantity": 10}], "price_override": 0.01},
        "endpoint": "/api/v1/order"
    }
}

def _now():
    return datetime.datetime.now().strftime("%H:%M:%S")

def add_log(entry):
    """Helper to log to memory and console"""
    print(f"[{entry['time']}] {entry['type']} : {entry['msg']}")
    agent_logs.append(entry)

# --- INTELLIGENT AUTO-AGENT (Background) ---
async def supply_chain_manager():
    global simulator, engine, MANAGED_SKUS, MANAGED_PRODUCTS, agent_running
    
    # 1. Discovery Phase: Fetch Catalog (With Retry)
    while True:
        try:
            add_log({"time": _now(), "msg": "🔍 Discovering Supplier Catalog...", "type": "NORMAL"})
            
            # Routing Header: Tell the Egress Proxy where to send this
            routing_headers = {"X-Target-URL": DESTINATION_URL}
            
            # Uses netra_client.get which adds Auth/Sig headers automatically
            resp = await netra_client.get("/api/v1/products", headers=routing_headers)
            
            if resp.status_code == 200:
                products = resp.json()
                MANAGED_SKUS = [p['sku'] for p in products] # Manage ALL discovered products
                MANAGED_PRODUCTS = products # Store full details for UI
                simulator = DemandSimulator(MANAGED_SKUS)
                engine = LogisticsEngine(simulator)
                add_log({"time": _now(), "msg": f"✅ Managing Supply Chain for {len(MANAGED_SKUS)} SKUs", "type": "NORMAL"})
                break # Success! Exit discovery loop
            else:
                 add_log({"time": _now(), "msg": f"❌ Catalog Fetch Failed ({resp.status_code}). Retrying in 5s...", "type": "ERROR"})
        except Exception as e:
            add_log({"time": _now(), "msg": f"❌ Connection Retry: {e}", "type": "ERROR"})
        
        await asyncio.sleep(5)

    # 2. Operational Loop
    while True:
        if not agent_running:
            await asyncio.sleep(2)
            continue
            
        try:
            # A. Simulate Consumption (Factory running)
            consumed = simulator.consume()
            if consumed:
                 total_used = sum(c['used'] for c in consumed)

            # B. Evaluate Stock & Reorder
            orders_needed = engine.evaluate_needs()
            
            if orders_needed:
                for order in orders_needed:
                    sku = order['sku']
                    qty = order['quantity']
                    
                    add_log({"time": _now(), "msg": f"📉 Low Stock ({sku}). Placing Order for {qty}...", "type": "WARNING"})
                    
                    # Place Order via API
                    payload = {"items": [{"sku": sku, "quantity": qty}]}
                    
                    # Routing Header
                    routing_headers = {"X-Target-URL": DESTINATION_URL}
                    
                    # Secure POST
                    order_resp = await netra_client.post("/api/v1/order", payload, headers=routing_headers)
                    
                    if order_resp.status_code == 200:
                        data = order_resp.json()
                        add_log({"time": _now(), "msg": f"✅ Order Confirmed: ID {data.get('order_id')}", "type": "SUCCESS"})
                        # Receive Goods
                        engine.update_stock_after_delivery(sku, qty)
                    else:
                        try:
                            err_detail = order_resp.json().get('detail', order_resp.text)
                        except:
                            err_detail = order_resp.text
                        add_log({"time": _now(), "msg": f"❌ Order Rejected: {err_detail}", "type": "ERROR"})
            
        except Exception as e:
            pass # agent_logs.append({"time": _now(), "msg": f"Loop Error: {e}", "type": "ERROR"})
        
        await asyncio.sleep(5) 

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(supply_chain_manager())
    yield
    # Shutdown
    pass

app = FastAPI(title="ShopMart Agent (Agent A)", lifespan=lifespan)

# Enable CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory="templates")

# ... (Configuration & State are fine) ...

# --- DASHBOARD ROUTES ---
@app.get("/", response_class=HTMLResponse)
def get_dashboard(request: Request):
    return templates.TemplateResponse("console.html", {"request": request})

@app.get("/api/stats")
def get_stats():
    """Returns local inventory state for the UI"""
    if simulator:
        return {
            "inventory": simulator.local_inventory,
            "running": agent_running
        }
    return {"inventory": {}, "running": agent_running}

@app.get("/api/local_products")
def get_local_cached_products():
    """Returns the products discovered by the agent."""
    print(f"DEBUG: Serving {len(MANAGED_PRODUCTS)} products to UI")
    return MANAGED_PRODUCTS


@app.get("/logs")
def view_agent_activity():
    return agent_logs[-50:]

@app.post("/control/test_order")
async def manual_test_order():
    """Manually triggers a valid order to verify connectivity."""
    # global API_KEY # Handled inside client now
    agent_logs.append({"time": _now(), "msg": "🧪 Sending Manual Test Order...", "type": "NORMAL"})
    
    try:
        # Routing Header
        routing_headers = {"X-Target-URL": DESTINATION_URL}

        # 1. Get a product first
        cat_resp = await netra_client.get("/api/v1/products", headers=routing_headers)
        if cat_resp.status_code != 200:
                agent_logs.append({"time": _now(), "msg": f"❌ Test Failed: Cannot fetch catalog ({cat_resp.status_code})", "type": "ERROR"})
                return {"status": "failed"}
        
        products = cat_resp.json()
        if not products:
                agent_logs.append({"time": _now(), "msg": "❌ Test Failed: Catalog Empty", "type": "ERROR"})
                return {"status": "failed"}

        # 2. Order the first product
        target = products[0]
        payload = {"items": [{"sku": target['sku'], "quantity": 1}]}
        
        order_resp = await netra_client.post("/api/v1/order", payload, headers=routing_headers)
        
        if order_resp.status_code == 200:
            data = order_resp.json()
            agent_logs.append({"time": _now(), "msg": f"✅ Test Success: Order {data.get('order_id')} Confirmed!", "type": "SUCCESS"})
            return {"status": "success"}
        else:
            agent_logs.append({"time": _now(), "msg": f"❌ Test Rejected: {order_resp.text}", "type": "ERROR"})
            return {"status": "rejected"}
                
    except Exception as e:
        agent_logs.append({"time": _now(), "msg": f"❌ Test Connection Error: {e}", "type": "ERROR"})
        return {"status": "error"}

@app.post("/control/manual_request")
async def manual_request_order(payload: dict):
    """Handles manual order form submission from the UI."""
    # payload = {sku: str, quantity: int}
    
    sku = payload.get('sku')
    try:
        qty = int(payload.get('quantity', 0))
    except:
        return {"status": "error", "message": "Invalid Quantity"}
        
    if not sku or qty <= 0:
        return {"status": "error", "message": "Invalid Parameters"}

    add_log({"time": _now(), "msg": f"📤 Manual Request: {sku} (Qty: {qty})...", "type": "NORMAL"})

    try:
        api_payload = {"items": [{"sku": sku, "quantity": qty}]}
        
        # Routing Header
        routing_headers = {"X-Target-URL": DESTINATION_URL}

        # Secure POST
        order_resp = await netra_client.post("/api/v1/order", api_payload, headers=routing_headers)
        
        if order_resp.status_code == 200:
            data = order_resp.json()
            # Update local stock since we just bought it
            if engine: engine.update_stock_after_delivery(sku, qty)
            
            success_msg = f"✅ Request Approved: Warehouse Order #{data.get('order_id')}"
            add_log({"time": _now(), "msg": success_msg, "type": "SUCCESS"})
            return {"status": "success", "message": str(data)}
        else:
            err_msg = f"❌ Request Denied: {order_resp.text}"
            add_log({"time": _now(), "msg": err_msg, "type": "ERROR"})
            return {"status": "rejected", "message": order_resp.text}
            
    except Exception as e:
        add_log({"time": _now(), "msg": f"❌ Connection Error: {e}", "type": "ERROR"})
        return {"status": "error", "message": str(e)}

@app.post("/control/{action}")
def control_agent(action: str):
    global agent_running, agent_logs
    if action == "stop":
        agent_running = False
        agent_logs.append({"time": _now(), "msg": "🛑 AGENT PAUSED", "type": "NORMAL"})
    elif action == "start":
        agent_running = True
        agent_logs.append({"time": _now(), "msg": "▶ AGENT RESUMED", "type": "NORMAL"})
    elif action == "clear_logs":
        agent_logs = []
    return {"status": "ok"}

@app.post("/launch_attack")
async def trigger_attack(attack: AttackRequest):
    attack_def = ATTACKS.get(attack.type)
    if not attack_def: return {"error": "Unknown Attack"}
    
    agent_logs.append({"time": _now(), "msg": f"⚡ EXECUTING RED TEAM ATTACK: {attack.type}", "type": "ATTACK"})
    
    try:
        # --- SMART AUTOMATION: BOLA ENUMERATION ---
        if attack.type == "BOLA":
            agent_logs.append({"time": _now(), "msg": "🕵️ Smart Attack: Enumerating IDs 1-10...", "type": "NORMAL"})
            found = False
            for i in range(1, 11):
                # Override payload with dynamic ID
                dynamic_payload = {"order_id": i} 
                # Secure Client used even for attacks (to get past WAF/Auth)
                resp = await netra_client.post(attack_def['endpoint'], dynamic_payload)
                
                if resp.status_code == 200:
                        data = resp.json()
                        msg = f"🔥 VULNERABILITY FOUND: Stole Order #{i} (Owned by {data.get('customer')})"
                        agent_logs.append({"time": _now(), "msg": msg, "type": "WARNING"}) # Warning = Vulnerability Found
                        found = True
                        break # Stop after first success
            
            if not found:
                    agent_logs.append({"time": _now(), "msg": "❌ Enumeration Failed: No valid orders found in range.", "type": "NORMAL"})
            return {"status": "ok"}
        
        # --- STANDARD ATTACKS (SQLi, DoS, etc) ---
        resp = await netra_client.post(attack_def['endpoint'], attack_def['payload'])
        
        # Interpret Result
        if resp.status_code == 200:
            msg = f"⚠️ VULNERABILITY? Server accepted payload (200 OK)"
            l_type = "WARNING"
        elif resp.status_code >= 400:
                msg = f"🛡️ ATTACK BLOCKED (HTTP {resp.status_code}): {resp.text[:100]}"
                l_type = "SUCCESS" # Using Success color to show the DEFENSE worked
        else:
            msg = f"Result: {resp.status_code}"
            l_type = "NORMAL"

        agent_logs.append({"time": _now(), "msg": msg, "type": l_type})
    except Exception as e:
            add_log({"time": _now(), "msg": f"❌ Connection Error: {e}", "type": "ERROR"})
    
    return {"status": "Attack Sent"}

# --- NETRA SECURE MOVE LISTENER (AGENT B) ---
# This endpoint listens for incoming "moves" or updates from Agent A (Warehouse)
# In the Netra Peer-to-Peer model, the Warehouse might "push" updates here.

@app.post("/api/v1/secure_response")
async def handle_incoming_secure_move(data: dict):
    """
    Receives and processes a secure transaction from Agent A.
    This demonstrates the 'Return Move' logic.
    """
    # 1. Process the incoming secure data
    order_id = data.get("order_id", "Unknown")
    status = data.get("status", "Pending")
    msg = data.get("warehouse_msg", "")
    
    add_log({
        "time": _now(), 
        "msg": f"🛡️ SECURE MOVE RECEIVED: Order {order_id} is {status}. Logic: {msg}", 
        "type": "SUCCESS"
    })
    
    # 2. Optionally Prepare a Secure Acknowledgment (The Counter-Move)
    # This is the LIVE URL of Laptop B's Netra Proxy Ingress (Port 8000)
    LAPTOP_B_PUBLIC_URL = os.environ.get("LAPTOP_B_INGRESS_URL", "https://site-b-ngrok.io")
    
    ack_packet = {
        "order_id": order_id,
        "acknowledgment": "Move verified and state updated in Agent B.",
        "timestamp": _now()
    }

    # 3. Use Netra Egress to send back the Acknowledgment
    try:
        # NOTE: For this specific response, we might need custom headers for X-Target-URL
        # netra_client supports extending headers.
        
        # The URL here is quirky because it calls localhost:9005 directly for egress
        # But netra_client was initialized with a base_url (likely localhost:9005).
        # if TARGET_URL is localhost:9005, we can just use empty path or "/"?
        # Actually proper way:
        
        custom_headers = {
            "X-Target-URL": LAPTOP_B_PUBLIC_URL,
            "X-API-KEY": "agent_a_internal_sk"
        }
        
        # We can use the full URL to be safe, netra_client.post handles absolute URLs
        await netra_client.post(
            "http://localhost:9005", 
            ack_packet,
            headers=custom_headers
        )
    except Exception as e:
        # In a real scenario, we would log this to the console
        pass

    return {"status": "Move Captured. Counter-Move Sent."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9001)

