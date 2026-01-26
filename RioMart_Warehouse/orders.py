from sqlalchemy.orm import Session
from database_setup import Product, CustomerOrder, InventoryTransaction
import datetime
import uuid

class OrderManager:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, customer_id: str, items: list[dict]):
        """
        Processes an order transactionally.
        items: [{"sku": "...", "quantity": 1}, ...]
        """
        # Calculate total and validate stock
        total_amount = 0.0
        order_uuid = str(uuid.uuid4())
        
        # We'll store a summary string for the 'product_name' legacy field or new items_payload
        # For this upgraded version, let's use the new json payload
        
        transaction_records = []
        
        for item in items:
            sku = item.get("sku")
            qty = item.get("quantity", 1)
            
            product = self.db.query(Product).filter(Product.sku == sku).first()
            if not product:
                raise ValueError(f"Product SKU {sku} not found")
            
            if product.stock < qty:
                raise ValueError(f"Insufficient stock for {product.name}. Requested: {qty}, Available: {product.stock}")
            
            # Deduct Stock
            product.stock -= qty
            product.last_updated = datetime.datetime.utcnow()
            
            # Create Transaction Record
            trans = InventoryTransaction(
                product_id=product.id,
                change_amount=-qty,
                reason="Customer Order",
                reference_id=order_uuid
            )
            transaction_records.append(trans)
            
            total_amount += (product.price * qty)

        # Create Order Record
        new_order = CustomerOrder(
            order_uuid=order_uuid,
            customer_id=customer_id,
            status="Confirmed", # Auto-confirm if stock is available
            total_amount=round(total_amount, 2),
            items_payload=str(items) # Storing as stringified JSON for simplicity in SQLite
        )
        
        self.db.add(new_order)
        self.db.add_all(transaction_records)
        self.db.commit()
        self.db.refresh(new_order)
        
        return new_order

    def get_recent_orders(self, limit=10):
        return self.db.query(CustomerOrder).order_by(CustomerOrder.created_at.desc()).limit(limit).all()
