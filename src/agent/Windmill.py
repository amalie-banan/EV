import random 
from mesa import Agent 
import math
import pandas as pd
from datetime import timedelta
from services.weather_calculator import WeatherEfficiencyCalculator
from services.energy_calculator import EnergyCalculator
class Windmill(Agent):
    def __init__(self,model,scaling_factor,rotordiameter=0,turbine_direction=0,capacity_kw=2.0,pos=None, turbine_type='standard'):
        super().__init__(model)
        self.pos = pos

        # Tid 
        self.time_resolution = self.model.time_resolution
        self.time_step_in_hours =  self.model.time_step_in_hours
        self.current_time = self.model.weather_data.index.get_level_values("timestamp").min()
        
       
        ##scaling specs - how many windmills are "present" in same grid
        self.scaling_factor = scaling_factor

        ##Tekniske specs
        self.turbine_type = turbine_type
        self.rated_power = self._get_rated_power(turbine_type) ##MW
        self.min_operational_wind_speed = 3.0 ## m/s - minimum vind til at starte
        self.max_operational_wind_speed = 25.0 ## m/s - max vind før nedlukning 
        self.optimal_wind_speed = 12.0 # m/s optimal vindhastighed

        self.hub_height = 80  # meter
        self.rotor_diameter = rotordiameter  # meter
        self.capacity_kw = capacity_kw
        self.turbine_direction = turbine_direction
        self.area = math.pi * (self.rotor_diameter / 2) ** 2
        self.cp = 0.4


        ## Tilstand
        self.operational = True
        self.maintenance_needed = False
        self.age = 0
        self.efficiency = 1.0 #Degrades over tid


        ##Output tracking
        self.current_power_output = 0.0 # MW
        self.total_energy_produced = 0.0 #MWh
        self.revenue = 0.0 # DKK
        self.latest_energy_kWh =0.0  
        ## Grid 
        self.grid_connected = True
        self.grid_capacity_limit = self.rated_power


        
        self.energy_calculator = EnergyCalculator(rotordiameter=rotordiameter, capacity_kw=capacity_kw)



        self.freq_offsets = {
            'hourly': lambda t: t + timedelta(hours=1),
            'daily': lambda t: t + timedelta(days=1),
            'weekly': lambda t: t + timedelta(weeks=1),
            'monthly': lambda t: (t + pd.offsets.MonthEnd(1)).to_pydatetime()
        }

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
    
    def calculate_air_density(self, temp_celsius):
        return 1.225 * (273.15 / (temp_celsius + 273.15))

    def adjust_wind_speed_by_direction(self, wind_speed, wind_dir_deg):
        theta = math.radians(wind_dir_deg - self.turbine_direction)
        return wind_speed * max(math.cos(theta), 0)

    def calculate_power(self, wind_speed_mps, temp_celsius):
        rho = self.calculate_air_density(temp_celsius)
        power_watt = 0.5 * rho * self.area * (wind_speed_mps ** 3) * self.cp
        power_kw = power_watt / 1000
        return min(power_kw, self.capacity)
    

    def age_windmill(self):
        """Ældning af vindmølle - reducerer effektivitet"""

        self.age += self.time_step_in_hours / 8760         
        # Effektivitet falder gradvist
        annual_degradation = 0.005  # 0.5% per år
        degradation_per_time_step = annual_degradation * (self.time_step_in_hours / 8760)
        self.efficiency *= (1 - degradation_per_time_step)
        
        # Check for end-of-life
        if self.age > 20:  # 20 års levetid
            self.operational = False
    
    def get_info(self,summary):
        """Debug information"""
        return {
            "time": self.model.current_simulation_time,
       #     "weather": summary['summary'],
            "position": self.pos,
            "type": self.turbine_type,
            "operational": self.operational,
            "current_output": f"{self.current_power_output:.2f} MW",
            "age": f"{self.age:.1f} years",
            "total_energy": f"{self.total_energy_produced:.1f} MWh",
            "revenue": f"{self.revenue:.0f} DKK"
        }    
    def step(self):
        if self.current_time > self.model.weather_data.index.get_level_values("timestamp").max():
            print("✅ All data processed.")
            return

        # Find slut-tid for perioden 
        next_time = self.freq_offsets[self.time_resolution](self.current_time)

        # Udsnit af data for perioden
        df_period = self.model.weather_data.loc[self.current_time:next_time - timedelta(seconds=1)]

        if df_period.empty:
            print(f"⚠️ No data for: {self.current_time} to {next_time}")
            self.current_time = next_time
            return
        
        # Beregn energi for perioden
        energy_df = self.energy_calculator.calculate_energy(df_period, time_resolution=self.time_resolution)
        #self.latest_energy_kWh = energy_this_step
        # Gå videre til næste periode
        self.current_time = next_time
        
    