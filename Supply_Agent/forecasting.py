import random
import math

class DemandSimulator:
    """
    Simulates the consumption of materials in a manufacturing plant.
    """
    def __init__(self, managed_skus):
        self.skus = managed_skus
        # Internal Virtual Inventory (What the agent *has* in its local warehouse)
        self.local_inventory = {sku: random.randint(50, 200) for sku in self.skus}
        # Daily usage rate (mean, std_dev)
        self.usage_profile = {sku: (random.randint(5, 20), random.randint(1, 5)) for sku in self.skus}
        
    def consume(self):
        """Reduces stock based on simulated usage. Returns list of consumed items."""
        consumed_log = []
        for sku in self.skus:
            # Normal distribution of usage, ensuring non-negative
            usage = max(0, int(random.gauss(*self.usage_profile[sku])))
            
            if usage > 0:
                current_stock = self.local_inventory[sku]
                actual_consumption = min(current_stock, usage)
                self.local_inventory[sku] -= actual_consumption
                
                consumed_log.append({
                    "sku": sku, 
                    "used": actual_consumption, 
                    "remaining": self.local_inventory[sku]
                })
        return consumed_log

    def get_stock_level(self, sku):
        return self.local_inventory.get(sku, 0)
