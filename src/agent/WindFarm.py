import random 
from mesa import Agent 

class WindFarm(Agent):
    def step(self):
        if self.profitability < threshold:
            self.decommission()  # "Bevæger sig væk" fra kortet
        
        # Nye møller "spawner" på bedste lokationer
        if market_conditions_good:
            new_location = find_optimal_spot()
            self.model.add_turbine(new_location)