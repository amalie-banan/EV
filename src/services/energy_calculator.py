import math
import numpy as np
import pandas as pd

class EnergyCalculator:
    def __init__(self, rotordiameter, capacity_kw, turbine_direction=0, cp=0.4):
        self.rotordiameter = rotordiameter
        self.capacity_kw = capacity_kw
        self.turbine_direction = turbine_direction
        self.cp = cp
        self.area = math.pi * (rotordiameter / 2) ** 2

    def calculate_energy(self, weather_df: pd.DataFrame, time_resolution='hourly'):
        """
        weather_df: DataFrame med MultiIndex, hvor 'timestamp' er en af levels
        Skal indeholde kolonner: wind_speed, wind_dir, temp
        time_resolution: 'hourly', 'daily', 'weekly', 'monthly'
        Returnerer: DataFrame med energy_kWh pr. tidsperiode
        """
        # Tjek om 'timestamp' findes i index levels
        if 'timestamp' not in weather_df.index.names:
            raise ValueError("weather_df skal have 'timestamp' som en del af index")

        # Lav kopi for at undgå mutation
        df = weather_df.copy()

        # Hent tid som datetime Series fra index
        timestamps = df.index.get_level_values("timestamp")

        # Konverter til NumPy arrays
        wind_speed = df['wind_speed'].to_numpy()
        wind_dir = df['wind_dir'].to_numpy()
        temp_c = df['temp'].to_numpy()

        # Beregn effektiv vindretning
        theta_rad = np.radians(wind_dir - self.turbine_direction)
        effective_wind = wind_speed * np.clip(np.cos(theta_rad), 0, None)

        # Lufttæthed (rho)
        rho = 1.225 * (273.15 / (temp_c + 273.15))

        # Beregn rå power
        power_kw = 0.5 * rho * self.area * effective_wind**3 * self.cp / 1000
        power_kw = np.where((effective_wind >= 3) & (effective_wind <= 25), power_kw, 0)
        power_kw = np.minimum(power_kw, self.capacity_kw)

        # Tilføj kolonne
        df['power_kw'] = power_kw

        # Tilføj tidsstempel som kolonne
        df = df.copy()
        df['timestamp'] = timestamps

        # Map tidsopløsning
        freq_map = {
            'hourly': 'h',
            'daily': 'd',
            'weekly': 'w',
            'monthly': 'm'
        }

        if time_resolution not in freq_map:
            raise ValueError("Ugyldig time_resolution. Brug: 'hourly', 'daily', 'weekly', 'monthly'.")

        # Sæt timestamp som index og resample
        df = df.set_index('timestamp')
        energy = df['power_kw'].resample(freq_map[time_resolution]).sum().rename("energy_kWh")

        return energy.reset_index()