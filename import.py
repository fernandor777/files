from sqlalchemy import create_engine
import geopandas as gpd

user = "postgres"
password = "admin"
host = "localhost"
port = 5432
database = "postgis_in_action"
source_file = "boundary_shp/boundary.shp"
target_schema = "public"
target_table = "boundary"

conn = f"postgresql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(conn)

#Read shapefile using GeoPandas
gdf = gpd.read_file(source_file)

#Import shapefile to databse
gdf.to_postgis(name=target_table, con=engine, schema=target_schema)

print("success")
