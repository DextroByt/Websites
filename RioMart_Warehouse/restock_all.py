from database_setup import Session as DBSession, Product, InventoryTransaction
import datetime

def restock_all():
    db = DBSession()
    try:
        products = db.query(Product).all()
        print(f"Checking {len(products)} products...")
        
        for p in products:
            if p.stock < 500: # High threshold to keep agent happy
                add_amount = 1000
                print(f"Restocking {p.name} (SKU: {p.sku}): {p.stock} -> {p.stock + add_amount}")
                p.stock += add_amount
                
                # Log transaction
                trans = InventoryTransaction(
                    product_id=p.id,
                    change_amount=add_amount,
                    reason="System Restock",
                    reference_id="SYS_RESTOCK"
                )
                db.add(trans)
        
        db.commit()
        print("Restock Complete!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restock_all()
