from sqlalchemy.orm import Session
from database_setup import Product, InventoryTransaction
import datetime

class InventoryManager:
    def __init__(self, db: Session):
        self.db = db

    def get_low_stock_items(self):
        """Returns items where stock is below their specific reorder level"""
        return self.db.query(Product).filter(Product.stock <= Product.reorder_level).all()

    def restock_product(self, sku: str, amount: int, reason: str = "Manual Restock"):
        product = self.db.query(Product).filter(Product.sku == sku).first()
        if not product:
            raise ValueError("Product not found")
        
        product.stock += amount
        product.last_updated = datetime.datetime.utcnow()
        
        trans = InventoryTransaction(
            product_id=product.id,
            change_amount=amount,
            reason=reason,
            reference_id=f"RESTOCK-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        )
        
        self.db.add(trans)
        self.db.commit()
        return product
