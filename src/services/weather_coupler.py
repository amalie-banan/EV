import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
class WeatherWindmillCoupler:
    """Service class for weather-windmill coupling """
    
    def __init__(self, weather_data):
        self.weather_data = weather_data
        self.weather_by_position = self._create_weather_lookup()
        self.available_parameters = [
            'temp_mean_past1h',
            'wind_speed_past1h', 
            'wind_dir_past1h'
        ]

    def _create_weather_lookup(self):
        """Create fast lookup table for weather data per grid position"""
        weather_lookup = {}
        
        for _, row in self.weather_data.iterrows():
            pos = row['Grid_Position']
            if pos is None:
                continue
                
            if pos not in weather_lookup:
                weather_lookup[pos] = []
            
            weather_lookup[pos].append({
                'observed': row['observed'],
                'parameter_id': row['parameter_id'],
                'value': row['value'],
                'station_id': row['station_id']
            })
        
        # Sort by time for each position
        for pos in weather_lookup:
            weather_lookup[pos].sort(key=lambda x: x['observed'])
        
        return weather_lookup
    def get_weather_summary(self, grid_position, current_time):
        """
        Get a nice summary of weather conditions
        
        Returns:
        --------
        dict : Formatted weather summary
        """
        weather = self.get_all_weather_for_position(grid_position, current_time)
        
        # Add some derived metrics
        wind_speed = weather.get('wind_speed_past1h', 0)
        wind_dir = weather.get('wind_dir_past1h', 0)
        temp = weather.get('temp_mean_past1h', 15)
        
        # Wind direction text
        wind_directions = {
            0: "Nord", 45: "Nordøst", 90: "Øst", 135: "Sydøst",
            180: "Syd", 225: "Sydvest", 270: "Vest", 315: "Nordvest"
        }
        
        closest_dir = min(wind_directions.keys(), key=lambda x: abs(x - (wind_dir or 0)))
        wind_dir_text = wind_directions[closest_dir]
        
        # Wind strength categories
        if wind_speed < 3:
            wind_strength = "Svag"
        elif wind_speed < 8:
            wind_strength = "Moderat"  
        elif wind_speed < 15:
            wind_strength = "Kraftig"
        else:
            wind_strength = "Stormfuld"
        
        return {
            **weather,  # Include all raw data
            'wind_direction_text': wind_dir_text,
            'wind_strength': wind_strength,
            'temperature_celsius': temp,
            'summary': f"{wind_strength} {wind_dir_text.lower()}envind ({wind_speed:.1f} m/s), {temp:.1f}°C"
        }
    
    def get_avg_wind(self,position,current_time,time_resolution,time_step_in_hours):
        print("hej")
        print(position,current_time,time_resolution,time_step_in_hours)
        weather_samples = []
        # Sample weather data over the period
        for hour_offset in range(0, time_step_in_hours):  
            sample_time = current_time - timedelta(hours=hour_offset)
         #   print(sample_time)
            weather = self.get_all_weather_for_position(position, sample_time)
            
            if weather and all(weather.get(param) is not None for param in ['wind_speed_past1h', 'temp_mean_past1h', 'wind_dir_past1h']):
                weather_samples.append(weather)
          #  print(weather_samples)
        if not weather_samples:
        # Fallback to current time if no samples found
            return self.get_all_weather_for_position(position, current_time)
        # Beregn gennemsnit
        avg_temp = sum(sample['temp_mean_past1h'] for sample in weather_samples) / len(weather_samples)
        avg_wind_speed = sum(sample['wind_speed_past1h'] for sample in weather_samples) / len(weather_samples)
        
        # For vindretning skal vi være forsigtige med cirkulære værdier (0° = 360°)
        # Konverter til vektorer, beregn gennemsnit, konverter tilbage
      
        sin_sum = sum(math.sin(math.radians(sample['wind_dir_past1h'])) for sample in weather_samples)
        cos_sum = sum(math.cos(math.radians(sample['wind_dir_past1h'])) for sample in weather_samples)
        avg_wind_dir = math.degrees(math.atan2(sin_sum, cos_sum))
        if avg_wind_dir < 0:
            avg_wind_dir += 360  # Sørg for at værdi er mellem 0-360
        
        # Returner i ønsket format
        return {
            'position': position,
            'time': current_time,
            'temp_mean_past1h': round(avg_temp, 1),
            'wind_speed_past1h': round(avg_wind_speed, 1),
            'wind_dir_past1h': round(avg_wind_dir, 1)
        }
         



    def get_all_weather_for_position(self, grid_position, current_time, parameters=None):
        """
        Get ALL weather parameters for a specific grid position and time
        
        Parameters:
        -----------
        grid_position : tuple
            Grid position (x, y)
        current_time : datetime
            Target time
        parameters : list, optional
            List of parameters to get. If None, gets all available parameters
            
        Returns:
        --------
        dict : Weather data for all requested parameters
            {
                'temp_mean_past1h': 15.2,
                'wind_speed_past1h': 8.5,
                'wind_dir_past1h': 270.0,
                'position': (x, y),
                'time': current_time
            }
        """
        
        # Use all available parameters if none specified
        if parameters is None:
            parameters = self.available_parameters
        
        # If position not found, try nearest
        if grid_position not in self.weather_by_position:
            return self._get_nearest_all_weather(grid_position, current_time, parameters)
        
        weather_records = self.weather_by_position[grid_position]
        target_time = pd.to_datetime(current_time)
        
        # Remove timezone if present
        if hasattr(target_time, 'tz') and target_time.tz is not None:
            target_time = target_time.tz_localize(None)
        
        # Get data for each parameter
        weather_data = {
            'position': grid_position,
            'time': current_time
        }
        
        for param in parameters:
            # Filter records for this parameter
            relevant_records = [r for r in weather_records if r['parameter_id'] == param]
            
            if relevant_records:
                # Find closest time for this parameter
                closest_record = min(relevant_records, 
                                   key=lambda x: abs((pd.to_datetime(x['observed']) - target_time).total_seconds()))
                weather_data[param] = closest_record['value']
            else:
                weather_data[param] = None
        
        return weather_data
     
    def _get_nearest_all_weather(self, target_position, current_time, parameters):
        """Find ALL weather parameters from nearest grid position"""
        if not self.weather_by_position:
            return {param: None for param in parameters}
        
        target_x, target_y = target_position
        min_distance = float('inf')
        nearest_position = None
        
        # Find nearest position with weather data
        for pos in self.weather_by_position.keys():
            pos_x, pos_y = pos
            distance = ((target_x - pos_x) ** 2 + (target_y - pos_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_position = pos
        
        if nearest_position:
            return self.get_all_weather_for_position(nearest_position, current_time, parameters)
        else:
            return {param: None for param in parameters}