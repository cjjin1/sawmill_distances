########################################################################################################################
# roads_data_prep.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Uses osmnx to retrieve roads data
# Usage: <output_roads_file> <output_nodes_files> <aoi>
#        <output_roads_file> <output_nodes_files> <north> <south> <east> <west>
########################################################################################################################

import osmnx as ox
import sys

#read in area of interest
aoi = sys.argv[3]
#create graph
#if there are 4 input arguments, read in arguments as coordinates for bbox
#otherwise, read in the first argument as the name of place for aoi
graph = None
if len(sys.argv) == 7:
    north = float(sys.argv[3])
    south = float(sys.argv[4])
    east = float(sys.argv[5])
    west = float(sys.argv[6])
    graph = ox.graph_from_bbox((north, south, east, west), network_type = "drive")
else:
    graph = ox.graph_from_place(aoi, network_type='drive')

#get nodes and edges from graph
nodes, edges = ox.graph_to_gdfs(graph)

#copy the edges
truck_roads = edges.copy()

#remove roads explicitly restricted for heavy goods vehicles
if 'hgv' in truck_roads.columns:
    truck_roads = truck_roads[~truck_roads['hgv'].isin(['no'])]

#save the roads and nodes to data folder
truck_roads.to_file(sys.argv[1])
nodes.to_file(sys.argv[2])