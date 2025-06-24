import requests
import zipfile
import geopandas as gpd
import pandas as pd
import os
from pyproj import Transformer
from shapely.geometry import Point

class WindmillDataHandler:
    def __init__(self):
       pass

    def download_windmill_data(self):
        """Download og udpak vindmølle data fra Energistyrelsen"""
        
        print("Downloader vindmølle data...")
        
        # Direkte zip URL
        zip_url = "https://ens.dk/media/3631/download"
        zip_filename = "vindmoeller.zip"
        extract_dir = "./vindmoeller_data"
        
        try:
            # Download zip fil
            response = requests.get(zip_url)
            response.raise_for_status() 
            
            # Gem zip fil
            with open(zip_filename, "wb") as f:
                f.write(response.content)
            print(f"Download færdig: {zip_filename}")
            
            # Opret folder hvis den ikke eksisterer
            os.makedirs(extract_dir, exist_ok=True)
            
            # Udpak zip fil
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                print(f"Filer udpakket til: {extract_dir}")
                
                # Vis indhold
                files = zip_ref.namelist()
                print("Indhold i zip:")
                for file in files:
                    print(f"  - {file}")
            
            # Find shapefile - søg rekursivt i alle undermapper
            shp_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.shp'):
                        shp_files.append(os.path.join(root, file))
            
            if not shp_files:
                print("Ingen .shp filer fundet")
                print("#### Søger rekursivt i alle mapper ####")
                for root, dirs, files in os.walk(extract_dir):
                    print(f"Mappe: {root}")
                    for file in files:
                        print(f"  - {file}")
                return None
            
            # Brug første shapefile
            shp_path = shp_files[0]
            print(f"Læser shapefile: {shp_path}")
            
            # Læs med geopandas
            gdf = gpd.read_file(shp_path)
            
            print(f"Loaded {len(gdf)} vindmøller")
            print(f"Kolonner: {list(gdf.columns)}")
            print(f"Første 3 rækker:")
            print(gdf.head(3))
            
            if gdf is None:
                print("Ingen data at gemme!")
                return False
            
            try:
                # Konverter geometry til separate lat/lon kolonner for CSV
                gdf_for_csv = gdf.copy()
                
                # Tilføj lat/lon kolonner hvis geometry eksisterer
                if 'geometry' in gdf_for_csv.columns:
                    gdf_for_csv['Latitude'] = gdf_for_csv.geometry.y
                    gdf_for_csv['Longitude'] = gdf_for_csv.geometry.x
                    # Fjern geometry kolonne (kan ikke gemmes i CSV)
                    gdf_for_csv = gdf_for_csv.drop('geometry', axis=1)
                
                # Gem som CSV
                gdf_for_csv.to_csv("vindmoeller_data.csv", index=False, encoding='utf-8')
                print(f"✅ Data gemt som CSV vindmoeller_data.csv")

                
            except Exception as e:
                print(f"❌ Fejl ved gemning af CSV: {e}")
              
            # Ryd op - slet zip fil
            os.remove(zip_filename)
             
            print(f"Typen af gdf: {type(gdf)}")
            return gdf
            
        except requests.RequestException as e:
            print(f"Download fejl: {e}")
            return None
        except zipfile.BadZipFile as e:
            print(f"Zip fil fejl: {e}")
            return None
        except Exception as e:
            print(f"Generel fejl: {e}")
            return None
    
    def get_windmill_positions(self,windmill_data):
        """Returner liste af vindmølle positioner til ABM"""
        if windmill_data is None:
            return []
        
        positions = []
        skipped_count = 0
        
        for idx, row in windmill_data.iterrows():
            # Tjek om geometry eksisterer og ikke er None
            if row.geometry is None or pd.isna(row.geometry):
                skipped_count += 1
                continue
            
            try:
                # Konverter geometry til lat/lon
                lat = row.geometry.y
                lon = row.geometry.x
                
                # Tjek om koordinaterne er gyldige
                if pd.isna(lat) or pd.isna(lon):
                    skipped_count += 1
                    continue
                
                # Hent metadata - prøv forskellige kolonnenavne
                capacity = None
                for col_name in ['KAPACITET', 'kapacitet', 'Kapacitet', 'CAPACITY', 'capacity', 'Capacity']:
                    if col_name in row.index:
                        capacity = getattr(row, col_name, None)
                        if capacity is not None and not pd.isna(capacity):
                            break
                
                # Default kapacitet hvis ingen fundet
                if capacity is None or pd.isna(capacity):
                    capacity = 2.0
                
                positions.append({
                    'id': idx,
                    'lat': lat,
                    'lon': lon,
                    'capacity': float(capacity),
                    'geometry': row.geometry
                })
                
            except Exception as e:
                print(f"Fejl ved behandling af række {idx}: {e}")
                skipped_count += 1
                continue
        
        if skipped_count > 0:
            print(f"Advarsel: {skipped_count} vindmøller sprunget over pga. manglende/ugyldig geometri")
        
        print(f"Behandlet {len(positions)} gyldige vindmøller")
        return positions
    
    def get_summary(self,windmill_data):
        """Få oversigt over data"""
        if windmill_data is None:
            return "Ingen data loaded"
        
        total_count = len(windmill_data)
        
        # Prøv at finde kapacitets-kolonne
        capacity_col = None
        for col in ['KAPACITET', 'capacity', 'Kapacitet', 'CAPACITY']:
            if col in windmill_data.columns:
                capacity_col = col
                break
        
        if capacity_col:
            total_capacity = windmill_data[capacity_col].sum()
            avg_capacity = windmill_data[capacity_col].mean()
            
            return f"""
            Vindmølle Data Oversigt:
            - Total antal: {total_count}
            - Total kapacitet: {total_capacity:.1f} MW
            - Gennemsnit kapacitet: {avg_capacity:.1f} MW
            - Kolonner: {list(windmill_data.columns)}
            """
        else:
            return f"""
                Vindmølle Data Oversigt:
                - Total antal: {total_count}
                - Kolonner: {list(windmill_data.columns)}
            """
 

    def transform_utm_to_wgs84(self,gdf, utm_crs="EPSG:25832", target_crs="EPSG:4326"):
        """
        Konverter UTM koordinater til WGS84 (latitude/longitude)
        
        Parameters:
        -----------
        gdf : geopandas.GeoDataFrame
            GeoDataFrame med UTM koordinater
        utm_crs : str
            UTM koordinatsystem (default: "EPSG:25832" for ETRS 1989 UTM zone 32N)
        target_crs : str
            Mål koordinatsystem (default: "EPSG:4326" for WGS84)
        
        Returns:
        --------
        geopandas.GeoDataFrame
            GeoDataFrame med tilføjede Latitude og Longitude kolonner
        """
        
        print(type(gdf))
        # Lav en kopi så vi ikke ændrer original
        gdf_converted = gdf.copy()
        
        try:
            # Opret transformer
            transformer = Transformer.from_crs(utm_crs, target_crs, always_xy=True)
            
            # Konverter koordinater
            latitudes = []
            longitudes = []
            
            for idx, row in gdf_converted.iterrows():
                try:
                    if row.geometry is not None and not row.geometry.is_empty:
                        # Konverter UTM til WGS84
                        lon, lat = transformer.transform(row.geometry.x, row.geometry.y)
                        latitudes.append(lat)
                        longitudes.append(lon)
                    else:
                        latitudes.append(None)
                        longitudes.append(None)
                except Exception as e:
                    print(f"Fejl ved konvertering af række {idx}: {e}")
                    latitudes.append(None)
                    longitudes.append(None)
            
            # Tilføj nye kolonner
            gdf_converted['Latitude'] = latitudes
            gdf_converted['Longitude'] = longitudes
            
            # Statistik
            valid_coords = sum(1 for lat, lon in zip(latitudes, longitudes) 
                            if lat is not None and lon is not None)
            
            print(f"✅ Konverteret {valid_coords}/{len(gdf_converted)} koordinater")
            
            return gdf_converted
            
        except Exception as e:
            print(f"❌ Fejl ved coordinate transformation: {e}")
            return gdf
    

    def save_with_coordinates(self,gdf_with_coords, filename="vindmoeller_with_coordinates.csv"):
        """
        Gem GeoDataFrame som CSV med både UTM og WGS84 koordinater
        
        Parameters:
        -----------
        gdf_with_coords : geopandas.GeoDataFrame
            GeoDataFrame med konverterede koordinater
        filename : str
            Filnavn til at gemme CSV
        """
        
        try:
            # Lav kopi til CSV (fjern geometry)
            csv_data = gdf_with_coords.copy()
            
            # Bevar originale UTM koordinater
            if 'geometry' in csv_data.columns:
                csv_data['UTM_X'] = csv_data.geometry.x
                csv_data['UTM_Y'] = csv_data.geometry.y
                csv_data = csv_data.drop('geometry', axis=1)
            
            # Gem som CSV
            csv_data.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Data gemt som: {filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Fejl ved gemning: {e}")
            return False


    