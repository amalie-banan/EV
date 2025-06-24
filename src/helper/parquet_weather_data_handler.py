import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
import time
import pyarrow as pa
import pyarrow.parquet as pq
from helper.helper_functions import map_coordinates_to_grid

class ParquetWeatherHandler:
    def __init__(self, startdate='2024-01-01T00:00:00Z', enddate='2024-01-02T00:00:00Z'):
        self.startdate = startdate
        self.enddate = enddate
        self.dmi_api_key = "87f0ab67-b82c-427a-9fdd-2fecacf8da2f"
        self.dmi_base_url = "https://dmigw.govcloud.dk/v2/metObs/collections/observation/items"
        
        # Setup data directory
        self.data_dir = Path("weather_parquet_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Danmarks regioner for chunk processing
        self.regions = {
            'nordjylland': '8.0,56.5,11.0,57.8',
            'midtjylland': '8.0,55.5,11.0,56.5', 
            'sydjylland': '8.0,54.8,10.0,55.5',
            'fyn': '9.5,55.0,11.0,55.7',
            'nordsjælland': '11.5,55.6,12.8,56.2',
            'midtsjælland': '10.8,55.2,12.5,55.6',
            'sydsjælland': '10.8,54.9,12.5,55.2',
        }
        
        # Vejrparametre
        self.parameters = [
            'temp_mean_past1h',
            'wind_speed_past1h', 
            'wind_dir_past1h'
        ]
        
        print(f"🎯 Parquet Weather Handler initialiseret")
        print(f"📅 Periode: {startdate} til {enddate}")
        print(f"📁 Data gemmes i: {self.data_dir}")
        print(f"🗺️  {len(self.regions)} regioner, {len(self.parameters)} parametre")

        
    
    def create_time_chunks(self, chunk_days=7):
        """Opdel tidsperiode i chunks"""
        start = datetime.fromisoformat(self.startdate.replace('Z', '+00:00'))
        end = datetime.fromisoformat(self.enddate.replace('Z', '+00:00'))
        
        chunks = []
        current = start
        
        while current < end:
            chunk_end = min(current + timedelta(days=chunk_days), end)
            chunks.append({
                'start': current.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'end': chunk_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'date_str': current.strftime('%Y%m%d')
            })
            current = chunk_end
        
        return chunks
    
    def download_chunk(self, region_name, bbox, parameter, time_chunk):
        """Download ét chunk af data"""
        try:
            params = {
                'datetime': f"{time_chunk['start']}/{time_chunk['end']}",
                'bbox': bbox,
                'parameterId': parameter,
                'api-key': self.dmi_api_key,
                'limit': 10000
            }
            
            response = requests.get(self.dmi_base_url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                observations = []
                
                for obs in data.get('features', []):
                    properties = obs['properties']
                    coordinates = obs['geometry']['coordinates']
                    
                    observation = {
                        'observed': properties.get('observed'),
                        'station_id': properties.get('stationId'),
                        'parameter_id': parameter,
                        'value': properties.get('value'),
                        'longitude': coordinates[0],
                        'latitude': coordinates[1],
                        'region': region_name
                    }
                    observations.append(observation)
                
                return observations
            
            elif response.status_code == 429:
                print(f"⏳ Rate limited - venter 30 sekunder")
                time.sleep(30)
                return self.download_chunk(region_name, bbox, parameter, time_chunk)
            
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error downloading chunk: {e}")
            return []
    
    def save_parquet_chunk(self, observations, region_name, parameter, chunk_date):
        """Gem chunk som Parquet fil"""
        if not observations:
            return False
        
        # Konverter til DataFrame
        df = pd.DataFrame(observations)
        df['observed'] = pd.to_datetime(df['observed'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Fjern NaN værdier
        df = df.dropna(subset=['value'])
        
        if len(df) == 0:
            return False
        
        # Filnavn: region_parameter_YYYYMMDD.parquet
        filename = f"{region_name}_{parameter}_{chunk_date}.parquet"
        filepath = self.data_dir / filename
        
        # Gem med compression
        df.to_parquet(
            filepath, 
            compression='snappy',
            index=False,
            engine='pyarrow'
        )
        
        print(f"💾 {filename}: {len(df)} records")
        return True
    
    def download_all_data(self, chunk_days=7):
        """Download alle data i chunks"""
        print(f"\n🚀 Starter download med {chunk_days}-dages chunks...")
        
        time_chunks = self.create_time_chunks(chunk_days)
        total_operations = len(time_chunks) * len(self.regions) * len(self.parameters)
        
        print(f"📊 Total operationer: {total_operations}")
        print(f"⏱️  Estimeret tid: ~{total_operations * 2 / 60:.0f} minutter")
        
        operation_count = 0
        successful_chunks = 0
        total_records = 0
        
        for chunk_idx, time_chunk in enumerate(time_chunks):
            print(f"\n📅 Chunk {chunk_idx+1}/{len(time_chunks)}: {time_chunk['start'][:10]}")
            
            for region_name, bbox in self.regions.items():
                for parameter in self.parameters:
                    operation_count += 1
                    
                    print(f"  {operation_count}/{total_operations} | {region_name} | {parameter}", end=" -> ")
                    
                    # Download data
                    observations = self.download_chunk(region_name, bbox, parameter, time_chunk)
                    
                    if observations:
                        # Save som Parquet
                        success = self.save_parquet_chunk(
                            observations, region_name, parameter, time_chunk['date_str']
                        )
                        
                        if success:
                            successful_chunks += 1
                            total_records += len(observations)
                    else:
                        print("Ingen data")
                    
                    # Rate limiting
                    time.sleep(1)
        
        print(f"\n🎉 Download færdig!")
        print(f"✅ Successful chunks: {successful_chunks}")
        print(f"📈 Total records: {total_records:,}")
        print(f"💽 Data location: {self.data_dir}")
        
        return self.get_data_summary()
    
    def get_data_summary(self):
        """Få oversigt over gemte data"""
        parquet_files = list(self.data_dir.glob("*.parquet"))
        
        if not parquet_files:
            return {"status": "No data files found"}
        
        total_size = sum(f.stat().st_size for f in parquet_files)
        
        # Load sample for analysis
        sample_df = pd.read_parquet(parquet_files[0])
        
        summary = {
            "total_files": len(parquet_files),
            "total_size_mb": round(total_size / (1024*1024), 2),
            "data_directory": str(self.data_dir),
            "parameters": list(self.parameters),
            "regions": list(self.regions.keys()),
            "sample_records": len(sample_df),
            "sample_time_range": f"{sample_df['observed'].min()} to {sample_df['observed'].max()}"
        }
        
        return summary
    
    def load_data(self, region=None, parameter=None, start_date=None, end_date=None):
        """Load data med filtering"""
        parquet_files = list(self.data_dir.glob("*.parquet"))
        print("HEJHEJEHJEH")
        if not parquet_files:
            print("❌ Ingen Parquet filer fundet")
            return pd.DataFrame()
        
        # Filter files based on criteria
        filtered_files = []
        for file in parquet_files:
            filename = file.stem
            
            # Check region filter
            if region and region not in filename:
                continue
            
            # Check parameter filter  
            if parameter and parameter not in filename:
                continue
            
            filtered_files.append(file)
        
        if not filtered_files:
            print(f"❌ Ingen filer matcher criteria: region={region}, parameter={parameter}")
            return pd.DataFrame()
        
        print(f"📂 Loading {len(filtered_files)} Parquet files...")
        
        # Load and combine all files
        dfs = []
        for file in filtered_files:
            try:
                df = pd.read_parquet(file)
                dfs.append(df)
            except Exception as e:
                print(f"⚠️  Fejl ved loading {file}: {e}")
        
        if not dfs:
            return pd.DataFrame()
        
        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Apply date filters
        if start_date:
            combined_df = combined_df[combined_df['observed'] >= pd.to_datetime(start_date)]
        if end_date:
            combined_df = combined_df[combined_df['observed'] <= pd.to_datetime(end_date)]
        
        # Sort by observed time
        combined_df = combined_df.sort_values('observed').reset_index(drop=True)
        
        print(f"✅ Loaded {len(combined_df):,} records")
        return combined_df

