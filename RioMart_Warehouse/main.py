from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import datetime

# Import Internal Modules
from database_setup import Session as DBSession, Product, CustomerOrder, AccessLog, APIKey
from auth import get_api_key, get_db
from orders import OrderManager
from inventory import InventoryManager

app = FastAPI(title="Warehouse")
templates = Jinja2Templates(directory="templates")

# --- MIDDLEWARE & LOGGING ---
@app.middleware("http")
async def intelligent_logging(request: Request, call_next):
    start_time = datetime.datetime.now()
    
    # Store request body safely
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8") if body_bytes else ""
    async def receive():
        return {"type": "http.request", "body": body_bytes}
    request._receive = receive
    
    response = await call_next(request)
    
    duration = (datetime.datetime.now() - start_time).total_seconds() * 1000
    
    # Log to Database
    db = DBSession()
    try:
        log = AccessLog(
            timestamp=datetime.datetime.utcnow(),
            endpoint=str(request.url.path),
            method=request.method,
            source_ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            status_code=response.status_code,
            response_time_ms=duration,
            payload=body_str[:500] # Truncate large bodies
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Logging Failed: {e}")
    finally:
        db.close()
        
    return response

# --- WEB DASHBOARD ROUTES ---
@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    orders = db.query(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(10).all()
    logs = db.query(AccessLog).order_by(AccessLog.id.desc()).limit(10).all()
    
    # KPIs
    low_stock_count = db.query(Product).filter(Product.stock <= Product.reorder_level).count()
    total_sales = sum(o.total_amount for o in orders) if orders else 0
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "products": products,
        "orders": orders, # Now passing orders
        "logs": logs,
        "low_stock_count": low_stock_count,
        "total_sales": round(total_sales, 2)
    })

@app.post("/dashboard/manual_restock")
def manual_restock_ui(sku: str = Form(...), amount: int = Form(...), db: Session = Depends(get_db)):
    """Handle manual restock from UI form"""
    inv = InventoryManager(db)
    try:
        inv.restock_product(sku, amount, reason="Manual UI Restock")
        return JSONResponse({"status": "success", "message": f"Restocked {sku} by {amount}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

@app.post("/dashboard/manual_order")
def manual_order_ui(sku: str = Form(...), quantity: int = Form(...), db: Session = Depends(get_db)):
    """Handle manual order placement from UI form"""
    mgr = OrderManager(db)
    try:
        item = {"sku": sku, "quantity": quantity}
        order = mgr.create_order(customer_id="MANUAL_UI", items=[item])
        return JSONResponse({"status": "success", "message": f"Order {order.order_uuid} Created"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)

@app.get("/dashboard/orders")
def get_dashboard_orders(db: Session = Depends(get_db)):
    """API for dashboard polling of recent orders"""
    orders = db.query(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(10).all()
    # Serialize manually or use Pydantic. Simple list of dicts for now.
    return [
        {
            "id": o.order_uuid,
            "customer": o.customer_id,
            "total": o.total_amount,
            "status": o.status,
            "time": o.created_at.strftime("%H:%M:%S"),
            "items": o.items_payload
        }
        for o in orders
    ]

# --- API V1 (ENTERPRISE) ---

@app.get("/api/v1/products")
def list_products(
    category: str = None, 
    db: Session = Depends(get_db), 
    api_key: APIKey = Depends(get_api_key)
):
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    return query.all()

@app.get("/api/v1/inventory/low_stock")
def check_low_stock(db: Session = Depends(get_db), api_key: APIKey = Depends(get_api_key)):
    inv = InventoryManager(db)
    return inv.get_low_stock_items()

@app.post("/api/v1/order")
def create_b2b_order(
    order_data: dict, 
    db: Session = Depends(get_db), 
    api_key: APIKey = Depends(get_api_key)
):
    """
    Enterprise Order Endpoint.
    Expects JSON: {"items": [{"sku": "...", "quantity": 1}]}
    """
    mgr = OrderManager(db)
    try:
        items = order_data.get("items", [])
        if not items:
            # Fallback for legacy simple format if needed, or strictly enforce new format
            # Let's support the simple format used in the prompt's example if possible or just fail
            # The prompt example had {"product": "name"}. We are moving to SKU based.
            # We will reject legacy format to enforce "Enterprise Quality".
            raise ValueError("Invalid Format. Expected 'items' list with SKUs.")
            
        order = mgr.create_order(customer_id=api_key.owner, items=items)
        return {
            "status": "Order Confirmed",
            "order_id": order.order_uuid,
            "total_amount": order.total_amount
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/logs/stream")
def stream_logs(db: Session = Depends(get_db)):
    # Public endpoint for the dashboard polling (or secure it if preferred)
    # Keeping it simple for the simulation visualization
    return db.query(AccessLog).order_by(AccessLog.id.desc()).limit(20).all()

if __name__ == "__main__":
    import uvicorn
    # HOST on 9001
    uvicorn.run(app, host="0.0.0.0", port=9001)

