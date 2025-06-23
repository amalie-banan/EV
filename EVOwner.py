import random 
from mesa import Agent 


class EVOwner(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.battery_capacity = random.choice([40, 60, 75, 100])  # kWh
        self.current_charge = random.uniform(0.2, 0.8) * self.battery_capacity
        self.daily_driving_km = random.normalvariate(40, 15)
        self.charging_preference = random.choice(['home', 'work', 'public'])
        self.departure_time = random.normalvariate(8, 1)  # Afgang hjemmefra
        self.arrival_time = random.normalvariate(17, 1)   # Hjemkomst
        self.is_charging = False
        self.current_location_type = 'home'  # 'home', 'work', 'transit'

    def step(self):
        """Hvad agenten gør i hvert step"""
        # Opdater batteriniveau baseret på kørsel
        self.update_battery_level()
        
        # Beslut om at bevæge sig
        self.move()
        
        # Tjek om der skal lades
        self.consider_charging()
    
    def update_battery_level(self):
        """Opdaterer batteriniveau baseret på kørsel"""
        # Simpel model: tab 0.1-0.3 kWh per step
        energy_consumption = random.uniform(0.1, 0.3)
        self.current_charge = max(0, self.current_charge - energy_consumption)
    
    def move(self):
        """Bevæg agenten"""
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        possible_steps = list(set(set(possible_steps).intersection(set(self.model.valid_coords))))
        
        
        if possible_steps:
            new_position = self.random.choice(possible_steps)
            self.model.grid.move_agent(self, new_position)
            
    
    def consider_charging(self):
        """Beslut om der skal lades"""
        charge_level = self.current_charge / self.battery_capacity
        
        # Lad hvis batteriet er under 30%
        if charge_level < 0.3:
            self.is_charging = True
            # Find nærmeste ladestation (implementeres senere)
        elif charge_level > 0.8:
            self.is_charging = False
    
    def get_battery_percentage(self):
        """Returnerer batteriniveau i procent"""
        return (self.current_charge / self.battery_capacity) * 100
