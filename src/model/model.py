from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
import random
import math
from pathlib import Path
import os
import pandas as pd
import traceback

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
       
        self.create_weather_data=create_weather_data
        self.weather_data_startdate=weather_data_startdate
        self.weather_data_enddate=weather_data_enddate
        self.create_windmill_data=create_windmill_data

        self.windmills_created = False 
        self.num_working_windmills = working_windmills
        self.num_broken_windmills = broken_windmills
        self.grid = MultiGrid(width, height, True)
        self.current_step = 0
        self.time_resolution = time_resolution
        self.time_step_hours = {"hourly": 1,"daily": 24, "weekly": 168,"monthly": 720}[time_resolution]

        
        windmill_data = self.get_windmill_data()
        self.valid_coords = list(windmill_data['Grid_Position'])

        Grid_Position_counts = windmill_data['Grid_Position'].value_counts()
        self.grid_position_dict = Grid_Position_counts.to_dict()


        #### CREATE AGENTS ####
        self.create_windmills('standard')
       
    def create_windmills(self,turbine_type):
        print("#"*50)
        print("Creating Windmills to map")
        print("#"*50)
        
        positions = list(set([x for x in self.valid_coords if x is not None]))
        random.shuffle(positions)
        agents_to_place =  min(self.num_working_windmills,len(positions))
        if len(positions) >= 0:
            n_windmills = self.num_working_windmills
            for i in range(0,n_windmills):
                if agents_to_place>0 :
                    pos = positions.pop()
                    scaling_factor = self.grid_position_dict.get(pos)
                    if self.grid.is_cell_empty(pos):
                        windmill = Windmill(self, scaling_factor=scaling_factor,turbine_type=turbine_type)
                        self.grid.place_agent(windmill, pos)
                        agents_to_place-=1
                        print(f"Placed Windmill #{i+1} at: ", pos, " with scaling factor ", scaling_factor)

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
            handler = ParquetWeatherHandler()
            weather_data = handler.load_data()
        else:
            print("📂 Download data")
            handler = ParquetWeatherHandler(self.weather_data_startdate,self.weather_data_enddate)
            handler.download_all_data(chunk_days=7)
            weather_data = handler.load_data()     
        
        weather_data['Grid_Position'] = weather_data.apply(
                lambda row: map_coordinates_to_grid(row['latitude'], row['longitude'], self.grid.width, self.grid.height),
                axis=1)
        weather_data.to_csv("weather_data.csv")
        return weather_data  

    def get_windmill_data(self):
        if not self.create_windmill_data and os.path.isfile("vindmoeller_complete.csv"):
            windmill_data = pd.read_csv("vindmoeller_complete.csv")
        else:
            #self.create_windmill_data or not os.path.isfile("vindmoeller_complete.csv"):
            WindmillDataHandler()
            windmill_data = pd.read_csv("vindmoeller_complete.csv")
        
        windmill_data = windmill_data[['GSRN','Tilsluttet','Kapacitet','Rotordiame','Navhøjde',
                                       'Fabrikat','Model','Kommune', 'Postnummer', 'Ejerlav',
                                       'Latitude', 'Longitude']]
     
        
        windmill_data['Grid_Position'] = windmill_data.apply(
                lambda row: map_coordinates_to_grid(row['Latitude'], row['Longitude'], self.grid.width, self.grid.height),
                axis=1
            )
        return windmill_data
    def step(self):
        """En simulation step"""
        self.current_step += 1
        
        # Alle agenter tager et step
        for agent in self.agents:
            agent.step()
   