from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
import random
import math

# Korrekte imports til dine agent klasser
from agent.GridNode import GridNode  

from agent.Windmill import Windmill
from agent.DenmarkOutline import DenmarkOutline
from helper.helper_functions import create_elliptical_octagon_outline_precise,get_cells_inside_outline_scanline

class EVModel(Model):
    """Model af elbil-økosystemet i Danmark"""
    
    def __init__(self, working_windmills=200, width=60, height=60, broken_windmills=0):
        super().__init__()
        self.num_working_windmills = working_windmills
        self.num_broken_windmills = broken_windmills
        self.grid = MultiGrid(width, height, True)
        self.current_step = 0
          
        outline_coords = self.create_denmark_outline()
        self.valid_coords = self.create_valid_coords(outline_coords)

        self.create_windmills('standard')
       
        
    def create_windmills(self,turbine_type):
        print("#"*50)
        print("Creating Windmills to map")
        print("#"*50)
        
        positions = self.valid_coords
        random.shuffle(positions)
        if len(positions)>0:
            n_windmills = self.num_working_windmills
            for i in range(0,n_windmills):
                pos = positions.pop()
                if self.grid.is_cell_empty(pos):
                    windmill = Windmill(self, turbine_type)
                    self.grid.place_agent(windmill, pos)
                    print(f"Placed Windmill #{i+1} at: ", pos)
                else:
                    print(f"Position {pos} is already occupied.")

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
           
    def step(self):
        """En simulation step"""
        self.current_step += 1
        
        # Alle agenter tager et step
        for agent in self.agents:
            agent.step()
   