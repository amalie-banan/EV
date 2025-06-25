from mesa_viz_tornado.modules import CanvasGrid, ChartModule, TextElement
from mesa_viz_tornado.ModularVisualization import ModularServer

# Korrekte imports baseret på din filstruktur
from model.model import WindEnergyModel   
from agent.Windmill import Windmill
from agent.DenmarkOutline import DenmarkOutline

def agent_portrayal(agent):
    """Definerer hvordan agenter vises"""

    if isinstance(agent, DenmarkOutline):
        portrayal = {
            "Shape": "rect", "Color": "darkgreen","Filled": "false", "Layer": -1,"w": 0.5,"h": 0.8,"stroke_color": "green","stroke_width": 2}
    elif isinstance(agent, Windmill):
        if agent.scaling_factor >= 20:
            portrayal = {"Shape": "rect", "Color": "red", "Filled": "True", "Layer": 1, "w": 1, "h": 1}
        elif 10 < agent.scaling_factor < 20:
            portrayal = {"Shape": "rect", "Color": "orange", "Filled": "True", "Layer": 1, "w": 1, "h": 1}
        elif 5 < agent.scaling_factor <= 10:
            portrayal = {"Shape": "rect", "Color": "yellow", "Filled": "True", "Layer": 1, "w": 1, "h": 1}
        elif 1 < agent.scaling_factor <= 5:
            portrayal = {"Shape": "rect", "Color": "#006400", "Filled": "True", "Layer": 1, "w": 1, "h": 1}
        else:
            portrayal = {"Shape": "rect", "Color": "#90EE90", "Filled": "True", "Layer": 1, "w": 1, "h": 1}
    else:
        portrayal = {"Shape": "circle", "Color": "gray", "Filled": "true", "Layer": 0, "r": 0.3}
    
    return portrayal

class ModelStats(TextElement):
    """Viser model-statistikker i realtid"""
    
    def render(self, model):
        ev_count = len([a for a in model.agents if isinstance(a, Windmill)])
        return f"""
        <h3>Danmark EV Model - Step {model.current_step}</h3>
        <p><strong>Elbiler:</strong> {ev_count}</p>
        """

def create_server():
    """Opretter og returnerer visualiseringsserver"""
    print("Creating server...")
    
    grid = CanvasGrid(agent_portrayal, 100, 100, 1000, 1000)
    get_data_startdate = '2024-01-01T23:59:59Z'
    get_data_enddate = '2024-01-08T23:59:59Z'
    
    model_params = {
        "working_windmills": 1400,
        "broken_windmills": 1,
        'time_resolution': 'daily',
        "create_windmill_data": False,
        "create_weather_data": False,
        "weather_data_startdate": get_data_startdate,
        "weather_data_enddate": get_data_enddate,
        "width": 90,
        "height": 90
    }
    
    server = ModularServer(
        WindEnergyModel,
        [grid],
        "Danmark - Vindmøller",
        model_params
    )
    
    return server

def launch_server(port=8521):
    """Starter visualiseringsserveren"""
    print("Launching server...")
    server = create_server()
    server.port = port
    server.launch()
 