import math

class LogisticsEngine:
    """
    Decides WHEN and HOW MUCH to order.
    """
    def __init__(self, simulator):
        self.simulator = simulator
        # Configuration
        self.min_stock_level = 30 # Safety Stock
        self.max_stock_level = 200
        self.eoq_cost_per_order = 50 # Ordering Cost
        self.holding_cost = 2 # Holding cost per unit per year
        
    def evaluate_needs(self):
        """
        Checks local inventory. Returns list of orders to place.
        """
        orders_needed = []
        
        for sku, current_stock in self.simulator.local_inventory.items():
            if current_stock <= self.min_stock_level:
                # We need to reorder
                # Simple Min-Max replenishment for now, or EOQ if we had annual demand data
                # Let's use a "Smart Replenish" target
                
                qty_to_order = self.max_stock_level - current_stock
                
                # Check bounds
                if qty_to_order > 0:
                    orders_needed.append({"sku": sku, "quantity": qty_to_order, "priority": "High"})
        
        return orders_needed
    
    def update_stock_after_delivery(self, sku, qty):
        if sku in self.simulator.local_inventory:
            self.simulator.local_inventory[sku] += qty
