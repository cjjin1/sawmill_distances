########################################################################################################################
# distance_calculator.py
# Author: James Jin
# unity ID: cjjin
# Purpose: Calculates distance from a point on a public road to the nearest sawmill
# Usage: <Workspace> <Public Roads Shapefile> <NFS exit points> <sawmills>
########################################################################################################################

import arcpy, sys, os
from arcpy.sa import *

def calculate_distance(starting_point, roads, sawmill, output_path):
    """Takes in a starting point, roads raster, and a sawmill destination
       Finds the distance from the starting point to the sawmill destination
       Returns a feature class containing a path and distance
       Can accommodate multiple destinations if destination is unknown, will find
       the closest destination out of the entire sawmill feature class"""
    road_cost = CostDistance(starting_point, roads)
    road_backlink = CostBackLink(starting_point, roads)
    cost_path = CostPath(
        sawmill,
        road_cost,
        road_backlink,
        "BEST_SINGLE"
    )
    path_shp = output_path
    arcpy.conversion.RasterToPolyline(cost_path, path_shp, simplify="SIMPLIFY")
    arcpy.management.AddField(path_shp, "distance", "DOUBLE")
    arcpy.management.CalculateGeometryAttributes(
        path_shp, [["distance", "LENGTH_GEODESIC"]], "MILES_US"
    )
    distance = 0
    sc = arcpy.da.SearchCursor(path_shp, ["distance"])
    for row in sc:
        distance += row[0]
    del row, sc
    return distance
