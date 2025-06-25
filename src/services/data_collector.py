import pandas as pd 

class ModelDataCollector:
    def __init__(self, model):
        self.model = model
        self.simulation_data = []
        
    def collect_step_data(self):
        """Gem model output for hvert step"""
        for windmill in self.model.windmills:
            step_data = {
                'timestamp': self.model.current_simulation_time,
                'position': windmill.pos,
                'predicted_power_mw': windmill.current_power_output,
                'wind_speed': windmill.current_wind_speed,
                'weather_efficiency': windmill.weather_efficiency
            }
            self.simulation_data.append(step_data)
    
    def save_to_csv(self):
        df = pd.DataFrame(self.simulation_data)
        df.to_csv(f"model_predictions_{self.model.time_resolution}.csv")