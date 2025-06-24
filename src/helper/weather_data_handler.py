import requests
import json
import numpy as np
from datetime import datetime, timedelta
import random
import pandas as pd


class WeatherDataHandler:
    def __init__(self, startdate,enddate,limit=10):
        
        self.limit = limit
        self.startdate = startdate
        self.enddate = enddate
        self.current_weather = {}
        self.historical_data = {}

        self.dmi_api_key = "87f0ab67-b82c-427a-9fdd-2fecacf8da2f"
        self.dmi_base_url = "https://dmigw.govcloud.dk/v2/metObs/collections/observation/items"
        
        self.bbox_jylland_fyn = '7.963,54.8805,10.9707,57.7781'
        self.bbox_sjaelland = '10.5456,54.9436,13.1935,56.4662'
        self.bbox_bornholm = '14.4879,54.8931,15.3815,55.3517'

        self.temp_parameters = ['temp_mean_past1h']
        self.wind_parameters = ['wind_dir_past1h','wind_speed_past1h']
 
        self.bbox = [self.bbox_jylland_fyn,self.bbox_sjaelland,self.bbox_bornholm
        ]

        self.paramters = self.temp_parameters + self.wind_parameters
        self.get_weather_data(self.paramters)


        self.owm_api_key = None  # Sæt din API key her
        self.owm_base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather_data(self, parameters, csv_filename="weather_data.csv"):
        """Hent vejrdata og gem som CSV"""
        
        all_observations = []
        
        for bbox in self.bbox:
            for parameter in parameters:
                params = {
                    'limit': self.limit,
                    'datetime': self.startdate + "/" + self.enddate,
                    'bbox': bbox,
                    'parameterId': parameter,
                    'api-key': self.dmi_api_key
                }
                
                response = requests.get(self.dmi_base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for obs in data.get('features', []):
                        properties = obs['properties']
                        coordinates = obs['geometry']['coordinates']
                        
                        # Samle alt i én række
                        row = {
                            'longitude': coordinates[0],
                            'latitude': coordinates[1],
                            'parameter_id': parameter,
                            'value': properties.get('value'),
                            'observed': properties.get('observed'),
                            'station_id': properties.get('stationId'),
                            'bbox_area': bbox
                        }
                        
                        all_observations.append(row)
                
                else:
                    print(f"Fejl {response.status_code}: {response.text}")
        
        # Konverter til DataFrame og gem
        if all_observations:
            df = pd.DataFrame(all_observations)
            df['observed'] = pd.to_datetime(df['observed'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Gemt {len(df)} observationer som {csv_filename}")
            
            return df
        
        return pd.DataFrame()
startdate = '2024-06-22' + 'T00:00:00Z'
enddate = '2024-06-23' + 'T00:00:00Z'

handler = WeatherDataHandler(startdate,enddate,limit=10000)