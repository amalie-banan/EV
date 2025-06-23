from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
import random
import math

# Korrekte imports til dine agent klasser
from agent.EVOwner import EVOwner
from agent.ChargingStation import ChargingStation
from agent.GridNode import GridNode  
from agent.DenmarkOutline import DenmarkOutline
from helper.helper_functions import create_elliptical_octagon_outline_precise,get_cells_inside_outline_scanline

class EVModel(Model):
    """Model af elbil-økosystemet i Danmark"""
    
    def __init__(self, num_ev_owners=200, width=60, height=60, num_charging_stations=20):
        super().__init__()
        self.num_ev_owners = num_ev_owners
        self.num_charging_stations = num_charging_stations
        self.grid = MultiGrid(width, height, True)
        self.current_step = 0
        
        # Definer danske byer som klynger
        self.city_clusters = {
            'København': {
                'center': (58, 17),  # Sydøst (højre side, nederst)
                'radius': 5,
                'population_weight': 0.35,
                'density_multiplier': 3.5
            },
            'Aarhus': {
                'center': (25, 35),  # Midtjylland (midt på kortet)
                'radius': 4,
                'population_weight': 0.18,
                'density_multiplier': 2.8
            },
            'Odense': {
                'center': (31, 21),  # Fyn (mellem Jylland og Sjælland)
                'radius': 3,
                'population_weight': 0.10,
                'density_multiplier': 2.2
            },
            'Aalborg': {
                'center': (22, 58),  # Nordjylland (øverst på kortet)
                'radius': 3,
                'population_weight': 0.08,
                'density_multiplier': 1.9
            },
            'Esbjerg': {
                'center': (11, 28),  # Vestjylland
                'radius': 2,
                'population_weight': 0.04,
                'density_multiplier': 1.4
            },
            'Randers': {
                'center': (28, 42),  # Østjylland
                'radius': 2,
                'population_weight': 0.03,
                'density_multiplier': 1.3
            },
            'Holstebro': {
                'center': (17, 39),  # Vestjylland
                'radius': 1,
                'population_weight': 0.02,
                'density_multiplier': 1.0
            }
        }
        
        
        # Data collection
     #   self.datacollector = DataCollector(
        #    model_reporters={
        #        "Total_EVs": lambda m: len([a for a in m.agents if isinstance(a, EVOwner)]),
         #       "Average_Battery_Level": self.get_average_battery_level,
            #    "Charging_Stations_Utilization": self.get_avg_station_utilization,
           #     "EVs_Charging": self.get_charging_count,
        #        "Grid_Load": self.calculate_grid_load
         #   },
         #   agent_reporters={
          #     "Battery_Percentage": lambda a: a.get_battery_percentage() if isinstance(a, EVOwner) else None,
           #     "Is_Charging": lambda a: a.is_charging if isinstance(a, EVOwner) else None,
              #  "Station_Utilization": lambda a: a.get_average_utilization() if isinstance(a, ChargingStation) else None
           # }
        #)
        
        # Opret sandsynlighedskort og agenter
        self.probability_map = self.create_probability_map()
        outline_coords = self.create_denmark_outline()
        self.valid_coords = self.create_valid_coords(outline_coords)
        self.create_ev_owners()
       
     #   self.create_charging_stations()
        
        # Indsaml initial data
    #    self.datacollector.collect(self)
    
    def create_probability_map(self):
        print("#"*50)
        print("Creating probability map")
        print("#"*50)
        """Skaber sandsynlighedskort baseret på byklynger"""
        prob_map = np.ones((self.grid.width, self.grid.height)) * 0.1
        print(prob_map)
        
        for city, data in self.city_clusters.items():
            center_x, center_y = data['center']
            radius = data['radius']
            multiplier = data['density_multiplier']
            
            for x in range(max(0, center_x - radius), min(self.grid.width, center_x + radius + 1)):
                for y in range(max(0, center_y - radius), min(self.grid.height, center_y + radius + 1)):
                    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius:
                        decay = max(0.1, 1 - (distance / radius) * 0.7)
                        prob_map[x][y] = multiplier * decay
        
        return prob_map
    
    def create_ev_owners(self): 
        print("#"*50)
        print("Creating EV owners")
        print("#"*50)
        
        danish_positions = self.valid_coords
        # Beregn sandsynligheder
        danish_probs = []
        for x, y in danish_positions:
            prob = self.probability_map[x, y]
            danish_probs.append(prob)
    
        # Normaliser og placer agenter
        if len(danish_positions) > 0:
            danish_probs = np.array(danish_probs)
            danish_probs = danish_probs / np.sum(danish_probs)
            
            num_to_create = min(self.num_ev_owners, len(danish_positions))
            
            chosen_indices = np.random.choice(
                len(danish_positions), 
                size=num_to_create, 
                p=danish_probs, 
                replace=False
            )
            
            for i, pos_idx in enumerate(chosen_indices):
                x, y = danish_positions[pos_idx]
                ev_owner = EVOwner(self)
                self.grid.place_agent(ev_owner, (x, y))
                print(f"Placed EVOwner #{i+1} at: ({x},{y})")
            
            print(f"Successfully created {num_to_create} EV owners")
        
    def create_charging_stations(self):
        print("#"*50)
        print("Creating Charging stations")
        print("#"*50)
        """Opretter ladestationer i byerne"""
        for city, data in self.city_clusters.items():
            center_x, center_y = data['center']
            radius = data['radius']
            
            # Antal stationer baseret på byens størrelse
            num_stations = max(1, int(data['population_weight'] * self.num_charging_stations))
            
            for _ in range(num_stations):
                # Placer station i eller nær bycentret
                x = random.randint(
                    max(0, center_x - radius), 
                    min(self.grid.width - 1, center_x + radius)
                )
                y = random.randint(
                    max(0, center_y - radius), 
                    min(self.grid.height - 1, center_y + radius)
                )
                
                # Find ledig plads
                if not self.grid.is_cell_empty((x, y)):
                    possible_positions = self.grid.get_neighborhood((x, y), moore=True, radius=3)
                    empty_positions = [pos for pos in possible_positions if self.grid.is_cell_empty(pos)]
                    if empty_positions:
                        x, y = self.random.choice(empty_positions)
                    else:
                        continue
                
                # Bestem stationstype baseret på by
                if data['density_multiplier'] > 2.5:  # Store byer
                    station_type = random.choice(['public', 'fast', 'work'])
                else:  # Mindre byer
                    station_type = random.choice(['public', 'work'])
                
                charging_station = ChargingStation(self, station_type,(x,y))
                self.grid.place_agent(charging_station, (x, y))

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
        return outline_coordinates
    def create_valid_coords(self,outline_coords):
        # Find alle celler INDE I Danmark
        denmark_inside_cells = get_cells_inside_outline_scanline(outline_coords, self.grid.width, self.grid.height)
        print(denmark_inside_cells)
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
        
        # Indsaml data
      #  self.datacollector.collect(self)
    
        """Returnerer statistik per by"""
        city_stats = {}
        
        for city, data in self.city_clusters.items():
            center_x, center_y = data['center']
            radius = data['radius']
            
            ev_count = 0
            station_count = 0
            
            for x in range(max(0, center_x - radius), min(self.grid.width, center_x + radius + 1)):
                for y in range(max(0, center_y - radius), min(self.grid.height, center_y + radius + 1)):
                    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance <= radius:
                        agents_in_cell = self.grid.get_cell_list_contents([(x, y)])
                        ev_count += len([a for a in agents_in_cell if isinstance(a, EVOwner)])
                        station_count += len([a for a in agents_in_cell if isinstance(a, ChargingStation)])
            
            city_stats[city] = {
                'ev_count': ev_count,
                'station_count': station_count,
                'ev_per_station': ev_count / max(1, station_count)
            }
        
        return city_stats