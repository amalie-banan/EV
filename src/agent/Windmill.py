import random 
from mesa import Agent 

class Windmill(Agent):
    def __init__(self,model,pos=None, turbine_type='standard'):
        super().__init__(model)
        self.pos = pos

        ##Tekniske specs
        self.turbine_type = turbine_type
        self.rated_power = self._get_rated_power(turbine_type) ##MW
        self.min_operational_wind_speed = 3.0 ## m/s - minimum vind til at starte
        self.max_operational_wind_speed = 25.0 ## m/s - max vind før nedlukning 
        self.optimal_wind_speed = 12.0 # m/s optimal vindhastighed

        self.hub_height = 80  # meter
        self.rotor_diameter = 100  # meter


        ## Tilstand
        self.operational = True
        self.maintenance_needed = False
        self.age = 0
        self.effeciency = 1.0 #Degrades over tid

        ##Output tracking
        self.current_power_output = 0.0 # MW
        self.total_energy_produced = 0.0 #MWh
        self.revenue = 0.0 # DKK

        ## Grid 
        self.grid_connected = True
        self.grid_capacity_limit = self.rated_power

    def _get_rated_power(self,turbine_type):
     ##Forskellige mølle-typer med forskellige kapaciteter###
        turbine_specs = {
            "small": 0.8,      # MW
            "standard": 2.3,   # MW - typisk onshore
            "large": 3.6,      # MW
            "offshore": 8.0    # MW - moderne offshore
        }
        if turbine_type in turbine_specs:
            return turbine_specs[turbine_type]
        else:
            raise ValueError(f"Unknown turbine type: {turbine_type}")
    
    def age_windmill(self):
        """Ældning af vindmølle - reducerer effektivitet"""
        self.age += 1/365  # daglig ældning
        
        # Effektivitet falder gradvist
        annual_degradation = 0.005  # 0.5% per år
        self.efficiency *= (1 - annual_degradation/365)
        
        # Check for end-of-life
        if self.age > 20:  # 20 års levetid
            self.operational = False
    
    def get_info(self):
        """Debug information"""
        return {
            "type": self.turbine_type,
            "position": self.pos,
            "operational": self.operational,
            "current_output": f"{self.current_power_output:.2f} MW",
            "age": f"{self.age:.1f} years",
            "total_energy": f"{self.total_energy_produced:.1f} MWh",
            "revenue": f"{self.revenue:.0f} DKK"
        }    
    def step(self):
        print(self.get_info())
 