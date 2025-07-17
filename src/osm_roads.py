########################################################################################################################
# osm_roads.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Uses osmnx to retrieve roads data, can retrieve one specific type of road along with truck only roads
# Usage: <output_roads_file> <output_nodes_files> <aoi> <road type[optional]>
#        <output_roads_file> <output_nodes_files> <north> <south> <east> <west> <road type[optional]>
########################################################################################################################

import osmnx as ox
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
aoi = sys.argv[3]
#create graph
#if there are 6 input arguments, read in arguments as coordinates for bbox
#otherwise, read in the first argument as the name of place for aoi
g_main = None
g_single = None
single_road_type = None

cf = (
    '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|road"]'
)
if len(sys.argv) >= 7:
    north, south, east, west = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
    g_main = ox.graph_from_bbox(
        (north, south, east, west), custom_filter=cf, simplify=False, retain_all=True
    )
    if len(sys.argv) == 8:
        single_road_type = sys.argv[7]
        cf_single = f'["highway"="{single_road_type}"]'
        g_single = ox.graph_from_bbox(
            (north, south, east, west), custom_filter=cf_single, simplify=False, retain_all=True
        )
elif len(sys.argv) >= 4:
    g_main = ox.graph_from_place(aoi, custom_filter=cf, simplify=False, retain_all=True)
    if len(sys.argv) == 5:
        single_road_type = sys.argv[4]
        cf_single = f'["highway"="{single_road_type}"]'
        g_single = ox.graph_from_place(aoi, custom_filter=cf_single, simplify=False, retain_all=True)

#get nodes and edges from graph
nodes_main, edges_main = ox.graph_to_gdfs(g_main)

#save the roads to scratch folder as gpkg files, then export to feature class in File GDB
temp_file = "E:/timber_project/scratch/temp_roads.gpkg"
layer_name = "roads"
export_to_arcgis(edges_main, temp_file, layer_name)
if single_road_type:
    nodes_single, edges_single = ox.graph_to_gdfs(g_single)
    export_to_arcgis(edges_single, temp_file, f"{single_road_type}s")