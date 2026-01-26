import requests
import json

RIO_URL = "http://localhost:9001"
API_KEY = "rio_sk_live_7384928492"

def run_diagnostics():
    print("🔍 Starting Diagnostics...")
    
    # 1. Fetch Catalog
    print(f"\n1. Fetching Catalog from {RIO_URL}...")
    try:
        resp = requests.get(f"{RIO_URL}/api/v1/products", headers={"X-API-KEY": API_KEY})
        if resp.status_code == 200:
            products = resp.json()
            print(f"   ✅ Success. Found {len(products)} products.")
            if not products:
                print("   ⚠️ Catalog is empty! Agent cannot operate.")
                return
        else:
            print(f"   ❌ Failed to fetch catalog. Status: {resp.status_code}, Body: {resp.text}")
            return
    except Exception as e:
        print(f"   ❌ Connection Error: {e}")
        return

    # 2. Pick a Product to Test
    target_product = products[0]
    sku = target_product['sku']
    print(f"\n2. Testing Order for SKU: {sku} (Current Stock: {target_product['stock']}, Price: {target_product['price']})")

    # 3. Place a Valid Order
    payload = {
        "items": [
            {"sku": sku, "quantity": 1}
        ]
    }
    print(f"   Sending Payload: {json.dumps(payload)}")
    
    try:
        resp = requests.post(f"{RIO_URL}/api/v1/order", json=payload, headers={"X-API-KEY": API_KEY})
        if resp.status_code == 200:
            print(f"   ✅ Order Accepted: {resp.json()}")
        else:
            print(f"   ❌ Order Rejected (HTTP {resp.status_code})")
            print(f"   ⚠️ Reason: {resp.text}")
            
    except Exception as e:
        print(f"   ❌ Request Failed: {e}")

    # 4. Test Error Case (Invalid SKU)
    print("\n3. Testing Error Handling (Invalid SKU)...")
    try:
        resp = requests.post(f"{RIO_URL}/api/v1/order", json={"items": [{"sku": "INVALID-999", "quantity": 1}]}, headers={"X-API-KEY": API_KEY})
        print(f"   Response: {resp.status_code} - {resp.text}")
    except:
        pass

if __name__ == "__main__":
    run_diagnostics()
