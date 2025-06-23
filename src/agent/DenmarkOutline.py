import random 
from mesa import Agent 

class DenmarkOutline(Agent):
    """Agent der repræsenterer Danmarks grænser"""
    
    def __init__(self, model):
        super().__init__(model)
        self.is_border = True
    
    def step(self):
        # Gør nada - statisk element
        pass