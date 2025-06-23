import random 
from mesa import Agent 

class EnergyPacket(Agent):
    def step(self):
        # Energi "bevæger sig" gennem transmission-nettet
        next_station = self.find_path_to_destination()
        self.move_to(next_station)
         