import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class WeatherWindmillCoupler:
    """Service class for weather-windmill coupling """
    
    def __init__(self, weather_data):
        self.weather_data = weather_data
        self.weather_by_position = self._create_weather_lookup()
        
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
    
    def get_weather_for_position(self, grid_position, current_time, parameter='wind_speed_past1h'):
        """Get weather data for specific grid position and time"""
        
        if grid_position not in self.weather_by_position:
            return self._get_nearest_weather(grid_position, current_time, parameter)
        
        weather_records = self.weather_by_position[grid_position]
        target_time = pd.to_datetime(current_time)
        
        # Filter for the right parameter
        relevant_records = [r for r in weather_records if r['parameter_id'] == parameter]
        
        if not relevant_records:
            return None
        
        # Find closest time
        closest_record = min(relevant_records, 
                           key=lambda x: abs((pd.to_datetime(x['observed']) - target_time).total_seconds()))
        
        return closest_record['value']
    
    def _get_nearest_weather(self, target_position, current_time, parameter):
        """Find weather data from nearest grid position"""
        if not self.weather_by_position:
            return None
        
        target_x, target_y = target_position
        min_distance = float('inf')
        nearest_weather = None
        
        for pos in self.weather_by_position.keys():
            pos_x, pos_y = pos
            distance = ((target_x - pos_x) ** 2 + (target_y - pos_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                weather_value = self.get_weather_for_position(pos, current_time, parameter)
                if weather_value is not None:
                    nearest_weather = weather_value
        
        return nearest_weather
