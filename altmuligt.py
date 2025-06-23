#########model

    def get_average_battery_level(self):
        """Gennemsnitligt batteriniveau for alle EVs"""
        ev_agents = [a for a in self.agents if isinstance(a, EVOwner)]
        if not ev_agents:
            return 0
        return sum(a.get_battery_percentage() for a in ev_agents) / len(ev_agents)
    
  #  def get_avg_station_utilization(self):
   #     """Gennemsnitlig udnyttelse af ladestationer"""
    #    stations = [a for a in self.agents if isinstance(a, ChargingStation)]
     #   if not stations:
      #      return 0
       # return sum(a.get_average_utilization() for a in stations) / len(stations)
    
    def get_charging_count(self):
        """Antal EVs der lader lige nu"""
        ev_agents = [a for a in self.agents if isinstance(a, EVOwner)]
        return sum(1 for a in ev_agents if a.is_charging)
    
    def calculate_grid_load(self):
        """Beregner samlet grid-belastning"""
        charging_evs = self.get_charging_count()
        # Antag gennemsnitlig ladehastighed på 22 kW per EV
        return charging_evs * 22  # kW
    
    def get_city_statistics(self):
    
      <p><strong>Lader nu:</strong> {charging_count} ({charging_count/max(1,ev_count)*100:.1f}%)</p>
        <p><strong>Gns. batteriniveau:</strong> {avg_battery:.1f}%</p>
        <p><strong>Grid belastning:</strong> {grid_load:.0f} kW</p>
      


         stats = ModelStats()
    
    # Charts for data over tid
    battery_chart = ChartModule([
        {"Label": "Average_Battery_Level", "Color": "Blue"},
        {"Label": "EVs_Charging", "Color": "Red"}
    ], data_collector_name='datacollector')
    
    grid_load_chart = ChartModule([
        {"Label": "Grid_Load", "Color": "Green"}
    ], data_collector_name='datacollector')
    
    utilization_chart = ChartModule([
        {"Label": "Charging_Stations_Utilization", "Color": "Purple"}
    ], data_collector_name='datacollector')
    