from mesa_viz_tornado.modules import CanvasGrid, ChartModule, TextElement
from mesa_viz_tornado.ModularVisualization import ModularServer

# Korrekte imports baseret på din filstruktur
from agent.EVOwner import EVOwner
from agent.ChargingStation import ChargingStation  
from model.model import EVModel   
from agent.DenmarkOutline import DenmarkOutline

# Resten af din kode forbliver den samme...

def agent_portrayal(agent):
    """Definerer hvordan agenter vises"""


    if isinstance(agent, DenmarkOutline):
        # Danmarks omrids - tynd grøn linje
        portrayal = {
            "Shape": "rect",
            "Color": "darkgreen",
            "Filled": "false",  # Kun omrids
            "Layer": -1,  # Baggrund
            "w": 0.9,
            "h": 0.9,
            "stroke_color": "green",
            "stroke_width": 2
        }
        
    elif isinstance(agent, EVOwner):
        # EV-ejere: Farve baseret på batteriniveau
        battery_pct = agent.get_battery_percentage()
        
        if battery_pct > 70:
            color = "green"  # Høj batteriniveau
        elif battery_pct > 30:
            color = "orange"  # Medium batteriniveau
        else:
            color = "red"  # Lav batteriniveau - skal lade!
        
        # Hvis de lader, gør dem større
        size = 0.8 if agent.is_charging else 0.6
        
        portrayal = {
            "Shape": "circle",
            "Color": color,
            "Filled": "true",
            "Layer": 1,  # EVs ovenpå ladestationer
            "r": size
        }
        
    elif isinstance(agent, ChargingStation):
        # Ladestationer: Farve og form baseret på type
        station_colors = {
            'home': 'blue',
            'work': 'purple', 
            'public': 'darkgreen',
            'fast': 'gold'
        }
        
        color = station_colors.get(agent.station_type, 'gray')
        
        # Størrelse baseret på udnyttelse
      #  utilization = agent.get_average_utilization()
    #    size = 0.3 + (utilization * 0.5)  # Mellem 0.3 og 0.8
        
        portrayal = {
            "Shape": "rect",
            "Color": color,
            "Filled": "true",
            "Layer": 0,  # Under EVs
        }
    
    else:
        # Fallback for ukendte agenttyper
        portrayal = {
            "Shape": "circle",
            "Color": "gray",
            "Filled": "true",
            "Layer": 0,
            "r": 0.3
        }
    
    return portrayal

class ModelStats(TextElement):
    """Viser model-statistikker i realtid"""
    
    def render(self, model):
        ev_count = len([a for a in model.agents if isinstance(a, EVOwner)])
        station_count = len([a for a in model.agents if isinstance(a, ChargingStation)])
    #    charging_count = model.get_charging_count()
    #    avg_battery = model.get_average_battery_level()
    #    grid_load = model.calculate_grid_load()
        
        return f"""
        <h3>Danmark EV Model - Step {model.current_step}</h3>
        <p><strong>Elbiler:</strong> {ev_count}</p>
        <p><strong>Ladestationer:</strong> {station_count}</p>
      
        
        <h4>Farve guide:</h4>
        <p style="color: green;">🟢 EV: Batteriniveau > 70%</p>
        <p style="color: orange;">🟠 EV: Batteriniveau 30-70%</p>
        <p style="color: red;">🔴 EV: Batteriniveau < 30%</p>
        <p style="color: blue;">🔷 Hjemmelader</p>
        <p style="color: purple;">🟣 Arbejdsplads lader</p>
        <p style="color: darkgreen;">🟩 Offentlig lader</p>
        <p style="color: gold;">🟨 Hurtiglader</p>
        """

def create_server():
    """Opretter og returnerer visualiseringsserver"""
    
    # Grid visualisering
    grid = CanvasGrid(agent_portrayal, 70, 70, 1000, 1000)
    
    # Statistik element
 #
    # Model parametre som kan justeres i browseren
    model_params = {
        "num_ev_owners":100,
        "num_charging_stations": 25,
        "width": 70,  # Fast værdi
        "height": 70   # Fast værdi
    }
    
    # Opret server
    server = ModularServer(
        EVModel,
        [grid],#, stats, battery_chart, grid_load_chart, utilization_chart],
        "Danmark - Elbiler",
        model_params
    )
    
    return server

def launch_server(port=8521):
    """Starter visualiseringsserveren"""
    server = create_server()
    server.port = port
    server.launch()

if __name__ == "__main__":
    launch_server()