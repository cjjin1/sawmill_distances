########################################################################################################################
# osm_roads.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Uses osmnx to retrieve roads data, can retrieve one specific type of road along with truck only roads
# Usage: <output_roads_file_GDB> <aoi> <aoi type(place or shapefile)> <output_name>
########################################################################################################################

import osmnx as ox
import geopandas as gpd
import sys, arcpy, os

def export_to_arcgis(edges, file, layer):
    """Converts the edges of a graph to a GPKG file, then to a feature class, removing Big Integer type fields"""
    edges.to_file(file, layer = layer, driver = "GPKG")
    arcpy.conversion.FeatureClassToFeatureClass(
        in_features=os.path.join(file, layer),
        out_path=sys.argv[1],
        out_name=layer
    )
    arcpy.management.DeleteField(os.path.join(sys.argv[1], layer), ["u", "v", "key", "osmid"])
    arcpy.management.Delete(file)

arcpy.env.overwriteOutput = True

#read in area of interest
aoi = sys.argv[2]
aoi_type = sys.argv[3]
fc_name = sys.argv[4]
#create graph with custom filter
g_main = None
cf = (
    '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|road|service"]'
)
#check what kind of input was read (shapefile or place name)
if aoi_type == "aoi":
    g_main = ox.graph_from_place(aoi, custom_filter=cf, simplify=False, retain_all=True)
elif aoi_type == "shapefile":
    gdf = gpd.read_file(aoi)
    # Ensure CRS is EPSG:4326
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    polygon = gdf.geometry.iloc[0]
    g_main = ox.graph_from_polygon(polygon, custom_filter=cf, network_type="drive")

#get nodes and edges from graph
nodes_main, edges_main = ox.graph_to_gdfs(g_main)

#save the roads to scratch folder as gpkg files, then export to feature class in File GDB
temp_file = "C:/timber_project/scratch/temp_roads.gpkg"
export_to_arcgis(edges_main, temp_file, fc_name)