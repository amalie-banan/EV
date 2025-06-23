from mesa_viz_tornado.modules import CanvasGrid, ChartModule, TextElement
from mesa_viz_tornado.ModularVisualization import ModularServer

# Korrekte imports baseret på din filstruktur
from model.model import EVModel   

from agent.Windmill import Windmill
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
            "w": 0.5,
            "h": 0.8,
            "stroke_color": "green",
            "stroke_width": 2
        }
    elif isinstance(agent, Windmill):
         
         portrayal = {
            "Shape": "rect",
            "Color": "blue",
            "Filled": "True",  # Kun omrids
            "Layer": 1,  # Foran
            "w": 1,
            "h": 1
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
        ev_count = len([a for a in model.agents if isinstance(a, Windmill)])
        #station_count = len([a for a in model.agents if isinstance(a, ChargingStation)])
    #    charging_count = model.get_charging_count()
    #    avg_battery = model.get_average_battery_level()
    #    grid_load = model.calculate_grid_load()
        
        return f"""
        <h3>Danmark EV Model - Step {model.current_step}</h3>
        <p><strong>Elbiler:</strong> {ev_count}</p>
        
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
    
    # Model parametre som kan justeres i browseren
    model_params = {
        "working_windmills": 10,
        "broken_windmills": 1,
        "width": 70,  # Fast værdi
        "height": 70   # Fast værdi
    }
    
    # Opret server
    server = ModularServer(
        EVModel,
        [grid],  # Tilføj andre visualiseringselementer her hvis nødvendigt
        "Danmark - Vindmøller",
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