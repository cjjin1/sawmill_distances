########################################################################################################################
# roads_data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Uses osmnx to retrieve roads data
# Usage: <output_roads_file> <output_nodes_files> <aoi>
#        <output_roads_file> <output_nodes_files> <north> <south> <east> <west>
########################################################################################################################

import osmnx as ox
import sys, arcpy, os

#read in area of interest
aoi = sys.argv[3]
#create graph
#if there are 6 input arguments, read in arguments as coordinates for bbox
#otherwise, read in the first argument as the name of place for aoi
graph = None
cf = (
    '[highway~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service|track|road"]'
)
if len(sys.argv) == 7:
    north, south, east, west = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])
    graph = ox.graph_from_bbox((north, south, east, west), custom_filter=cf, simplify=False, retain_all=True)
else:
    graph = ox.graph_from_place(aoi, custom_filter=cf, simplify=False, retain_all=True)

#get nodes and edges from graph
nodes, edges = ox.graph_to_gdfs(graph)

# #copy the edges
# truck_roads = edges.copy()
#
# #remove roads explicitly restricted for heavy goods vehicles
# if 'hgv' in truck_roads.columns:
#     truck_roads = truck_roads[~truck_roads['hgv'].isin(['no'])]

#save the roads and nodes to scratch folder as gpkg files
#nodes are commented out as they are not necessary at this time
edges.to_file("F:/timber_project/scratch/temp_roads.gpkg", layer = "roads", driver = "GPKG")
#nodes.to_file("F:/timber_project/scratch/temp_nodes.gpkg", layer = "nodes", driver = "GPKG")

#convert gpkg files to feature class in File GDB
arcpy.conversion.FeatureClassToFeatureClass(
    in_features = os.path.join("F:/timber_project/scratch/temp_roads.gpkg", "roads"),
    out_path = sys.argv[1],
    out_name = "roads"
)
#delete fields with type big integer
arcpy.management.DeleteField(os.path.join(sys.argv[1], "roads"), ["u", "v", "key", "osmid"])
# arcpy.conversion.FeatureClassToFeatureClass(
#     in_features = os.path.join("F:/timber_project/scratch/temp_nodes.gpkg", "nodes"),
#     out_path = sys.argv[2],
#     out_name = "nodes"
# )

#delete temporary gpkg files
arcpy.management.Delete("F:/timber_project/scratch/temp_roads.gpkg")
#.management.Delete("F:/timber_project/scratch/temp_nodes.gpkg")