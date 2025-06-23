from mesa import Agent
import random

class GridNode(Agent):
    def __init__(self, model, region):
        super().__init__(model)
        self.region = region  # DK1, DK2
        self.current_load = 0
        self.max_capacity = random.randint(1000, 5000)  # MW
        self.renewable_percentage = 0  # Fra Energinet API
        self.price_per_kwh = 0  # Spotpris