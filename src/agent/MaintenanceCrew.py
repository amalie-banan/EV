import random 
from mesa import Agent 

class MaintenanceCrew(Agent):
    def step(self):
        # Bevæger sig rundt og reparerer møller
        broken_turbine = self.find_nearest_broken_turbine()
        self.move_towards(broken_turbine)