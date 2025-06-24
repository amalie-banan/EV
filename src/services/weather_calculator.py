
class WeatherEfficiencyCalculator:
    """Pure calculation class for weather effects"""
    
    @staticmethod
    def calculate_wind_power_curve(wind_speed, turbine_type="standard"):
        """Calculate power output based on wind speed"""
        # Different turbine types have different curves
        curves = {
            "standard": {"cut_in": 3.0, "rated": 12.0, "cut_out": 25.0},
            "offshore": {"cut_in": 3.5, "rated": 14.0, "cut_out": 30.0},
            "small": {"cut_in": 2.5, "rated": 10.0, "cut_out": 20.0}
        }
        
        curve = curves.get(turbine_type, curves["standard"])
        
        if wind_speed < curve["cut_in"]:
            return 0.0
        elif wind_speed >= curve["cut_out"]:
            return 0.0
        elif wind_speed >= curve["rated"]:
            return 1.0
        else:
            # Cubic relationship below rated wind
            ratio = (wind_speed - curve["cut_in"]) / (curve["rated"] - curve["cut_in"])
            return ratio ** 3
    
    @staticmethod
    def calculate_temperature_efficiency(temperature, optimal_temp=15.0):
        """Calculate efficiency based on temperature"""
        temp_diff = abs(temperature - optimal_temp)
        efficiency_loss = temp_diff * 0.002  # 0.2% per degree
        return max(0.8, 1.0 - efficiency_loss)
    
    @staticmethod
    def calculate_direction_efficiency(wind_direction, optimal_direction=270.0):
        """Calculate efficiency based on wind direction"""
        direction_diff = min(abs(wind_direction - optimal_direction), 
                           360 - abs(wind_direction - optimal_direction))
        efficiency_loss = (direction_diff / 180) * 0.2
        return max(0.8, 1.0 - efficiency_loss)