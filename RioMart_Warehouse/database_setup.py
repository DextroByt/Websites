from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from faker import Faker
import random
import datetime
import uuid

Base = declarative_base()
engine = create_engine('sqlite:///./rio_mart.db', connect_args={"check_same_thread": False})

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    category = Column(String)  # New: e.g., 'Electronics', 'Raw Materials'
    stock = Column(Integer)
    reorder_level = Column(Integer, default=20) # New: Threshold for low stock warning
    price = Column(Float)
    
    # Audit trail
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class APIKey(Base):
    """Stores authorized clients (Agents/Partners)"""
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, index=True) # The actual header value
    owner = Column(String) # e.g. "Supply_Agent_Mumbai_01"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    permissions = Column(String) # comma-separated scopes: "read,write"

class InventoryTransaction(Base):
    """Immutable ledger of all stock movements"""
    __tablename__ = 'inventory_transactions'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    product_id = Column(Integer, ForeignKey('products.id'))
    change_amount = Column(Integer) # +100 or -5
    reason = Column(String) # 'Purchase Order', 'Sale', 'Adjustment'
    reference_id = Column(String) # Order ID or PO Number

class CustomerOrder(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String) # Link to API Key owner
    status = Column(String, default="Pending") # 'Pending', 'Processing', 'Shipped', 'Cancelled'
    total_amount = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # JSON blob for line items to keep it simple but flexible
    items_payload = Column(Text) 

class AccessLog(Base):
    __tablename__ = 'access_logs'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    method = Column(String)
    endpoint = Column(String)
    source_ip = Column(String)
    user_agent = Column(String)
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    payload = Column(Text) # Request Body (Truncated if too large)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
fake = Faker()

def seed_data():
    # 1. Seed Products if empty
    if session.query(Product).count() == 0:
        print("Creating Enterprise Product Catalog...")
        categories = ['Electronics', 'Industrial', 'Office Supplies', 'Logistics']
        for _ in range(50):
            p = Product(
                name=f"{fake.word().title()} {fake.word().title()}",
                sku=fake.ean13(),
                category=random.choice(categories),
                stock=random.randint(1000, 5000),
                reorder_level=30,
                price=round(random.uniform(10.0, 2000.0), 2)
            )
            session.add(p)
        
        # 2. Seed Default API Key for the Agent
        # reliable-key-123 is what we will configure the Agent to use
        print("Creating Default API Keys...")
        k = APIKey(
            key="rio_sk_live_7384928492", 
            owner="Supply_Agent_Alpha", 
            permissions="read,write:order"
        )
        session.add(k)
        
        session.commit()
        print("✅ RioMart Database Seeded Successfully.")
    else:
        print("ℹ️  Database already initialized.")

if __name__ == "__main__":
    seed_data()
