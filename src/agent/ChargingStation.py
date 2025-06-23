from mesa import Agent
import random


class ChargingStation(Agent):
    def __init__(self, model, station_type, location):
        super().__init__(model)
        self.station_type = station_type  # 'home', 'work', 'public', 'fast'
        self.max_power = {'home': 11, 'work': 22, 'public': 50, 'fast': 150}[station_type]
        self.occupied_slots = 0
        self.total_slots = random.randint(2, 12)
        self.queue = []
        self.location = location
        self.utilization_history = []