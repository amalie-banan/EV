from mesa import Model
from mesa.space import MultiGrid
import numpy as np
import time
import random
import math
from pathlib import Path
import os
import pandas as pd
import traceback
from datetime import datetime, timedelta
from cleaning.missing_data import MissingWeatherDataAnalyzer
from mesa.datacollection import DataCollector
# I model/model.py
from services.weather_coupler import WeatherWindmillCoupler
from services.weather_calculator import WeatherEfficiencyCalculator
#from mesa import RandomActivation  


# Korrekte imports til dine agent klasser
from agent.GridNode import GridNode  

from agent.Windmill import Windmill
from agent.DenmarkOutline import DenmarkOutline
from helper.helper_functions import create_elliptical_octagon_outline_precise,get_cells_inside_outline_scanline,map_coordinates_to_grid
from helper.windmill_data_handler import WindmillDataHandler
from helper.parquet_weather_data_handler import ParquetWeatherHandler

class WindEnergyModel(Model):
    """Model af vindmøller i Danmark"""
    def __init__(self, working_windmills=200, broken_windmills=0, 
                 time_resolution='daily',
                 weather_data_startdate='2024-01-01T00:00:00Z',
                 weather_data_enddate='2024-01-08T00:00:00Z',
                 create_windmill_data=False, create_weather_data=False, width=60, height=60 ):
        super().__init__() 
       
        #self.schedule = RandomActivation(self)
    
        self.create_weather_data=create_weather_data
        self.weather_data_startdate=weather_data_startdate
        self.weather_data_enddate=weather_data_enddate
        self.create_windmill_data=create_windmill_data

        self.current_simulation_time = datetime.strptime(weather_data_startdate, "%Y-%m-%dT%H:%M:%SZ") #datetime(2024, 1, 1, 12, 0, 0)
        print(self.current_simulation_time)
        self.time_resolution = time_resolution
        self.time_step_in_hours = {'hourly': 1, 'daily': 24, 'weekly': 168, 'monthly': 720}[time_resolution]
        


        self.num_working_windmills = working_windmills
        self.num_broken_windmills = broken_windmills
        self.grid = MultiGrid(width, height, True)
        self.current_step = 0
       

        self.weather_data = self.get_weather_data()
       # self.weather_coupler = WeatherWindmillCoupler(weather_data=self.weather_data) 
        
        self.windmill_data = self.get_windmill_data()


        
        
        #### CREATE AGENTS ####
        self.create_windmills('standard')
        
        self.produced_in_jan2023 = self.windmill_data.set_index('Grid_Position')['Y2023-1_mean'].to_dict()


        ### CREATE DATACOLLECTORS ###

    
        
        self.energy_datacollector = DataCollector(
        model_reporters={
            "TotalEnergyProduced": lambda m: sum(agent.total_energy_produced for agent in m.agents if isinstance(agent, Windmill))

        }
    )
       
    def create_windmills(self,turbine_type):
        print("#"*50)
        print("Creating Windmills to map")
        print("#"*50)
        valid_coords = list(self.windmill_data['Grid_Position'])
        Grid_Position_counts = self.windmill_data['Grid_Position'].value_counts()
        grid_position_dict = Grid_Position_counts.to_dict()
        rotodiam_mean_dict = self.windmill_data.set_index('Grid_Position')['Rotodiam_mean'].to_dict()
        capacity_mean_dict = self.windmill_data.set_index('Grid_Position')['Kapacitet_mean'].to_dict()
        


        positions = list(set([x for x in valid_coords if x is not None]))
        random.shuffle(positions)
        agents_to_place =  min(self.num_working_windmills,len(positions))
        if len(positions) >= 0:
            n_windmills = self.num_working_windmills
            for i in range(0,n_windmills):
                if agents_to_place>0 :
                    pos = positions.pop()
                    
                    scaling_factor = grid_position_dict.get(pos)
                    if self.grid.is_cell_empty(pos):
                        rotordiam_mean = rotodiam_mean_dict.get(pos)
                        capacity_mean = capacity_mean_dict.get(pos)
                        windmill = Windmill(self, rotordiameter=rotordiam_mean,capacity_kw=capacity_mean,scaling_factor=scaling_factor,turbine_type=turbine_type)
                        self.grid.place_agent(windmill, pos)
                        agents_to_place-=1 
                #        print(f"Placed Windmill #{i+1} at: ", pos, " with scaling factor ", scaling_factor)

                    else:
                        print(f"Position {pos} is already occupied.")
                else:
                    print("No more agents to place in world")
                    break

    def create_denmark_outline(self):
        """Opretter Danmarks omrids som tynde grønne rektangler på 70x70 grid"""
        
        outline_coordinates = []
    
               
        jylland_main = create_elliptical_octagon_outline_precise(15, 25, 15, 40)
        jylland_inside = get_cells_inside_outline_scanline(jylland_main, self.grid.width, self.grid.height)
        jylland_nose = create_elliptical_octagon_outline_precise(30, 35, 7, 5, rotation_degrees=5)
        jylland_nose_inside = get_cells_inside_outline_scanline(jylland_nose, self.grid.width, self.grid.height)
        jylland_nose = [coord for coord in jylland_nose if coord not in jylland_inside and coord not in jylland_main and coord not in jylland_nose_inside] 
        jylland_main = [coord for coord in jylland_main if coord not in jylland_nose_inside]
        jylland_coords = jylland_main+ jylland_nose
        #print(jylland_nose_inside)

        sjaelland_coords = create_elliptical_octagon_outline_precise(58, 17, 12, 16)
        fyn_coords = create_elliptical_octagon_outline_precise(37, 12, 7, 6,rotation_degrees=-20)
        outline_coordinates.extend(jylland_coords)
        outline_coordinates.extend(sjaelland_coords)
        outline_coordinates.extend(fyn_coords)
        
        
        # Opret outline-agenter
        for x, y in outline_coordinates:
            if 0 <= x < self.grid.width and 0 <= y < self.grid.height:
                if self.grid.is_cell_empty((x, y)):
                    outline_agent = DenmarkOutline(self)
                    self.grid.place_agent(outline_agent, (x, y))   
                    print(f"Placed DenmarkOutline at: ({x},{y})")

        return outline_coordinates
 
    def create_valid_coords(self,outline_coords):
        # Find alle celler INDE I Danmark
        denmark_inside_cells = get_cells_inside_outline_scanline(outline_coords, self.grid.width, self.grid.height)
        print(len(denmark_inside_cells))
        print(f"Found {len(denmark_inside_cells)} cells inside Denmark")
        
        if len(denmark_inside_cells) == 0:
            print("No cells found inside Denmark outline!")
            return
            
        # Find tomme celler indenfor Danmark
        cells_in_denmark = []
        for x, y in denmark_inside_cells:
            if self.grid.is_cell_empty((x, y)):
                cells_in_denmark.append((x, y))
        
        print(f"Found {len(cells_in_denmark)} empty cells inside Denmark")
        
        # Resten af din kode som før...
        return cells_in_denmark
    def get_weather_data(self):
        if not self.create_weather_data and Path("weather_parquet_data").exists():
            print("📂 Loading existing data (should NOT download)")
            handler = ParquetWeatherHandler(self.weather_data_startdate,self.weather_data_enddate)
            print(self.weather_data_startdate,self.weather_data_enddate)
            weather_data = handler.load_data()
        else:
            print("📂 Download data")
            handler = ParquetWeatherHandler(self.weather_data_startdate,self.weather_data_enddate)
            
            handler.download_all_data(chunk_days=7)
            weather_data = handler.load_data()     
        
        weather_data['Grid_Position'] = weather_data.apply(
                lambda row: map_coordinates_to_grid(row['latitude'], row['longitude'], self.grid.width, self.grid.height),
                axis=1)
        
        
        # Konverter 'observed' til datetime
        weather_data['observed'] = pd.to_datetime(weather_data['observed'])
        
        
        # Pivotér til én række per station_id + tidspunkt og fjern index igen bagefter
        df_wide = weather_data.pivot_table(
            index=['observed', 'station_id', 'latitude', 'longitude', 'region', 'Grid_Position'],
            columns='parameter_id',
            values='value'
        ).reset_index()

        # Omdøb kolonner hvis ønsket
        df_wide = df_wide.rename(columns={
            'observed': 'timestamp',
            'wind_speed_past1h': 'wind_speed',
            'wind_dir_past1h': 'wind_dir',
            'temp_mean_past1h': 'temp',
            'humidity_past1h': 'humidity'
        })
        
        analyzer = MissingWeatherDataAnalyzer(df_wide)
        df_wide = analyzer._method_interpolate_then_median()
        df_wide.set_index(['timestamp', 'station_id'], inplace=True)
        df_wide.sort_index(inplace=True)   
        df_wide.to_csv("weather_data.csv")
        return df_wide  

    def get_windmill_data(self):
        if not self.create_windmill_data and os.path.isfile("vindmoeller_complete.csv"):
            windmill_data = pd.read_csv("vindmoeller_complete.csv")
        else:
            #self.create_windmill_data or not os.path.isfile("vindmoeller_complete.csv"):
            WindmillDataHandler()
            windmill_data = pd.read_csv("vindmoeller_complete.csv")
        
        windmill_data = windmill_data[['GSRN','Tilsluttet','Kapacitet','Rotordiame','Navhøjde',
                                       'Fabrikat','Model','Kommune', 'Postnummer', 'Ejerlav',
                                       'Latitude', 'Longitude','Y2023-1']]
     
        
        windmill_data['Grid_Position'] = windmill_data.apply(
                lambda row: map_coordinates_to_grid(row['Latitude'], row['Longitude'], self.grid.width, self.grid.height),
                axis=1
            )
        # Beregn gennemsnittet af 'rotordiam' for hver 'Grid_Position' - relevant hvis der er flere vindmøller på ét (x,y)
        mean_rotordiam = windmill_data.groupby('Grid_Position')['Rotordiame'].mean().reset_index()
        mean_rotordiam.rename(columns={'Rotordiame': 'Rotodiam_mean'}, inplace=True)
        windmill_data = windmill_data.merge(mean_rotordiam, on='Grid_Position', how='left')

        #Beregn gennemsnittet af kapacitet tfor hver Grid_Position - relevant hvis der er flere vindmøller på ét (x,y)
        mean_capacity = windmill_data.groupby('Grid_Position')['Kapacitet'].mean().reset_index()
        mean_capacity.rename(columns={'Kapacitet': 'Kapacitet_mean'}, inplace=True)
        windmill_data = windmill_data.merge(mean_capacity, on='Grid_Position', how='left')

 

        mean_jan2023 = windmill_data.groupby('Grid_Position')['Y2023-1'].mean().reset_index()
        mean_jan2023.rename(columns={'Y2023-1': 'Y2023-1_mean'}, inplace=True)

        # Merge tilbage til originalt datasæt
        windmill_data = windmill_data.merge(mean_jan2023, on='Grid_Position', how='left')

        return windmill_data
    def step(self):
        """En simulation step"""
        
        start = time.perf_counter()
 
     
        self.agents.do("step")
        self.energy_datacollector.collect(self)
        print(self.energy_datacollector.get_model_vars_dataframe().tail(1))
      #  print(self.energy_datacollector.get_model_vars_dataframe())

       
        self.current_step += 1
        self.current_simulation_time += timedelta(hours=self.time_step_in_hours)
            
        # Alle agenter tager et step
        for agent in self.agents:
            agent.step()
        end = time.perf_counter()
        print(f"⏱️ step() tog {end - start:.3f} sekunder")

